from app import app, db

with app.app_context():
    db.create_all()
    print("✅ Banco de dados inicializado com sucesso!")
    print("📁 Arquivo criado: site.db")

