from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_socketio import SocketIO
from app.config import Config
import os
from flask_migrate import Migrate
from flask_mail import Mail

# Initialize extensions
db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message_category = 'info'
socketio = SocketIO()
mail = Mail()
migrate = Migrate()

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Initialize extensions with app
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    socketio.init_app(app, cors_allowed_origins="*")
    mail.init_app(app)

    
    # Ensure upload directory exists
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    with app.app_context():
        from app.models import User, UserRole
        admin_user = User.query.filter_by(role=UserRole.ADMIN).first()
        if not admin_user:
            admin_user = User(
                username='admin',
                email='admin@gmail.com',
                role=UserRole.ADMIN
            )
            admin_user.set_password('admin123')  # Set a default password
            db.session.add(admin_user)
            db.session.commit()
            print('Admin user created successfully!')
        else:
            print('Admin user already exists!')
    
    # Register blueprints
    from app.auth.routes import auth_bp as auth
    from app.attachee.routes import attachee_bp as attachee
    from app.assessor.routes import assessor
    from app.org_manager.routes import org_manager
    from app.admin.routes import admin
    from app.main.routes import main
    from app.video.routes import video
    
    app.register_blueprint(auth)
    app.register_blueprint(attachee)
    app.register_blueprint(assessor)
    app.register_blueprint(org_manager)
    app.register_blueprint(admin)
    app.register_blueprint(main)
    app.register_blueprint(video)
    
    # Register error handlers
    from app.errors import register_error_handlers
    register_error_handlers(app)
    
    # Create database tables if they don't exist
    with app.app_context():
        db.create_all()
    
    return app

# Import models to ensure they are registered with SQLAlchemy
from app import models