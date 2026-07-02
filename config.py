import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///reutilizaif.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SUAP_API_BASE_URL = 'https://suap.ifrn.edu.br'
    ADMIN_MATRICULAS = {'20231041110013'}

    GOOGLE_CLIENT_ID = os.environ.get('GOOGLE_CLIENT_ID', '')
    GOOGLE_CLIENT_SECRET = os.environ.get('GOOGLE_CLIENT_SECRET', '')
