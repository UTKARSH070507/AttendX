"""
AttendX - Analytics API Routes
Endpoints serving dashboard summary metrics and detailed statistical analysis.
"""
from flask import Blueprint, jsonify, current_app
from services import stats_service

analytics_bp = Blueprint('analytics_bp', __name__)

@analytics_bp.route('/dashboard', methods=['GET'])
def get_dashboard_data():
    """
    GET /api/dashboard
    Returns sample count, averages, group counts, and scatter plot coordinates.
    """
    db_path = current_app.config.get('DATABASE_PATH')
    data = stats_service.calculate_dashboard_metrics(db_path=db_path)
    return jsonify(data), 200

@analytics_bp.route('/analyze', methods=['GET', 'POST'])
def get_statistical_analysis():
    """
    GET /api/analyze
    Computes Pearson, Spearman, descriptive statistics, and ANOVA from SQLite records.
    """
    db_path = current_app.config.get('DATABASE_PATH')
    results = stats_service.perform_statistical_analysis(db_path=db_path)
    return jsonify(results), 200

