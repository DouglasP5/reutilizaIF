from functools import wraps
from flask import session, redirect, url_for


def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get('usuario_logado'):
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated


def is_admin():
    return session.get('is_admin', False)


def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not is_admin():
            return redirect(url_for('main.home'))
        return f(*args, **kwargs)
    return decorated
