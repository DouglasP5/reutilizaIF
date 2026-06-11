from flask import Blueprint, render_template, request, redirect, url_for, session
from services.suap_service import autenticar_suap
from services.auth_service import AuthService

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method != 'POST':
        return render_template('login.html')

    matricula = request.form.get('matricula', '').strip()
    senha = request.form.get('senha', '').strip()

    if not matricula or not senha:
        return render_template('login.html', error='Por favor, preencha todos os campos')

    resultado_local = AuthService.login_local(matricula, senha)
    if resultado_local['sucesso']:
        AuthService.iniciar_sessao(resultado_local['usuario'], resultado_local['usuario'].jwt_token)
        return redirect(url_for('main.home'))
    if resultado_local['erro']:
        return render_template('login.html', error=resultado_local['erro'])

    resultado = autenticar_suap(matricula, senha)
    if not resultado['sucesso']:
        return render_template('login.html', error=resultado.get('erro', 'Erro ao autenticar.'))

    session['registro_matricula'] = matricula
    session['registro_token'] = resultado['token']
    session['registro_dados'] = resultado['dados_usuario']
    return redirect(url_for('auth.registro'))


@auth_bp.route('/registro', methods=['GET', 'POST'])
def registro():
    if not session.get('registro_matricula'):
        return redirect(url_for('auth.login'))

    matricula = session['registro_matricula']
    token = session['registro_token']
    dados_usuario = session.get('registro_dados', {})

    if request.method != 'POST':
        return render_template('registro.html', matricula=matricula, dados_usuario=dados_usuario)

    senha = request.form.get('senha', '').strip()
    confirmar = request.form.get('confirmar_senha', '').strip()

    erro = _validar_senha(senha, confirmar)
    if erro:
        return render_template('registro.html', error=erro, matricula=matricula, dados_usuario=dados_usuario)

    usuario = AuthService.registrar(matricula, senha, token, dados_usuario)

    session.pop('registro_matricula', None)
    session.pop('registro_token', None)
    session.pop('registro_dados', None)

    AuthService.iniciar_sessao(usuario, token)
    session['dados_usuario'].update(dados_usuario)
    return redirect(url_for('main.home'))


@auth_bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('auth.login'))


def _validar_senha(senha, confirmar):
    if not senha or not confirmar:
        return 'Por favor, preencha todos os campos'
    if senha != confirmar:
        return 'As senhas não coincidem'
    if len(senha) < 6:
        return 'A senha deve ter pelo menos 6 caracteres'
    return None
