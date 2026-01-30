from app import create_app
from models import db
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

app = create_app()

with app.app_context():
    db.create_all()
