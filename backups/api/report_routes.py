"""
AttendX - Report & Upload API Routes
Endpoints for CSV dataset upload, validation, and CSV export streaming.
"""
from flask import Blueprint, request, jsonify, Response, current_app
from services import csv_service, report_service
from datetime import datetime

report_bp = Blueprint('report_bp', __name__)

@report_bp.route('/upload', methods=['POST'])
def upload_csv():
    """
    POST /api/upload
    Expects multipart/form-data with 'file' field containing CSV.
    """
    if 'file' not in request.files:
        return jsonify({
            'success': False,
            'error': "No file field uploaded. Please provide a multipart file upload with key 'file'."
        }), 400

    file = request.files['file']

    if not file or file.filename == '':
        return jsonify({
            'success': False,
            'error': 'No file was selected for upload.'
        }), 400

    if not file.filename.lower().endswith('.csv'):
        return jsonify({
            'success': False,
            'error': 'Invalid file format. Only standard comma-separated (.csv) files are supported.'
        }), 400

    db_path = current_app.config.get('DATABASE_PATH')
    result, status_code = csv_service.process_csv_upload(file.stream, db_path=db_path)
    return jsonify(result), status_code

@report_bp.route('/reports/csv', methods=['GET'])
def download_students_csv():
    """
    GET /api/reports/csv
    Streams all student records as a downloadable CSV attachment.
    """
    db_path = current_app.config.get('DATABASE_PATH')
    csv_stream = report_service.generate_students_csv_stream(db_path=db_path)

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"attendx_students_export_{timestamp}.csv"

    return Response(
        csv_stream.getvalue(),
        mimetype='text/csv',
        headers={
            'Content-Disposition': f'attachment; filename="{filename}"',
            'Content-Type': 'text/csv; charset=utf-8'
        }
    )

