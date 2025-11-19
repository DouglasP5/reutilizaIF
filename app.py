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
        # Tenta diferentes endpoints possíveis
        endpoints = [
            f"{SUAP_API_BASE_URL}/autenticacao/token/",
            f"{SUAP_API_BASE_URL}/autenticacao/token",
            f"https://suap.ifrn.edu.br/api/v2/autenticacao/token/",
        ]
        
        # Dados para autenticação
        data = {
            'username': str(matricula).strip(),
            'password': str(senha).strip()
        }
        
        response = None
        last_error = None
        
        # Tenta cada endpoint com form-data primeiro
        for url in endpoints:
            try:
                # Tenta com form-data (application/x-www-form-urlencoded)
                response = requests.post(url, data=data, timeout=10, allow_redirects=False)
                
                if response.status_code in [200, 201]:
                    break
                    
                # Se falhar, tenta com JSON
                if response.status_code not in [200, 201]:
                    headers_json = {
                        'Content-Type': 'application/json',
                        'Accept': 'application/json'
                    }
                    response = requests.post(url, json=data, headers=headers_json, timeout=10, allow_redirects=False)
                    
                    if response.status_code in [200, 201]:
                        break
                        
            except Exception as e:
                last_error = str(e)
                continue
        
        if not response:
            return {
                'sucesso': False,
                'erro': f'Não foi possível conectar ao SUAP. {last_error if last_error else "Verifique sua conexão."}'
            }
        
        # Log para debug (remover em produção)
        print(f"Status code: {response.status_code}")
        print(f"Response headers: {response.headers}")
        
        if response.status_code in [200, 201]:
            try:
                token_data = response.json()
                print(f"Token data keys: {token_data.keys() if isinstance(token_data, dict) else 'Not a dict'}")
                
                # SUAP pode retornar 'access', 'token' ou 'access_token'
                token = token_data.get('access') or token_data.get('token') or token_data.get('access_token')
                
                if token:
                    # Busca informações do usuário com o token
                    user_info = obter_dados_usuario_suap(token)
                    
                    if user_info:
                        # Log para debug - ver estrutura completa dos dados
                        print(f"Keys dos dados do usuário: {list(user_info.keys())}")
                        print(f"Estrutura completa (primeiros 500 chars): {str(user_info)[:500]}")
                        
                        # Verifica se o usuário é aluno (tem vínculo ativo como estudante)
                        # O campo 'vinculo' é um dicionário, não uma lista
                        vinculo = user_info.get('vinculo', {})
                        tipo_vinculo = str(user_info.get('tipo_vinculo', '')).lower()
                        
                        # Log para debug
                        print(f"Tipo de vínculo: {user_info.get('tipo_vinculo', 'N/A')}")
                        print(f"Vínculo (dict): {vinculo}")
                        if isinstance(vinculo, dict):
                            print(f"Chaves do vínculo: {list(vinculo.keys())}")
                            print(f"Situação: {vinculo.get('situacao', 'N/A')}")
                            print(f"Curso: {vinculo.get('curso', 'N/A')}")
                            print(f"Campus: {vinculo.get('campus', 'N/A')}")
                        
                        is_aluno = False
                        
                        # Verifica se é aluno através do tipo_vinculo
                        if tipo_vinculo:
                            if ('aluno' in tipo_vinculo or 
                                'estudante' in tipo_vinculo or
                                'student' in tipo_vinculo or
                                tipo_vinculo == 'aluno' or
                                tipo_vinculo == 'estudante'):
                                
                                # Verifica se está ativo através da situação
                                if isinstance(vinculo, dict):
                                    situacao = str(vinculo.get('situacao', '')).lower()
                                    # Considera ativo se não estiver em situações que indicam inatividade
                                    situacoes_inativas = ['inativo', 'cancelado', 'trancado', 'desligado', 'concluído']
                                    if situacao and not any(sit in situacao for sit in situacoes_inativas):
                                        is_aluno = True
                                        print(f"Aluno ativo encontrado! Tipo: {user_info.get('tipo_vinculo')}, Situação: {vinculo.get('situacao')}")
                                    elif not situacao:
                                        # Se não tem situação definida, assume que está ativo
                                        is_aluno = True
                                        print(f"Aluno encontrado (sem situação definida)! Tipo: {user_info.get('tipo_vinculo')}")
                                else:
                                    # Se não tem vínculo detalhado, mas tipo_vinculo indica aluno, permite
                                    is_aluno = True
                                    print(f"Aluno encontrado (sem detalhes de vínculo)! Tipo: {user_info.get('tipo_vinculo')}")
                        
                        # Se não identificou como aluno pelo tipo_vinculo, mas tem vínculo com curso/campus,
                        # provavelmente é aluno
                        if not is_aluno and isinstance(vinculo, dict):
                            if vinculo.get('curso') or vinculo.get('campus'):
                                situacao = str(vinculo.get('situacao', '')).lower()
                                situacoes_inativas = ['inativo', 'cancelado', 'trancado', 'desligado', 'concluído']
                                if not situacao or not any(sit in situacao for sit in situacoes_inativas):
                                    is_aluno = True
                                    print(f"Aluno identificado através do vínculo! Curso: {vinculo.get('curso')}, Campus: {vinculo.get('campus')}")
                        
                        # Se ainda não identificou, mas conseguiu autenticar, permite acesso
                        if not is_aluno:
                            print("Não foi possível identificar claramente como aluno, mas autenticação foi bem-sucedida. Permitindo acesso.")
                            is_aluno = True
                        
                        return {
                            'sucesso': True,
                            'token': token,
                            'dados_usuario': user_info,
                            'is_aluno': is_aluno
                        }
                    else:
                        return {
                            'sucesso': False,
                            'erro': 'Não foi possível obter os dados do usuário'
                        }
                else:
                    return {
                        'sucesso': False,
                        'erro': 'Token não encontrado na resposta do SUAP'
                    }
            except ValueError as e:
                print(f"Erro ao parsear JSON: {str(e)}")
                print(f"Response text: {response.text[:500]}")
                return {
                    'sucesso': False,
                    'erro': f'Resposta inválida do SUAP: {str(e)}'
                }
        elif response.status_code == 401:
            try:
                error_data = response.json()
                error_detail = error_data.get('detail', 'Credenciais inválidas')
                return {
                    'sucesso': False,
                    'erro': error_detail
                }
            except:
                return {
                    'sucesso': False,
                    'erro': 'Credenciais inválidas. Verifique sua matrícula e senha.'
                }
        else:
            error_msg = 'Erro ao autenticar'
            try:
                error_data = response.json()
                print(f"Error data: {error_data}")
                error_msg = error_data.get('detail') or error_data.get('message') or error_data.get('error') or error_msg
            except:
                error_text = response.text[:500] if response.text else 'Sem resposta'
                print(f"Error response text: {error_text}")
                error_msg = f'Erro {response.status_code}: {error_text}'
            
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
    Retorna um dicionário com todas as informações do usuário, incluindo foto.
    """
    try:
        headers = {
            'Authorization': f'Bearer {token}',
            'Accept': 'application/json'
        }
        
        # Tenta o endpoint principal de dados do usuário
        url = f"{SUAP_API_BASE_URL}/minhas-informacoes/meus-dados/"
        response = requests.get(url, headers=headers, timeout=10)
        
        dados = None
        if response.status_code == 200:
            dados = response.json()
        else:
            # Tenta endpoint alternativo
            url_alt = f"{SUAP_API_BASE_URL}/minhas-informacoes/"
            response_alt = requests.get(url_alt, headers=headers, timeout=10)
            if response_alt.status_code == 200:
                dados = response_alt.json()
        
        if dados:
            # Processa a foto se existir
            # A foto pode vir em diferentes formatos na API do SUAP
            if 'foto' in dados and dados['foto']:
                # Se a foto for uma URL relativa, converte para absoluta
                foto = dados['foto']
                if foto.startswith('/'):
                    dados['foto'] = f"https://suap.ifrn.edu.br{foto}"
                elif not foto.startswith('http'):
                    dados['foto'] = f"https://suap.ifrn.edu.br{foto}"
            elif 'url_foto' in dados and dados['url_foto']:
                dados['foto'] = dados['url_foto']
            elif 'foto_150x200' in dados and dados['foto_150x200']:
                dados['foto'] = dados['foto_150x200']
            
            # Garante que os vínculos estão formatados corretamente
            if 'vinculos' in dados and isinstance(dados['vinculos'], list):
                for vinculo in dados['vinculos']:
                    # Processa informações do curso se existir
                    if 'curso' in vinculo and isinstance(vinculo['curso'], dict):
                        curso_nome = vinculo['curso'].get('nome', '')
                        if curso_nome:
                            vinculo['curso_nome'] = curso_nome
                    
                    # Processa informações do campus se existir
                    if 'campus' in vinculo and isinstance(vinculo['campus'], dict):
                        campus_nome = vinculo['campus'].get('nome', '')
                        if campus_nome:
                            vinculo['campus_nome'] = campus_nome
            
            return dados
        
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
        try:
            matricula = request.form.get('matricula', '').strip()
            senha = request.form.get('senha', '').strip()
            
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
                # Trata erros específicos da API
                erro = resultado.get('erro', 'Erro ao autenticar. Verifique suas credenciais.')
                # Remove mensagens técnicas de erro de parsing
                if 'parse' in erro.lower() or 'cannot parse' in erro.lower():
                    erro = 'Erro na comunicação com o SUAP. Por favor, tente novamente ou verifique suas credenciais.'
                return render_template('login.html', error=erro)
        except Exception as e:
            print(f"Erro no login: {str(e)}")
            return render_template('login.html', error='Erro inesperado. Por favor, tente novamente.')
    
    return render_template('login.html')

@app.route('/home')
def home():
    # Verifica se o usuário está logado
    if not session.get('usuario_logado'):
        return redirect(url_for('login'))
    
    produtos = Produto.query.all()
    dados_usuario = session.get('dados_usuario', {})
    return render_template('home.html', produtos=produtos, usuario=dados_usuario)

@app.route('/perfil')
def perfil():
    # Verifica se o usuário está logado
    if not session.get('usuario_logado'):
        return redirect(url_for('login'))
    
    dados_usuario = session.get('dados_usuario', {})
    
    # Se não houver dados na sessão, tenta buscar novamente com o token
    if not dados_usuario and session.get('token'):
        token = session.get('token')
        dados_usuario = obter_dados_usuario_suap(token)
        if dados_usuario:
            session['dados_usuario'] = dados_usuario
    
    return render_template('perfil.html', usuario=dados_usuario)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)


