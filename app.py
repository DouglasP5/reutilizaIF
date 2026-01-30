from flask import Flask
from config import Config
from models import db
from routes.auth import auth_bp
from routes.main import main_bp
from routes.produtos import produtos_bp
from routes.perfil import perfil_bp

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    db.init_app(app)
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(produtos_bp)
    app.register_blueprint(perfil_bp)
    
    with app.app_context():
        db.create_all()
    
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, host='0.0.0.0', port=5000)
