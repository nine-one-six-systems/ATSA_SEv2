from flask import Flask, render_template
from config import SQLALCHEMY_DATABASE_URI, UPLOAD_FOLDER
from database.init_db import init_database
import os

def create_app():
    app = Flask(__name__, template_folder='templates', static_folder='static')
    app.config['SQLALCHEMY_DATABASE_URI'] = SQLALCHEMY_DATABASE_URI
    app.config['UPLOAD_FOLDER'] = str(UPLOAD_FOLDER)
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
    
    # Ensure upload directory exists
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    
    # Initialize database
    from models import db
    db.init_app(app)
    
    # Register blueprints
    from routes.api import api_bp
    app.register_blueprint(api_bp)
    
    # Register main routes
    @app.route('/')
    def index():
        return render_template('index.html')
    
    @app.route('/clients.html')
    def clients():
        return render_template('clients.html')
    
    @app.route('/upload.html')
    def upload():
        return render_template('upload.html')
    
    @app.route('/analysis.html')
    def analysis():
        return render_template('analysis.html')
    
    @app.route('/calculator.html')
    def calculator():
        return render_template('calculator.html')

    @app.route('/joint-analysis.html')
    def joint_analysis():
        return render_template('joint_analysis.html')

    # Initialize database tables
    with app.app_context():
        init_database()
    
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, host='0.0.0.0', port=5555)

