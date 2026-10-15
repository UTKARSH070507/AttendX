"""
AttendX API Blueprints Package
"""
from api.student_routes import student_bp
from api.analytics_routes import analytics_bp
from api.report_routes import report_bp

__all__ = ['student_bp', 'analytics_bp', 'report_bp']

