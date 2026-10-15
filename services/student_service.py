"""
AttendX - Student Service
Business logic and parameterized database operations for student records.
"""
import sqlite3
from database import get_db_connection

def validate_student_input(data, is_update=False):
    """
    Validates student payload against business and academic constraints.
    Returns (cleaned_data, error_dict).
    """
    errors = {}
    cleaned = {}

    # Roll Number
    if not is_update:
        roll = data.get('roll_number')
        if not roll or not str(roll).strip():
            errors['roll_number'] = 'Roll number is required and cannot be empty.'
        else:
            cleaned['roll_number'] = str(roll).strip().upper()

    # Name
    name = data.get('name')
    if not name or not str(name).strip():
        errors['name'] = 'Student name is required.'
    elif len(str(name).strip()) > 100:
        errors['name'] = 'Student name cannot exceed 100 characters.'
    else:
        cleaned['name'] = str(name).strip()

    # Attendance Percentage
    try:
        att = float(data.get('attendance_percentage', data.get('attendance', -1)))
        if att < 0.0 or att > 100.0:
            errors['attendance_percentage'] = 'Attendance percentage must be between 0.0 and 100.0.'
        else:
            cleaned['attendance_percentage'] = round(att, 2)
    except (ValueError, TypeError):
        errors['attendance_percentage'] = 'Attendance must be a valid numeric value.'

    # Examination Marks
    try:
        marks = float(data.get('marks', -1))
        if marks < 0.0 or marks > 100.0:
            errors['marks'] = 'Examination marks must be between 0.0 and 100.0.'
        else:
            cleaned['marks'] = round(marks, 2)
    except (ValueError, TypeError):
        errors['marks'] = 'Examination marks must be a valid numeric value.'

    return cleaned, errors

def get_attendance_group_label(att):
    if att >= 80.0:
        return 'high'
    elif att >= 60.0:
        return 'medium'
    return 'low'

def list_students(search=None, group=None, sort_by='roll_number', sort_dir='asc', page=1, page_size=None, db_path=None):
    """
    Fetches student records with optional search, group filtering, sorting, and pagination.
    """
    conn = get_db_connection(db_path)
    try:
        query = "SELECT id, roll_number, name, attendance_percentage, marks, created_at, updated_at FROM students WHERE 1=1"
        params = []

        # Search filter
        if search and search.strip():
            term = f"%{search.strip()}%"
            query += " AND (roll_number LIKE ? OR name LIKE ?)"
            params.extend([term, term])

        # Attendance Group filter
        if group:
            g = group.strip().lower()
            if g == 'high':
                query += " AND attendance_percentage >= 80.0"
            elif g == 'medium':
                query += " AND attendance_percentage >= 60.0 AND attendance_percentage < 80.0"
            elif g == 'low':
                query += " AND attendance_percentage < 60.0"

        # Sorting
        allowed_sorts = {
            'roll_number': 'roll_number',
            'name': 'name',
            'attendance_percentage': 'attendance_percentage',
            'marks': 'marks',
            'created_at': 'created_at'
        }
        col = allowed_sorts.get(sort_by, 'roll_number')
        direction = 'DESC' if str(sort_dir).lower() == 'desc' else 'ASC'
        query += f" ORDER BY {col} {direction}"

        # Total count query before pagination
        count_cursor = conn.execute(f"SELECT COUNT(*) as total FROM ({query})", params)
        total_count = count_cursor.fetchone()['total']

        # Pagination
        if page_size and int(page_size) > 0:
            limit = int(page_size)
            offset = (max(1, int(page)) - 1) * limit
            query += " LIMIT ? OFFSET ?"
            params.extend([limit, offset])

        cursor = conn.execute(query, params)
        rows = [dict(row) for row in cursor.fetchall()]

        # Attach computed attendance group key
        for r in rows:
            r['group'] = get_attendance_group_label(r['attendance_percentage'])

        return {
            'students': rows,
            'total_count': total_count,
            'page': int(page) if page_size else 1,
            'page_size': int(page_size) if page_size else total_count
        }
    finally:
        conn.close()

def get_student_by_id(student_id, db_path=None):
    """
    Fetches a single student by database ID.
    """
    conn = get_db_connection(db_path)
    try:
        cursor = conn.execute(
            "SELECT id, roll_number, name, attendance_percentage, marks, created_at, updated_at FROM students WHERE id = ?",
            (student_id,)
        )
        row = cursor.fetchone()
        if not row:
            return None
        res = dict(row)
        res['group'] = get_attendance_group_label(res['attendance_percentage'])
        return res
    finally:
        conn.close()

def create_student(data, db_path=None):
    """
    Inserts a new student record after validation and uniqueness check.
    """
    cleaned, errors = validate_student_input(data, is_update=False)
    if errors:
        return None, errors, 400

    conn = get_db_connection(db_path)
    try:
        with conn:
            cursor = conn.execute(
                """
                INSERT INTO students (roll_number, name, attendance_percentage, marks)
                VALUES (?, ?, ?, ?)
                """,
                (cleaned['roll_number'], cleaned['name'], cleaned['attendance_percentage'], cleaned['marks'])
            )
            student_id = cursor.lastrowid
            
        return get_student_by_id(student_id, db_path), None, 201
    except sqlite3.IntegrityError as e:
        if 'UNIQUE constraint failed' in str(e) or 'roll_number' in str(e):
            return None, {'roll_number': f"Roll number '{cleaned['roll_number']}' already exists."}, 409
        return None, {'database': 'Database constraint violation.'}, 400
    finally:
        conn.close()

def update_student(student_id, data, db_path=None):
    """
    Updates an existing student's name, attendance, or marks.
    """
    cleaned, errors = validate_student_input(data, is_update=True)
    if errors:
        return None, errors, 400

    conn = get_db_connection(db_path)
    try:
        # Check existence
        existing = get_student_by_id(student_id, db_path)
        if not existing:
            return None, {'error': f'Student with ID {student_id} not found.'}, 404

        with conn:
            conn.execute(
                """
                UPDATE students 
                SET name = ?, attendance_percentage = ?, marks = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (cleaned['name'], cleaned['attendance_percentage'], cleaned['marks'], student_id)
            )

        return get_student_by_id(student_id, db_path), None, 200
    finally:
        conn.close()

def delete_student(student_id, db_path=None):
    """
    Deletes a student record by ID.
    """
    conn = get_db_connection(db_path)
    try:
        existing = get_student_by_id(student_id, db_path)
        if not existing:
            return False, f'Student with ID {student_id} not found.'

        with conn:
            conn.execute("DELETE FROM students WHERE id = ?", (student_id,))
        return True, None
    finally:
        conn.close()

