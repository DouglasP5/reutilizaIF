from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
import requests
import os



app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

class Produto(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    preco = db.Column(db.Float, nullable=False)
    descricao = db.Column(db.String(200))


# URL base da API do SUAP
SUAP_API_BASE_URL = "https://suap.ifrn.edu.br/api/v2"


def autenticar_suap(matricula, senha):
    """
    Autentica um usuário na API do SUAP do IFRN.
    Retorna um dicionário com status, token e dados do usuário se bem-sucedido.
    """
    try:
        # O SUAP geralmente usa form-data ao invés de JSON
        url = f"{SUAP_API_BASE_URL}/autenticacao/token/"
        
        # Dados para autenticação usando form-data
        data = {
            'username': matricula,
            'password': senha
        }
        
        # Faz a requisição POST para autenticação (sem Content-Type para form-data)
        response = requests.post(url, data=data, timeout=10)
        
        if response.status_code == 200:
            token_data = response.json()
            # SUAP pode retornar 'access', 'token' ou 'access_token'
            token = token_data.get('access') or token_data.get('token') or token_data.get('access_token')
            
            if token:
                # Busca informações do usuário com o token
                user_info = obter_dados_usuario_suap(token)
                
                if user_info:
                    # Verifica se o usuário é aluno (tem vínculo ativo como estudante)
                    vinculos = user_info.get('vinculos', [])
                    is_aluno = any(
                        (vinculo.get('tipo_vinculo') == 'Aluno' or 
                         vinculo.get('tipo_vinculo', '').upper() == 'ALUNO' or
                         'aluno' in vinculo.get('tipo_vinculo', '').lower()) and 
                        vinculo.get('ativo', False)
                        for vinculo in vinculos
                    )
                    
                    return {
                        'sucesso': True,
                        'token': token,
                        'dados_usuario': user_info,
                        'is_aluno': is_aluno
                    }
            
            return {
                'sucesso': False,
                'erro': 'Não foi possível obter o token de acesso'
            }
        elif response.status_code == 401:
            return {
                'sucesso': False,
                'erro': 'Credenciais inválidas. Verifique sua matrícula e senha.'
            }
        else:
            error_msg = 'Erro ao autenticar'
            try:
                error_data = response.json()
                error_msg = error_data.get('detail') or error_data.get('message') or error_msg
            except:
                pass
            
            return {
                'sucesso': False,
                'erro': error_msg
            }
            
    except requests.exceptions.Timeout:
        return {
            'sucesso': False,
            'erro': 'Timeout ao conectar com o SUAP. Tente novamente.'
        }
    except requests.exceptions.RequestException as e:
        return {
            'sucesso': False,
            'erro': f'Erro ao conectar com o SUAP: {str(e)}'
        }
    except Exception as e:
        return {
            'sucesso': False,
            'erro': f'Erro inesperado: {str(e)}'
        }


def obter_dados_usuario_suap(token):
    """
    Obtém os dados do usuário autenticado na API do SUAP.
    """
    try:
        url = f"{SUAP_API_BASE_URL}/minhas-informacoes/meus-dados/"
        
        headers = {
            'Authorization': f'Bearer {token}'
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            return response.json()
        else:
            # Tenta endpoint alternativo
            url_alt = f"{SUAP_API_BASE_URL}/minhas-informacoes/"
            response_alt = requests.get(url_alt, headers=headers, timeout=10)
            if response_alt.status_code == 200:
                return response_alt.json()
            return None
            
    except Exception as e:
        print(f"Erro ao obter dados do usuário: {str(e)}")
        return None

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        matricula = request.form.get('matricula')
        senha = request.form.get('senha')
        
        if not matricula or not senha:
            return render_template('login.html', error='Por favor, preencha todos os campos')
        
        # Autentica no SUAP
        resultado = autenticar_suap(matricula, senha)
        
        if resultado['sucesso']:
            # Verifica se é aluno ativo
            if resultado.get('is_aluno'):
                # Salva informações na sessão
                session['usuario_logado'] = True
                session['matricula'] = matricula
                session['dados_usuario'] = resultado.get('dados_usuario', {})
                session['token'] = resultado.get('token')
                
                return redirect(url_for('home'))
            else:
                return render_template('login.html', error='Acesso restrito apenas para alunos com matrícula ativa no IFRN')
        else:
            return render_template('login.html', error=resultado.get('erro', 'Erro ao autenticar. Verifique suas credenciais.'))
    
    return render_template('login.html')

@app.route('/cadastro-usuario', methods=['GET', 'POST'])
def cadastro_usuario():
    if request.method == 'POST':
        matricula = request.form.get('matricula')
        senha = request.form.get('senha')
        confirmar_senha = request.form.get('confirmar_senha')
        
        if not matricula or not senha or not confirmar_senha:
            return render_template('cadastro-usuario.html', error='Por favor, preencha todos os campos')
        
        if senha != confirmar_senha:
            return render_template('cadastro-usuario.html', error='As senhas não coincidem')
        
        # Autentica no SUAP para verificar se as credenciais são válidas e se é aluno
        resultado = autenticar_suap(matricula, senha)
        
        if resultado['sucesso']:
            # Verifica se é aluno ativo
            if resultado.get('is_aluno'):
                # Salva informações na sessão e redireciona para home
                session['usuario_logado'] = True
                session['matricula'] = matricula
                session['dados_usuario'] = resultado.get('dados_usuario', {})
                session['token'] = resultado.get('token')
                
                return redirect(url_for('home'))
            else:
                return render_template('cadastro-usuario.html', error='Acesso restrito apenas para alunos com matrícula ativa no IFRN')
        else:
            return render_template('cadastro-usuario.html', error=resultado.get('erro', 'Erro ao autenticar. Verifique suas credenciais.'))
    
    return render_template('cadastro-usuario.html')

@app.route('/home')
def home():
    # Verifica se o usuário está logado
    if not session.get('usuario_logado'):
        return redirect(url_for('login'))
    
    produtos = Produto.query.all()
    dados_usuario = session.get('dados_usuario', {})
    return render_template('home.html', produtos=produtos, usuario=dados_usuario)


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)


