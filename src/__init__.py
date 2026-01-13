from flask import Flask
from flask_cors import CORS
from src.config import BaseConfig
from src.extensions import db

def create_app():
    app = Flask(__name__)
    CORS(app, supports_credentials=True)
    
    app.config.from_object(BaseConfig)
    
    # session配置
    app.secret_key = 'your-secret-key'
    app.config['SESSION_TYPE'] = 'filesystem'
    
    db.init_app(app)
    
    from src.routes.auth import bp as auth_bp
    from src.routes.facility import bp as facility_bp
    from src.routes.reservation import bp as reservation_bp
    from src.routes.user import bp as user_bp
    from src.routes.main import bp as main_bp
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(facility_bp)
    app.register_blueprint(reservation_bp)
    app.register_blueprint(user_bp)
    app.register_blueprint(main_bp)
    
    return app
