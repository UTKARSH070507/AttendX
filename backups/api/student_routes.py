"""
AttendX - Student API Routes
CRUD endpoints for student record management.
"""
from flask import Blueprint, request, jsonify, current_app
from services import student_service

student_bp = Blueprint('student_bp', __name__)

@student_bp.route('/students', methods=['GET'])
def list_students():
    """
    GET /api/students
    Query parameters: search, group, sort_by, sort_dir, page, page_size
    """
    search = request.args.get('search')
    group = request.args.get('group')
    sort_by = request.args.get('sort_by', 'roll_number')
    sort_dir = request.args.get('sort_dir', 'asc')
    page = request.args.get('page', 1)
    page_size = request.args.get('page_size', None)

    db_path = current_app.config.get('DATABASE_PATH')
    result = student_service.list_students(
        search=search,
        group=group,
        sort_by=sort_by,
        sort_dir=sort_dir,
        page=page,
        page_size=page_size,
        db_path=db_path
    )
    return jsonify(result), 200

@student_bp.route('/students/<int:student_id>', methods=['GET'])
def get_student(student_id):
    """
    GET /api/students/<id>
    """
    db_path = current_app.config.get('DATABASE_PATH')
    student = student_service.get_student_by_id(student_id, db_path=db_path)
    if not student:
        return jsonify({'error': f'Student with ID {student_id} not found.'}), 404
    return jsonify({'student': student}), 200

@student_bp.route('/students', methods=['POST'])
def add_student():
    """
    POST /api/students
    Body: {"roll_number": "...", "name": "...", "attendance_percentage": 85.0, "marks": 78.0}
    """
    if not request.is_json:
        return jsonify({'error': 'Request body must be JSON.'}), 400

    data = request.get_json()
    db_path = current_app.config.get('DATABASE_PATH')
    student, errors, status_code = student_service.create_student(data, db_path=db_path)

    if errors:
        return jsonify({'errors': errors}), status_code

    return jsonify({
        'message': 'Student created successfully.',
        'student': student
    }), 201

@student_bp.route('/students/<int:student_id>', methods=['PUT'])
def update_student(student_id):
    """
    PUT /api/students/<id>
    Body: {"name": "...", "attendance_percentage": ..., "marks": ...}
    """
    if not request.is_json:
        return jsonify({'error': 'Request body must be JSON.'}), 400

    data = request.get_json()
    db_path = current_app.config.get('DATABASE_PATH')
    student, errors, status_code = student_service.update_student(student_id, data, db_path=db_path)

    if errors:
        return jsonify({'errors': errors}), status_code

    return jsonify({
        'message': 'Student updated successfully.',
        'student': student
    }), 200

@student_bp.route('/students/<int:student_id>', methods=['DELETE'])
def delete_student(student_id):
    """
    DELETE /api/students/<id>
    """
    db_path = current_app.config.get('DATABASE_PATH')
    success, err_msg = student_service.delete_student(student_id, db_path=db_path)
    if not success:
        return jsonify({'error': err_msg}), 404

    return jsonify({'message': f'Student record {student_id} successfully deleted.'}), 200

