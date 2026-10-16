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
    from database import seed_initial_data
    seed_initial_data(test_db)
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

# ==============================================================================
# 5. Phase 6 Comprehensive Quality & Security Gate Tests
# ==============================================================================
def test_data_persistence_across_app_restart(tmp_path):
    """
    Verifies that records inserted into SQLite persist across separate application
    instances and server restarts without data loss.
    """
    persistent_db = str(tmp_path / "persistent_test.db")

    class PersistConfig(TestConfig):
        DATABASE_PATH = persistent_db
        TESTING = True

    # First app session: Insert a student
    app1 = create_app(PersistConfig)
    client1 = app1.test_client()
    create_res = client1.post('/api/students', json={
        'roll_number': 'PERSIST-01',
        'name': 'Persistent Student',
        'attendance_percentage': 88.0,
        'marks': 85.0
    })
    assert create_res.status_code == 201

    # Second app session: Simulate complete server reboot using same database file
    app2 = create_app(PersistConfig)
    client2 = app2.test_client()
    get_res = client2.get('/api/students?search=PERSIST-01')
    assert get_res.status_code == 200
    data = get_res.get_json()
    assert len(data['students']) == 1
    assert data['students'][0]['roll_number'] == 'PERSIST-01'
    assert data['students'][0]['name'] == 'Persistent Student'

def test_validation_missing_required_fields(client):
    """
    Verifies rejection of payloads missing roll_number, name, attendance, or marks.
    """
    # Missing name
    res1 = client.post('/api/students', json={
        'roll_number': 'MISS-01',
        'attendance_percentage': 75.0,
        'marks': 70.0
    })
    assert res1.status_code == 400
    assert 'name' in res1.get_json()['errors']

    # Missing attendance
    res2 = client.post('/api/students', json={
        'roll_number': 'MISS-02',
        'name': 'No Attendance',
        'marks': 70.0
    })
    assert res2.status_code == 400
    assert 'attendance_percentage' in res2.get_json()['errors']

def test_validation_malformed_json_payload(client):
    """
    Verifies that non-JSON or malformed requests return HTTP 400 with a clear error.
    """
    res = client.post(
        '/api/students',
        data="This is plain text, not JSON",
        content_type='text/plain'
    )
    assert res.status_code == 400

def test_csv_unsupported_file_type(client):
    """
    Verifies that non-CSV files (.txt, .pdf, .json) are rejected with HTTP 400.
    """
    fake_txt = io.BytesIO(b"Hello world, not a csv")
    res = client.post(
        '/api/upload',
        data={'file': (fake_txt, 'document.txt')},
        content_type='multipart/form-data'
    )
    assert res.status_code == 400
    assert 'csv' in res.get_json()['error'].lower()

def test_csv_empty_file_upload(client):
    """
    Verifies that empty CSV files are rejected gracefully.
    """
    empty_file = io.BytesIO(b"")
    res = client.post(
        '/api/upload',
        data={'file': (empty_file, 'empty.csv')},
        content_type='multipart/form-data'
    )
    assert res.status_code == 400

def test_security_sql_injection_resistance(client):
    """
    Security check: Submits classic SQL injection vectors to search and form endpoints.
    Verifies that parameterized queries prevent syntax breakage or table dropping.
    """
    # 1. SQL injection in student search query parameter
    sql_inj_query = "CS2026'; DROP TABLE students; --"
    res_search = client.get(f'/api/students?search={sql_inj_query}')
    assert res_search.status_code == 200  # Handled safely, returning empty or matched list

    # 2. Table still exists and is intact
    res_table_check = client.get('/api/students')
    assert res_table_check.status_code == 200
    assert res_table_check.get_json()['total_count'] >= 30

    # 3. SQL injection in student creation payload
    res_create = client.post('/api/students', json={
        'roll_number': "INJ-01' OR '1'='1",
        'name': "Hacker'; DELETE FROM students; --",
        'attendance_percentage': 50.0,
        'marks': 50.0
    })
    # Either accepted as literal string or validated cleanly, but never executed as raw SQL
    assert res_create.status_code in (201, 400)

    # 4. Final verification: Table is still healthy
    res_health = client.get('/api/health')
    assert res_health.status_code == 200
    assert res_health.get_json()['database'] == 'connected'

def test_security_xss_sanitization(client):
    """
    Security check: Submits XSS script tags and verifies they are stored harmlessly as literal strings.
    """
    xss_payload = "<script>alert('XSS')</script>"
    res = client.post('/api/students', json={
        'roll_number': 'XSS-01',
        'name': xss_payload,
        'attendance_percentage': 80.0,
        'marks': 80.0
    })
    assert res.status_code == 201
    created_id = res.get_json()['student']['id']

    # Retrieve and verify literal representation
    get_res = client.get(f'/api/students/{created_id}')
    assert get_res.status_code == 200
    assert get_res.get_json()['student']['name'] == xss_payload

