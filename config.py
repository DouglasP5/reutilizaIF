import os
from os.path import join, dirname
from dotenv import load_dotenv

dotenv_path = join(dirname(__file__), '.env')
load_dotenv(dotenv_path)

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    
    # Usar SQLite para desenvolvimento local
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///reutilizaif.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    SUAP_API_BASE_URL = "https://suap.ifrn.edu.br"
    ADMIN_MATRICULAS = {'20231041110013'}

