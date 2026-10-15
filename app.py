"""
AttendX - Student Attendance vs Academic Performance Analysis System
Flask Application Factory and Server Entry Point
"""
from datetime import datetime, timezone
from flask import Flask, render_template, jsonify, request
from config import Config
from database import init_db, get_db_connection
from api.student_routes import student_bp
from api.analytics_routes import analytics_bp
from api.report_routes import report_bp

def create_app(config_class=Config):
    """
    Creates and configures the Flask application instance.
    """
    app = Flask(
        __name__,
        static_folder='static',
        template_folder='templates'
    )
    app.config.from_object(config_class)

    # Automatically initialize SQLite database schema and seeds
    init_db(app.config.get('DATABASE_PATH'))

    # Register API Blueprints under /api prefix
    app.register_blueprint(student_bp, url_prefix='/api')
    app.register_blueprint(analytics_bp, url_prefix='/api')
    app.register_blueprint(report_bp, url_prefix='/api')

    # --------------------------------------------------------------------------
    # Health Check & Root Frontend View
    # --------------------------------------------------------------------------
    @app.route('/api/health', methods=['GET'])
    def health_check():
        """
        GET /api/health
        System operational and database connectivity check.
        """
        db_status = 'disconnected'
        try:
            conn = get_db_connection(app.config.get('DATABASE_PATH'))
            conn.execute("SELECT 1")
            conn.close()
            db_status = 'connected'
        except Exception as e:
            db_status = f'error: {str(e)}'

        return jsonify({
            'status': 'healthy',
            'database': db_status,
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'version': '1.0.0'
        }), 200

    @app.route('/', methods=['GET'])
    def index():
        """
        Serves the AttendX single-page dashboard.
        """
        return render_template('index.html')

    # --------------------------------------------------------------------------
    # Security Headers Middleware
    # --------------------------------------------------------------------------
    @app.after_request
    def set_security_headers(response):
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        return response

    # --------------------------------------------------------------------------
    # Centralized JSON Error Handling for API routes
    # --------------------------------------------------------------------------
    @app.errorhandler(400)
    def bad_request(error):
        if request.path.startswith('/api'):
            return jsonify({'error': 'Bad Request', 'message': getattr(error, 'description', str(error))}), 400
        return error

    @app.errorhandler(404)
    def not_found(error):
        if request.path.startswith('/api'):
            return jsonify({'error': 'Not Found', 'message': 'The requested resource was not found on this server.'}), 404
        return render_template('index.html'), 404

    @app.errorhandler(413)
    def payload_too_large(error):
        return jsonify({
            'error': 'File Too Large',
            'message': 'Uploaded file exceeds the maximum allowed limit of 2 MB.'
        }), 413

    @app.errorhandler(500)
    def internal_error(error):
        return jsonify({
            'error': 'Internal Server Error',
            'message': 'An unexpected server error occurred.'
        }), 500

    return app

if __name__ == '__main__':
    application = create_app()
    print("==================================================")
    print(" AttendX Flask Backend Starting")
    print(" Access: http://localhost:5000")
    print("==================================================")
    application.run(host='0.0.0.0', port=5000, debug=False)
