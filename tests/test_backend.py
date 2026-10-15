"""
AttendX - Backend Automated Test Suite
Validates database integrity, API routes, student CRUD, CSV parsing, and statistical calculations.
"""
import io
import pytest
from app import create_app
from config import TestConfig
from database import init_db, get_db_connection

@pytest.fixture
def app(tmp_path):
    # Use a fresh SQLite file in pytest temporary directory for clean isolation
    test_db = str(tmp_path / "test_attendx.db")
    
    class RuntimeTestConfig(TestConfig):
        DATABASE_PATH = test_db
        TESTING = True

    app_instance = create_app(RuntimeTestConfig)
    return app_instance

@pytest.fixture
def client(app):
    return app.test_client()

# ==============================================================================
# 1. Health & System Connectivity Tests
# ==============================================================================
def test_health_check(client):
    response = client.get('/api/health')
    assert response.status_code == 200
    data = response.get_json()
    assert data['status'] == 'healthy'
    assert data['database'] == 'connected'

def test_root_index_view(client):
    response = client.get('/')
    assert response.status_code == 200
    assert b'AttendX' in response.data

# ==============================================================================
# 2. Student CRUD & Validation Tests
# ==============================================================================
def test_list_students(client):
    response = client.get('/api/students')
    assert response.status_code == 200
    data = response.get_json()
    assert 'students' in data
    assert 'total_count' in data
    assert data['total_count'] >= 30  # Seed data present

def test_list_students_filtering_and_search(client):
    # Search for known seed student
    response = client.get('/api/students?search=Aarav')
    data = response.get_json()
    assert len(data['students']) >= 1
    assert data['students'][0]['roll_number'] == 'CS2026-001'

    # Filter by group
    response_high = client.get('/api/students?group=high')
    data_high = response_high.get_json()
    for s in data_high['students']:
        assert s['attendance_percentage'] >= 80.0

def test_get_student_by_id(client):
    response = client.get('/api/students/1')
    assert response.status_code == 200
    data = response.get_json()
    assert data['student']['id'] == 1
    assert data['student']['roll_number'] == 'CS2026-001'

def test_get_student_not_found(client):
    response = client.get('/api/students/99999')
    assert response.status_code == 404

def test_create_student_success(client):
    new_student = {
        'roll_number': 'TEST-999',
        'name': 'Test Student',
        'attendance_percentage': 88.5,
        'marks': 82.0
    }
    response = client.post('/api/students', json=new_student)
    assert response.status_code == 201
    data = response.get_json()
    assert data['student']['roll_number'] == 'TEST-999'
    assert data['student']['name'] == 'Test Student'

def test_create_student_duplicate_roll_number(client):
    # Try inserting roll number CS2026-001 which already exists
    dup = {
        'roll_number': 'CS2026-001',
        'name': 'Duplicate Person',
        'attendance_percentage': 75.0,
        'marks': 70.0
    }
    response = client.post('/api/students', json=dup)
    assert response.status_code == 409
    data = response.get_json()
    assert 'roll_number' in data['errors']

def test_create_student_validation_errors(client):
    # Invalid attendance > 100 and marks < 0
    invalid_data = {
        'roll_number': 'INVALID-1',
        'name': 'Invalid Data',
        'attendance_percentage': 110.0,
        'marks': -5.0
    }
    response = client.post('/api/students', json=invalid_data)
    assert response.status_code == 400
    data = response.get_json()
    assert 'attendance_percentage' in data['errors']
    assert 'marks' in data['errors']

def test_update_student(client):
    update_data = {
        'name': 'Aarav Sharma Updated',
        'attendance_percentage': 95.0,
        'marks': 92.5
    }
    response = client.put('/api/students/1', json=update_data)
    assert response.status_code == 200
    data = response.get_json()
    assert data['student']['name'] == 'Aarav Sharma Updated'
    assert data['student']['attendance_percentage'] == 95.0

def test_delete_student(client):
    # Create temporary student to delete
    create_res = client.post('/api/students', json={
        'roll_number': 'DEL-101',
        'name': 'To Be Deleted',
        'attendance_percentage': 50.0,
        'marks': 45.0
    })
    new_id = create_res.get_json()['student']['id']

    # Delete student
    del_res = client.delete(f'/api/students/{new_id}')
    assert del_res.status_code == 200

    # Verify deleted
    get_res = client.get(f'/api/students/{new_id}')
    assert get_res.status_code == 404

