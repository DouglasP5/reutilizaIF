"""
Script para inicializar o banco de dados
Execute este script para criar as tabelas do banco de dados
"""
from app import app, db

with app.app_context():
    # Cria todas as tabelas definidas nos modelos
    db.create_all()
    print("✅ Banco de dados inicializado com sucesso!")
    print("📁 Arquivo criado: site.db")

