from flask import Flask, session
from config import Config
from models import db, UsuarioInfo
from routes import is_admin
from services.oauth_service import init_oauth
from routes.auth import auth_bp
from routes.main import main_bp
from routes.produtos import produtos_bp
from routes.perfil import perfil_bp
from routes.tags import tags_bp


def _migrate_add_columns(app):
    """Adiciona colunas novas em tabelas existentes (SQLite não suporta IF NOT EXISTS)."""
    with app.app_context():
        conn = db.engine.raw_connection()
        try:
            cur = conn.cursor()
            for stmt in [
                "ALTER TABLE usuario_info ADD COLUMN is_admin BOOLEAN NOT NULL DEFAULT 0",
                "ALTER TABLE tag ADD COLUMN cor VARCHAR(7) NOT NULL DEFAULT '#6c757d'",
            ]:
                try:
                    cur.execute(stmt)
                except Exception:
                    pass  # coluna já existe
            conn.commit()
        finally:
            conn.close()


def _seed_admins(app):
    with app.app_context():
        for matricula in Config.ADMIN_MATRICULAS:
            u = UsuarioInfo.query.filter_by(matricula=matricula).first()
            if u and not u.is_admin:
                u.is_admin = True
        db.session.commit()


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    init_oauth(app)

    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(produtos_bp)
    app.register_blueprint(perfil_bp)
    app.register_blueprint(tags_bp)

    @app.context_processor
    def inject_globals():
        return {
            'is_admin': is_admin(),
            'usuario': session.get('dados_usuario', {}),
        }

    with app.app_context():
        db.create_all()

    _migrate_add_columns(app)
    _seed_admins(app)

    return app


if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, host='0.0.0.0', port=5000)