# ==============================================================================
# 3. CSV Dataset Upload & Validation Tests
# ==============================================================================
def test_csv_upload_valid(client):
    csv_content = (
        "roll_number,name,attendance_percentage,marks\n"
        "UPLOAD-01,Student One,82.5,79.0\n"
        "UPLOAD-02,Student Two,65.0,61.0\n"
    )
    data = {'file': (io.BytesIO(csv_content.encode('utf-8')), 'test.csv')}
    response = client.post('/api/upload', data=data, content_type='multipart/form-data')
    assert response.status_code == 200
    result = response.get_json()
    assert result['success'] is True
    assert result['inserted_count'] == 2
    assert result['rejected_count'] == 0

def test_csv_upload_missing_columns(client):
    csv_content = (
        "roll_number,name,marks\n"
        "UPLOAD-03,Student Three,80.0\n"
    )
    data = {'file': (io.BytesIO(csv_content.encode('utf-8')), 'test.csv')}
    response = client.post('/api/upload', data=data, content_type='multipart/form-data')
    assert response.status_code == 400
    result = response.get_json()
    assert result['success'] is False
    assert 'attendance_percentage' in result['error']

def test_csv_upload_row_rejection_reporting(client):
    csv_content = (
        "roll_number,name,attendance_percentage,marks\n"
        "GOOD-01,Valid Student,85.0,80.0\n"
        "BAD-01,Out of Bounds,125.0,75.0\n"  # Invalid attendance
        "BAD-02,Invalid Marks,75.0,abc\n"    # Non-numeric marks
        ",Missing Roll,80.0,80.0\n"          # Missing roll
        "GOOD-01,Duplicate In File,88.0,85.0\n" # Duplicate in file
    )
    data = {'file': (io.BytesIO(csv_content.encode('utf-8')), 'test.csv')}
    response = client.post('/api/upload', data=data, content_type='multipart/form-data')
    assert response.status_code == 200
    result = response.get_json()
    assert result['inserted_count'] == 1
    assert result['rejected_count'] == 4
    assert len(result['rejected_rows']) == 4

# ==============================================================================
# 4. Analytics & Reports Endpoints Tests
# ==============================================================================
def test_dashboard_metrics_endpoint(client):
    response = client.get('/api/dashboard')
    assert response.status_code == 200
    data = response.get_json()
    assert data['total_students'] >= 30
    assert data['avg_attendance'] > 0
    assert data['avg_marks'] > 0
    assert len(data['scatter_points']) == data['total_students']

def test_statistical_analysis_endpoint(client):
    response = client.get('/api/analyze')
    assert response.status_code == 200
    data = response.get_json()
    assert data['status'] == 'success'
    assert 'pearson' in data
    assert 'spearman' in data
    assert 'groups' in data
    assert 'anova' in data
    assert -1.0 <= data['pearson']['r'] <= 1.0
    assert -1.0 <= data['spearman']['rho'] <= 1.0

def test_export_csv_report_endpoint(client):
    response = client.get('/api/reports/csv')
    assert response.status_code == 200
    assert response.mimetype == 'text/csv'
    assert b'roll_number,name,attendance_percentage,marks' in response.data

def test_cors_headers_and_preflight(client):
    """
    Verifies that requests from port 5500 receive appropriate CORS headers
    and OPTIONS preflight returns HTTP 204.
    """
    # 1. Preflight OPTIONS on API route
    opt_res = client.options('/api/analyze', headers={'Origin': 'http://127.0.0.1:5500'})
    assert opt_res.status_code == 204
    assert opt_res.headers.get('Access-Control-Allow-Origin') == 'http://127.0.0.1:5500'
    assert 'GET' in opt_res.headers.get('Access-Control-Allow-Methods')

    # 2. GET on API route with Origin
    get_res = client.get('/api/analyze', headers={'Origin': 'http://127.0.0.1:5500'})
    assert get_res.status_code == 200
    assert get_res.headers.get('Access-Control-Allow-Origin') == 'http://127.0.0.1:5500'

    # 3. GET on students route with Origin
    students_res = client.get('/api/students', headers={'Origin': 'http://127.0.0.1:5500'})
    assert students_res.status_code == 200
    assert students_res.headers.get('Access-Control-Allow-Origin') == 'http://127.0.0.1:5500'


