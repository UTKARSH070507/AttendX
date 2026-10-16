"""
AttendX - Database Module
SQLite connection manager, schema initialization, and database utilities.
"""
import sqlite3
import os
from pathlib import Path
from config import Config

def get_db_connection(db_path=None):
    """
    Creates and returns a SQLite connection with Row factory enabled.
    """
    if db_path is None:
        db_path = Config.DATABASE_PATH
    
    # Ensure directory exists if writing to disk
    if db_path != ':memory:':
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

def init_db(db_path=None):
    """
    Initializes database tables, constraints, and indexes.
    Does NOT seed sample data; empty databases remain empty on startup.
    """
    conn = get_db_connection(db_path)
    try:
        with conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS students (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    roll_number TEXT NOT NULL UNIQUE COLLATE NOCASE,
                    name TEXT NOT NULL,
                    attendance_percentage REAL NOT NULL CHECK(attendance_percentage >= 0.0 AND attendance_percentage <= 100.0),
                    marks REAL NOT NULL CHECK(marks >= 0.0 AND marks <= 100.0),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)

            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_students_roll_number 
                ON students(roll_number);
            """)

            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_students_attendance 
                ON students(attendance_percentage);
            """)
    finally:
        conn.close()

def seed_initial_data(db_path=None):
    """
    Explicitly seeds baseline sample records for testing or demonstration.
    Must be called explicitly; not invoked during init_db() or app startup.
    """
    conn = get_db_connection(db_path)
    try:
        with conn:
            _seed_initial_data(conn)
    finally:
        conn.close()

def _seed_initial_data(conn):
    """
    Seeds realistic baseline records for academic project demonstration.
    """
    sample_records = [
        ("CS2026-001", "Aarav Sharma", 92.5, 88.0),
        ("CS2026-002", "Ananya Iyer", 84.0, 81.5),
        ("CS2026-003", "Rohan Verma", 67.5, 62.0),
        ("CS2026-004", "Priya Nair", 95.0, 91.0),
        ("CS2026-005", "Kabir Mehta", 54.0, 49.0),
        ("CS2026-006", "Diya Patel", 78.5, 74.0),
        ("CS2026-007", "Siddharth Rao", 88.0, 83.5),
        ("CS2026-008", "Sneha Kulkarni", 48.0, 42.0),
        ("CS2026-009", "Aditya Joshi", 72.0, 68.0),
        ("CS2026-010", "Ishaan Gupta", 61.5, 59.0),
        ("CS2026-011", "Rhea Deshmukh", 96.0, 94.0),
        ("CS2026-012", "Varun Pillai", 74.0, 71.0),
        ("CS2026-013", "Meera Sen", 86.5, 79.0),
        ("CS2026-014", "Aryan Reddy", 51.0, 45.0),
        ("CS2026-015", "Tanvi Bhatt", 81.0, 77.5),
        ("CS2026-016", "Kunal Ghosh", 69.0, 64.0),
        ("CS2026-017", "Pooja Hegde", 90.0, 86.0),
        ("CS2026-018", "Nikhil Menon", 58.5, 53.0),
        ("CS2026-019", "Shreya Saxena", 83.5, 80.0),
        ("CS2026-020", "Gaurav Malhotra", 42.0, 38.0),
        ("CS2026-021", "Avani Trivedi", 97.0, 93.0),
        ("CS2026-022", "Rahul Choudhury", 76.0, 70.0),
        ("CS2026-023", "Simran Kaur", 89.0, 85.0),
        ("CS2026-024", "Devansh Nambiar", 63.0, 60.0),
        ("CS2026-025", "Bhavna Mishra", 55.0, 50.0),
        ("CS2026-026", "Harsh Vardhan", 82.0, 76.0),
        ("CS2026-027", "Kritika Roy", 91.0, 89.0),
        ("CS2026-028", "Alok Pandey", 45.0, 40.0),
        ("CS2026-029", "Neha Agarwal", 77.0, 72.0),
        ("CS2026-030", "Vikram Singhania", 85.0, 82.0)
    ]
    conn.executemany("""
        INSERT INTO students (roll_number, name, attendance_percentage, marks)
        VALUES (?, ?, ?, ?)
    """, sample_records)