# ==============================================================================
# 6. Database Initialization, Startup Seeding & Persistence Verification
# ==============================================================================
def test_init_db_empty_database_does_not_insert_students(tmp_path):
    """
    Verifies that calling init_db() on an empty database initializes schema,
    indexes, and constraints, but inserts ZERO students.
    """
    empty_db = str(tmp_path / "empty_schema.db")
    init_db(empty_db)
    
    conn = get_db_connection(empty_db)
    try:
        # Check table exists
        cur = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='students'")
        assert cur.fetchone() is not None
        
        # Check record count is exactly 0
        count_cur = conn.execute("SELECT COUNT(*) FROM students")
        assert count_cur.fetchone()[0] == 0
    finally:
        conn.close()

def test_app_startup_empty_database_remains_empty(tmp_path):
    """
    Verifies that starting the Flask application with an empty database leaves
    the database empty (0 students) and does not insert any sample records.
    """
    fresh_db = str(tmp_path / "fresh_app.db")
    
    class FreshConfig(TestConfig):
        DATABASE_PATH = fresh_db
        TESTING = True

    app = create_app(FreshConfig)
    client = app.test_client()

    # GET /api/students should return empty list
    res = client.get('/api/students')
    assert res.status_code == 200
    data = res.get_json()
    assert data['total_count'] == 0
    assert data['students'] == []

    # GET /api/dashboard should report 0 total students
    dash_res = client.get('/api/dashboard')
    assert dash_res.status_code == 200
    assert dash_res.get_json()['total_students'] == 0

    # GET /api/analyze should report insufficient_data gracefully
    stats_res = client.get('/api/analyze')
    assert stats_res.status_code == 200
    assert stats_res.get_json()['status'] == 'insufficient_data'

def test_delete_all_students_and_restart_does_not_repopulate(tmp_path):
    """
    Verifies that deleting all students from the database and restarting the
    application does NOT re-insert or re-seed sample students.
    """
    restart_db = str(tmp_path / "restart_test.db")
    
    class RestartConfig(TestConfig):
        DATABASE_PATH = restart_db
        TESTING = True

    # 1. Start app and insert sample data
    app1 = create_app(RestartConfig)
    client1 = app1.test_client()
    from database import seed_initial_data
    seed_initial_data(restart_db)
    
    res1 = client1.get('/api/students')
    assert res1.get_json()['total_count'] == 30

    # 2. Delete all students
    conn = get_db_connection(restart_db)
    conn.execute("DELETE FROM students")
    conn.commit()
    count_after_del = conn.execute("SELECT COUNT(*) FROM students").fetchone()[0]
    conn.close()
    assert count_after_del == 0

    # 3. Simulate server restart with same database file
    app2 = create_app(RestartConfig)
    client2 = app2.test_client()
    
    # 4. Must remain completely empty
    res2 = client2.get('/api/students')
    assert res2.status_code == 200
    assert res2.get_json()['total_count'] == 0
    assert res2.get_json()['students'] == []

    conn2 = get_db_connection(restart_db)
    assert conn2.execute("SELECT COUNT(*) FROM students").fetchone()[0] == 0
    conn2.close()

def test_manual_student_creation_on_empty_database(tmp_path):
    """
    Verifies that adding students manually via the API works on a newly initialized empty database.
    """
    manual_db = str(tmp_path / "manual_test.db")
    
    class ManualConfig(TestConfig):
        DATABASE_PATH = manual_db
        TESTING = True

    app = create_app(ManualConfig)
    client = app.test_client()

    # Create first student
    post_res = client.post('/api/students', json={
        'roll_number': 'MANUAL-001',
        'name': 'Manual Student',
        'attendance_percentage': 87.5,
        'marks': 84.0
    })
    assert post_res.status_code == 201
    created = post_res.get_json()['student']
    assert created['roll_number'] == 'MANUAL-001'
    assert created['name'] == 'Manual Student'

    # Verify student is in list
    list_res = client.get('/api/students')
    assert list_res.get_json()['total_count'] == 1
    assert list_res.get_json()['students'][0]['roll_number'] == 'MANUAL-001'

def test_csv_import_on_empty_database(tmp_path):
    """
    Verifies that importing students through CSV works on an initially empty database.
    """
    csv_db = str(tmp_path / "csv_import_test.db")
    
    class CSVConfig(TestConfig):
        DATABASE_PATH = csv_db
        TESTING = True

    app = create_app(CSVConfig)
    client = app.test_client()

    csv_data = (
        "roll_number,name,attendance_percentage,marks\n"
        "CSV-001,Student Alpha,90.0,85.0\n"
        "CSV-002,Student Beta,70.0,65.0\n"
        "CSV-003,Student Gamma,50.0,45.0\n"
    )
    upload_res = client.post(
        '/api/upload',
        data={'file': (io.BytesIO(csv_data.encode('utf-8')), 'test.csv')},
        content_type='multipart/form-data'
    )
    assert upload_res.status_code == 200
    assert upload_res.get_json()['inserted_count'] == 3

    list_res = client.get('/api/students')
    assert list_res.get_json()['total_count'] == 3
    rolls = [s['roll_number'] for s in list_res.get_json()['students']]
    assert 'CSV-001' in rolls
    assert 'CSV-002' in rolls
    assert 'CSV-003' in rolls




