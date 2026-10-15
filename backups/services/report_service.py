"""
AttendX - Report Generation Service
Generates downloadable CSV datasets and statistical report streams.
"""
import csv
import io
from database import get_db_connection

def generate_students_csv_stream(db_path=None):
    """
    Produces a CSV stream of all current student observations.
    """
    conn = get_db_connection(db_path)
    try:
        cursor = conn.execute("""
            SELECT id, roll_number, name, attendance_percentage, marks, created_at, updated_at
            FROM students
            ORDER BY roll_number ASC
        """)
        rows = cursor.fetchall()

        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(['id', 'roll_number', 'name', 'attendance_percentage', 'marks', 'created_at', 'updated_at'])

        for row in rows:
            writer.writerow([
                row['id'],
                row['roll_number'],
                row['name'],
                row['attendance_percentage'],
                row['marks'],
                row['created_at'],
                row['updated_at']
            ])

        output.seek(0)
        return output
    finally:
        conn.close()

