from flask import Blueprint, render_template, request, redirect, url_for, session
from models import UsuarioInfo, db
from services.suap_service import autenticar_suap
from services.auth_service import AuthService
from services.oauth_service import oauth

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


@auth_bp.route('/login/google')
def login_google():
    redirect_uri = url_for('auth.callback_google', _external=True)
    return oauth.google.authorize_redirect(redirect_uri)


@auth_bp.route('/login/google/callback')
def callback_google():
    try:
        token = oauth.google.authorize_access_token()
    except Exception as e:
        return render_template('login.html', error=f'Falha na autenticação com Google. [{e}]')

    dados = token.get('userinfo') or {}
    email = dados.get('email')
    if not email:
        return render_template('login.html', error='Não foi possível obter o e-mail da conta Google.')

    usuario = UsuarioInfo.obter_ou_criar(email)
    usuario.nome = dados.get('name') or usuario.nome
    usuario.foto_url = dados.get('picture') or usuario.foto_url
    db.session.commit()

    AuthService.iniciar_sessao(usuario)
    return redirect(url_for('main.home'))


@auth_bp.route('/cadastro', methods=['GET', 'POST'])
def cadastro():
    if request.method != 'POST':
        return render_template('cadastro.html')

    nome = request.form.get('nome', '').strip()
    matricula = request.form.get('matricula', '').strip()
    curso = request.form.get('curso', '').strip()
    senha = request.form.get('senha', '').strip()
    confirmar = request.form.get('confirmar_senha', '').strip()

    form_valores = {'nome': nome, 'matricula': matricula, 'curso': curso}

    if not nome or not matricula:
        return render_template('cadastro.html', error='Por favor, preencha todos os campos', **form_valores)

    erro = _validar_senha(senha, confirmar)
    if erro:
        return render_template('cadastro.html', error=erro, **form_valores)

    resultado = AuthService.cadastrar_local(nome, matricula, senha, curso)
    if not resultado['sucesso']:
        return render_template('cadastro.html', error=resultado['erro'], **form_valores)

    AuthService.iniciar_sessao(resultado['usuario'])
    return redirect(url_for('main.home'))


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
