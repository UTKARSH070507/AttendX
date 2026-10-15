"""
AttendX - CSV Processing Service
Line-by-line validation, schema inspection, deduplication, and bulk insertion.
"""
import csv
import io
import sqlite3
from database import get_db_connection

REQUIRED_COLUMNS = ['roll_number', 'name', 'attendance_percentage', 'marks']

def process_csv_upload(file_stream, db_path=None):
    """
    Parses, validates, and imports a CSV dataset into SQLite.
    Returns: (summary_dict, status_code)
    """
    try:
        # Decode stream
        content = file_stream.read()
        if isinstance(content, bytes):
            text = content.decode('utf-8-sig')  # Handles UTF-8 with or without BOM
        else:
            text = content
    except UnicodeDecodeError:
        return {
            'success': False,
            'error': 'File encoding must be valid UTF-8.'
        }, 400

    if not text.strip():
        return {
            'success': False,
            'error': 'Uploaded CSV file is empty.'
        }, 400

    reader = csv.reader(io.StringIO(text))
    try:
        header_row = next(reader)
    except StopIteration:
        return {
            'success': False,
            'error': 'CSV contains no rows.'
        }, 400

    # Normalize header names
    cleaned_headers = [h.strip().lower() for h in header_row if h.strip()]
    missing_cols = [col for col in REQUIRED_COLUMNS if col not in cleaned_headers]
    if missing_cols:
        return {
            'success': False,
            'error': f"CSV is missing required column(s): {', '.join(missing_cols)}.",
            'required_columns': REQUIRED_COLUMNS,
            'received_columns': cleaned_headers
        }, 400

    # Map column indices
    col_map = {col: cleaned_headers.index(col) for col in REQUIRED_COLUMNS}

    # Fetch existing roll numbers for deduplication
    conn = get_db_connection(db_path)
    try:
        cursor = conn.execute("SELECT LOWER(roll_number) as roll FROM students")
        existing_rolls = {row['roll'] for row in cursor.fetchall()}
    finally:
        conn.close()

    valid_records = []
    rejected_rows = []
    seen_in_batch = set()
    row_number = 1  # 1-indexed (row 1 is header)

    for parts in reader:
        row_number += 1
        # Skip completely blank lines
        if not parts or not any(p.strip() for p in parts):
            continue

        if len(parts) < len(cleaned_headers):
            rejected_rows.append({
                'row': row_number,
                'roll_number': 'N/A',
                'reason': f'Insufficient columns (expected {len(cleaned_headers)}, found {len(parts)}).'
            })
            continue

        raw_roll = parts[col_map['roll_number']].strip()
        raw_name = parts[col_map['name']].strip()
        raw_att = parts[col_map['attendance_percentage']].strip()
        raw_marks = parts[col_map['marks']].strip()

        # Roll Number check
        if not raw_roll:
            rejected_rows.append({
                'row': row_number,
                'roll_number': 'N/A',
                'reason': 'Missing roll number.'
            })
            continue

        roll_upper = raw_roll.upper()
        roll_lower = raw_roll.lower()

        # Duplicate check against existing database
        if roll_lower in existing_rolls:
            rejected_rows.append({
                'row': row_number,
                'roll_number': roll_upper,
                'reason': 'Roll number already exists in database.'
            })
            continue

        # Duplicate check within this CSV file
        if roll_lower in seen_in_batch:
            rejected_rows.append({
                'row': row_number,
                'roll_number': roll_upper,
                'reason': 'Duplicate roll number repeated within this file.'
            })
            continue

        # Name check
        if not raw_name:
            rejected_rows.append({
                'row': row_number,
                'roll_number': roll_upper,
                'reason': 'Student name is missing or empty.'
            })
            continue

        # Attendance check
        try:
            att = float(raw_att)
            if att < 0.0 or att > 100.0:
                rejected_rows.append({
                    'row': row_number,
                    'roll_number': roll_upper,
                    'reason': f'Attendance percentage out of range [0-100]: {raw_att}'
                })
                continue
        except ValueError:
            rejected_rows.append({
                'row': row_number,
                'roll_number': roll_upper,
                'reason': f'Invalid attendance value (non-numeric): {raw_att}'
            })
            continue

        # Marks check
        try:
            marks = float(raw_marks)
            if marks < 0.0 or marks > 100.0:
                rejected_rows.append({
                    'row': row_number,
                    'roll_number': roll_upper,
                    'reason': f'Marks out of range [0-100]: {raw_marks}'
                })
                continue
        except ValueError:
            rejected_rows.append({
                'row': row_number,
                'roll_number': roll_upper,
                'reason': f'Invalid marks value (non-numeric): {raw_marks}'
            })
            continue

        # Passed all validation checks
        seen_in_batch.add(roll_lower)
        valid_records.append((roll_upper, raw_name, round(att, 2), round(marks, 2)))

    # Insert valid rows into SQLite
    inserted_count = 0
    if valid_records:
        conn = get_db_connection(db_path)
        try:
            with conn:
                conn.executemany("""
                    INSERT INTO students (roll_number, name, attendance_percentage, marks)
                    VALUES (?, ?, ?, ?)
                """, valid_records)
                inserted_count = len(valid_records)
        finally:
            conn.close()

    total_data_rows = len(valid_records) + len(rejected_rows)

    return {
        'success': True,
        'message': f"Import complete: {inserted_count} records inserted, {len(rejected_rows)} rows rejected.",
        'total_rows': total_data_rows,
        'inserted_count': inserted_count,
        'rejected_count': len(rejected_rows),
        'rejected_rows': rejected_rows
    }, 200

