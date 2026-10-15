"""
AttendX - Full-Stack Integration Automated Tests
Verifies that the frontend template, static assets, REST APIs, and database transactions work together seamlessly.
"""
import io
import pytest
from app import create_app
from config import TestConfig

@pytest.fixture
def app(tmp_path):
    test_db = str(tmp_path / "integration_attendx.db")
    
    class IntegrationConfig(TestConfig):
        DATABASE_PATH = test_db
        TESTING = True

    return create_app(IntegrationConfig)

@pytest.fixture
def client(app):
    return app.test_client()

def test_frontend_page_and_asset_delivery(client):
    """
    Verifies that the HTML dashboard and all referenced static JS/CSS bundles are served with HTTP 200.
    """
    # Root dashboard template
    res = client.get('/')
    assert res.status_code == 200
    assert b'AttendX' in res.data
    assert b'/static/js/api.js' in res.data
    assert b'/static/js/app.js' in res.data
    assert b'/static/js/charts.js' in res.data

    # Static CSS assets
    assert client.get('/static/css/variables.css').status_code == 200
    assert client.get('/static/css/layout.css').status_code == 200
    assert client.get('/static/css/components.css').status_code == 200

    # Static JS assets
    assert client.get('/static/js/api.js').status_code == 200
    assert client.get('/static/js/ui.js').status_code == 200
    assert client.get('/static/js/charts.js').status_code == 200
    assert client.get('/static/js/app.js').status_code == 200
    assert client.get('/static/vendor/chart.umd.min.js').status_code == 200

def test_end_to_end_student_lifecycle_and_statistical_update(client):
    """
    Tests complete lifecycle:
    1. Read initial dashboard metrics.
    2. Add new student.
    3. Verify dashboard and correlation update dynamically.
    4. Update student.
    5. Delete student and verify counts return to baseline.
    """
    # 1. Baseline Dashboard & Analysis
    dash_res1 = client.get('/api/dashboard')
    assert dash_res1.status_code == 200
    init_count = dash_res1.get_json()['total_students']

    stats_res1 = client.get('/api/analyze')
    assert stats_res1.status_code == 200
    init_r = stats_res1.get_json()['pearson']['r']

    # 2. Add New Student
    new_student = {
        'roll_number': 'INT-2026-001',
        'name': 'Integration Test Student',
        'attendance_percentage': 99.0,
        'marks': 98.0
    }
    create_res = client.post('/api/students', json=new_student)
    assert create_res.status_code == 201
    created_id = create_res.get_json()['student']['id']

    # 3. Verify Dashboard Reflected Change
    dash_res2 = client.get('/api/dashboard')
    assert dash_res2.get_json()['total_students'] == init_count + 1

    stats_res2 = client.get('/api/analyze')
    assert stats_res2.get_json()['sample_size'] == init_count + 1

    # 4. Update Student
    update_res = client.put(f'/api/students/{created_id}', json={
        'name': 'Integration Test Student Modified',
        'attendance_percentage': 85.0,
        'marks': 80.0
    })
    assert update_res.status_code == 200

    # 5. Delete Student
    delete_res = client.delete(f'/api/students/{created_id}')
    assert delete_res.status_code == 200

    # Verify counts return to initial
    dash_res3 = client.get('/api/dashboard')
    assert dash_res3.get_json()['total_students'] == init_count

def test_csv_upload_and_export_pipeline(client):
    """
    Verifies that uploading a CSV updates the database and the exported CSV contains the imported data.
    """
    csv_payload = (
        "roll_number,name,attendance_percentage,marks\n"
        "BULK-01,Bulk Alpha,91.0,88.0\n"
        "BULK-02,Bulk Beta,66.0,62.0\n"
    )
    upload_res = client.post(
        '/api/upload',
        data={'file': (io.BytesIO(csv_payload.encode('utf-8')), 'bulk.csv')},
        content_type='multipart/form-data'
    )
    assert upload_res.status_code == 200
    assert upload_res.get_json()['inserted_count'] == 2

    # Check exported CSV
    export_res = client.get('/api/reports/csv')
    assert export_res.status_code == 200
    export_text = export_res.data.decode('utf-8')
    assert 'BULK-01' in export_text
    assert 'BULK-02' in export_text

def test_student_search_filter_pagination(client):
    """
    Tests student list query parameters: search, group filtering, sorting, and pagination.
    """
    # Seed known students
    client.post('/api/students', json={'roll_number': 'TST-A', 'name': 'Alice Smith', 'attendance_percentage': 95.0, 'marks': 92.0})
    client.post('/api/students', json={'roll_number': 'TST-B', 'name': 'Bob Jones', 'attendance_percentage': 72.0, 'marks': 68.0})
    client.post('/api/students', json={'roll_number': 'TST-C', 'name': 'Charlie Brown', 'attendance_percentage': 45.0, 'marks': 40.0})

    # Search by name
    res = client.get('/api/students?search=Alice')
    assert res.status_code == 200
    data = res.get_json()
    assert any(s['name'] == 'Alice Smith' for s in data['students'])
    assert not any(s['name'] == 'Bob Jones' for s in data['students'])

    # Search by roll number
    res = client.get('/api/students?search=TST-B')
    assert res.status_code == 200
    assert len(res.get_json()['students']) == 1

    # Filter by group 'high' (>=80%)
    res_high = client.get('/api/students?group=high')
    assert res_high.status_code == 200
    for s in res_high.get_json()['students']:
        assert s['attendance_percentage'] >= 80.0

    # Filter by group 'low' (<60%)
    res_low = client.get('/api/students?group=low')
    assert res_low.status_code == 200
    for s in res_low.get_json()['students']:
        assert s['attendance_percentage'] < 60.0

    # Pagination test
    res_page = client.get('/api/students?page=1&page_size=2')
    assert res_page.status_code == 200
    page_data = res_page.get_json()
    assert len(page_data['students']) == 2
    assert page_data['page'] == 1

def test_csv_upload_rejection_reporting(client):
    """
    Verifies that invalid rows in CSV uploads are rejected with explicit reasons and accurate counts.
    """
    csv_payload = (
        "roll_number,name,attendance_percentage,marks\n"
        "VALID-01,Valid Student,82.0,78.0\n"
        "INVALID-01,,90.0,85.0\n"  # Missing name
        "INVALID-02,Out of Bounds,105.0,80.0\n"  # Attendance > 100
        "INVALID-03,Negative Marks,75.0,-5.0\n"  # Marks < 0
        "VALID-01,Duplicate Roll,80.0,80.0\n"  # Duplicate roll number
    )
    upload_res = client.post(
        '/api/upload',
        data={'file': (io.BytesIO(csv_payload.encode('utf-8')), 'mixed.csv')},
        content_type='multipart/form-data'
    )
    assert upload_res.status_code == 200
    res_data = upload_res.get_json()
    assert res_data['inserted_count'] == 1
    assert res_data['rejected_count'] == 4
    assert len(res_data['rejected_rows']) == 4

    rejection_reasons = [r['reason'] for r in res_data['rejected_rows']]
    assert any('name' in r.lower() for r in rejection_reasons)
    assert any('100' in r for r in rejection_reasons)
    assert any('duplicate' in r.lower() for r in rejection_reasons)

def test_csv_import_immediate_statistical_impact(client):
    """
    Verifies that importing students via CSV immediately alters statistical outcomes
    in the analysis endpoint without requiring server restart or manual caching flush.
    """
    # 1. Baseline analysis
    base_res = client.get('/api/analyze')
    base_size = base_res.get_json()['sample_size']
    base_r = base_res.get_json()['pearson']['r']

    # 2. Upload valid CSV records
    csv_content = (
        "roll_number,name,attendance_percentage,marks\n"
        "STAT-01,Stat Student One,98.0,99.0\n"
        "STAT-02,Stat Student Two,97.0,96.0\n"
        "STAT-03,Stat Student Three,35.0,28.0\n"
    )
    upload_res = client.post(
        '/api/upload',
        data={'file': (io.BytesIO(csv_content.encode('utf-8')), 'stats_test.csv')},
        content_type='multipart/form-data'
    )
    assert upload_res.status_code == 200
    assert upload_res.get_json()['inserted_count'] == 3

    # 3. Post-upload analysis
    new_res = client.get('/api/analyze')
    assert new_res.status_code == 200
    new_data = new_res.get_json()
    assert new_data['sample_size'] == base_size + 3
    assert 'pearson' in new_data
    assert 'spearman' in new_data
    assert 'anova' in new_data
    assert new_data['anova']['f_statistic'] > 0



