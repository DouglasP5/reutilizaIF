from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import inspect, text
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
    usuario_matricula = db.Column(db.String(20))
    usuario_nome = db.Column(db.String(150))


class UsuarioInfo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    matricula = db.Column(db.String(20), unique=True, nullable=False)
    telefone = db.Column(db.String(30))
    nome = db.Column(db.String(150))
    curso = db.Column(db.String(150))
    campus = db.Column(db.String(150))
    foto_url = db.Column(db.String(300))


#API do SUAP
SUAP_API_BASE_URL = "https://suap.ifrn.edu.br/api/v2"
ADMIN_MATRICULAS = {'20231041110013'}


def ensure_schema():
    inspector = inspect(db.engine)
    tables = inspector.get_table_names()

    def existing_columns(table):
        if table not in tables:
            return set()
        return {col['name'] for col in inspector.get_columns(table)}

    produto_cols = existing_columns('produto')
    for col_name, ddl in {
        'usuario_matricula': 'VARCHAR(20)',
        'usuario_nome': 'VARCHAR(150)'
    }.items():
        if col_name not in produto_cols:
            db.session.execute(text(f'ALTER TABLE produto ADD COLUMN {col_name} {ddl}'))
            db.session.commit()

    usuario_cols = existing_columns('usuario_info')
    for col_name, ddl in {
        'telefone': 'VARCHAR(30)',
        'nome': 'VARCHAR(150)',
        'curso': 'VARCHAR(150)',
        'campus': 'VARCHAR(150)',
        'foto_url': 'VARCHAR(300)'
    }.items():
        if col_name not in usuario_cols:
            db.session.execute(text(f'ALTER TABLE usuario_info ADD COLUMN {col_name} {ddl}'))
            db.session.commit()


def salvar_info_usuario(matricula, dados_usuario):
    if not matricula:
        return

    info = UsuarioInfo.query.filter_by(matricula=matricula).first()
    if not info:
        info = UsuarioInfo(matricula=matricula)
        db.session.add(info)

    info.nome = dados_usuario.get('nome_usual') or dados_usuario.get('nome') or info.nome

    vinculo = dados_usuario.get('vinculo') or {}
    curso = None
    campus = None
    if isinstance(vinculo, dict):
        curso = vinculo.get('curso')
        if isinstance(curso, dict):
            curso = curso.get('nome')
        campus = vinculo.get('campus')
        if isinstance(campus, dict):
            campus = campus.get('nome')

    if curso:
        info.curso = curso
    if campus:
        info.campus = campus

    foto = dados_usuario.get('url_foto_150x200') or dados_usuario.get('url_foto_75x100') or dados_usuario.get('foto')
    if foto:
        info.foto_url = foto

    db.session.commit()


def autenticar_suap(matricula, senha):
    
    try:
    
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
        
        for url in endpoints:
            try:
                response = requests.post(url, data=data, timeout=10, allow_redirects=False)
                
                if response.status_code in [200, 201]:
                    break
                    
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
        
        print(f"Status code: {response.status_code}")
        print(f"Response headers: {response.headers}")
        
        if response.status_code in [200, 201]:
            try:
                token_data = response.json()
                print(f"Token data keys: {token_data.keys() if isinstance(token_data, dict) else 'Not a dict'}")
                
                token = token_data.get('access') or token_data.get('token') or token_data.get('access_token')
                
                if token:
                    user_info = obter_dados_usuario_suap(token)
                    
                    if user_info:
                        print(f"Keys dos dados do usuário: {list(user_info.keys())}")
                        print(f"Estrutura completa (primeiros 500 chars): {str(user_info)[:500]}")
                        
                        vinculo = user_info.get('vinculo', {})
                        tipo_vinculo = str(user_info.get('tipo_vinculo', '')).lower()
                        
                        print(f"Tipo de vínculo: {user_info.get('tipo_vinculo', 'N/A')}")
                        print(f"Vínculo (dict): {vinculo}")
                        if isinstance(vinculo, dict):
                            print(f"Chaves do vínculo: {list(vinculo.keys())}")
                            print(f"Situação: {vinculo.get('situacao', 'N/A')}")
                            print(f"Curso: {vinculo.get('curso', 'N/A')}")
                            print(f"Campus: {vinculo.get('campus', 'N/A')}")
                        
                        is_aluno = False
                        
                        if tipo_vinculo:
                            if ('aluno' in tipo_vinculo or 
                                'estudante' in tipo_vinculo or
                                'student' in tipo_vinculo or
                                tipo_vinculo == 'aluno' or
                                tipo_vinculo == 'estudante'):
                                
                                if isinstance(vinculo, dict):
                                    situacao = str(vinculo.get('situacao', '')).lower()
                                    situacoes_inativas = ['inativo', 'cancelado', 'trancado', 'desligado', 'concluído']
                                    if situacao and not any(sit in situacao for sit in situacoes_inativas):
                                        is_aluno = True
                                        print(f"Aluno ativo encontrado! Tipo: {user_info.get('tipo_vinculo')}, Situação: {vinculo.get('situacao')}")
                                    elif not situacao:
                                        is_aluno = True
                                        print(f"Aluno encontrado (sem situação definida)! Tipo: {user_info.get('tipo_vinculo')}")
                                else:
                                    is_aluno = True
                                    print(f"Aluno encontrado (sem detalhes de vínculo)! Tipo: {user_info.get('tipo_vinculo')}")
                        
                        if not is_aluno and isinstance(vinculo, dict):
                            if vinculo.get('curso') or vinculo.get('campus'):
                                situacao = str(vinculo.get('situacao', '')).lower()
                                situacoes_inativas = ['inativo', 'cancelado', 'trancado', 'desligado', 'concluído']
                                if not situacao or not any(sit in situacao for sit in situacoes_inativas):
                                    is_aluno = True
                                    print(f"Aluno identificado através do vínculo! Curso: {vinculo.get('curso')}, Campus: {vinculo.get('campus')}")
                        
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
    try:
        headers = {
            'Authorization': f'Bearer {token}',
            'Accept': 'application/json'
        }
        
        url = f"{SUAP_API_BASE_URL}/minhas-informacoes/meus-dados/"
        response = requests.get(url, headers=headers, timeout=10)
        
        dados = None
        if response.status_code == 200:
            dados = response.json()
        else:
            url_alt = f"{SUAP_API_BASE_URL}/minhas-informacoes/"
            response_alt = requests.get(url_alt, headers=headers, timeout=10)
            if response_alt.status_code == 200:
                dados = response_alt.json()
        
        if dados:
            if 'foto' in dados and dados['foto']:
                foto = dados['foto']
                if foto.startswith('/'):
                    dados['foto'] = f"https://suap.ifrn.edu.br{foto}"
                elif not foto.startswith('http'):
                    dados['foto'] = f"https://suap.ifrn.edu.br{foto}"
            elif 'url_foto' in dados and dados['url_foto']:
                dados['foto'] = dados['url_foto']
            elif 'foto_150x200' in dados and dados['foto_150x200']:
                dados['foto'] = dados['foto_150x200']
            
            if 'vinculos' in dados and isinstance(dados['vinculos'], list):
                for vinculo in dados['vinculos']:
                    if 'curso' in vinculo and isinstance(vinculo['curso'], dict):
                        curso_nome = vinculo['curso'].get('nome', '')
                        if curso_nome:
                            vinculo['curso_nome'] = curso_nome
                    
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


def usuario_e_admin():
    return session.get('matricula') in ADMIN_MATRICULAS


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        try:
            matricula = request.form.get('matricula', '').strip()
            senha = request.form.get('senha', '').strip()
            
            if not matricula or not senha:
                return render_template('login.html', error='Por favor, preencha todos os campos')
            
            resultado = autenticar_suap(matricula, senha)
            
            if resultado['sucesso']:
                if resultado.get('is_aluno'):
                    session['usuario_logado'] = True
                    session['matricula'] = matricula
                    session['dados_usuario'] = resultado.get('dados_usuario', {})
                    session['token'] = resultado.get('token')

                    salvar_info_usuario(matricula, session['dados_usuario'])
                    
                    return redirect(url_for('home'))
                else:
                    return render_template('login.html', error='Acesso restrito apenas para alunos com matrícula ativa no IFRN')
            else:
                erro = resultado.get('erro', 'Erro ao autenticar. Verifique suas credenciais.')
                if 'parse' in erro.lower() or 'cannot parse' in erro.lower():
                    erro = 'Erro na comunicação com o SUAP. Por favor, tente novamente ou verifique suas credenciais.'
                return render_template('login.html', error=erro)
        except Exception as e:
            print(f"Erro no login: {str(e)}")
            return render_template('login.html', error='Erro inesperado. Por favor, tente novamente.')
    
    return render_template('login.html')

@app.route('/home')
def home():
    if not session.get('usuario_logado'):
        return redirect(url_for('login'))
    
    produtos = Produto.query.all()
    dados_usuario = session.get('dados_usuario', {})
    return render_template(
        'home.html',
        produtos=produtos,
        usuario=dados_usuario,
        is_admin=usuario_e_admin(),
        pode_criar=session.get('usuario_logado', False)
    )


@app.route('/produtos/novo', methods=['GET', 'POST'])
def novo_produto():
    if not session.get('usuario_logado'):
        return redirect(url_for('login'))

    if request.method == 'POST':
        nome = request.form.get('nome', '').strip()
        preco = request.form.get('preco', '').strip()
        descricao = request.form.get('descricao', '').strip()

        if not nome or not preco:
            return render_template('produto_form.html', error='Informe nome e preço.', produto=None, acao='novo')

        try:
            preco_valor = float(str(preco).replace(',', '.'))
        except ValueError:
            return render_template('produto_form.html', error='Preço inválido. Use somente números.', produto=None, acao='novo')

        dados_usuario = session.get('dados_usuario', {})
        nome_usuario = dados_usuario.get('nome_usual') or dados_usuario.get('nome') or 'Usuário'
        matricula_usuario = session.get('matricula')

        produto = Produto(
            nome=nome,
            preco=preco_valor,
            descricao=descricao,
            usuario_nome=nome_usuario,
            usuario_matricula=matricula_usuario
        )
        db.session.add(produto)
        db.session.commit()
        return redirect(url_for('home'))

    return render_template('produto_form.html', produto=None, acao='novo')


@app.route('/produtos/<int:produto_id>/editar', methods=['GET', 'POST'])
def editar_produto(produto_id):
    if not session.get('usuario_logado'):
        return redirect(url_for('login'))
    if not usuario_e_admin():
        return redirect(url_for('home'))

    produto = Produto.query.get_or_404(produto_id)

    if request.method == 'POST':
        nome = request.form.get('nome', '').strip()
        preco = request.form.get('preco', '').strip()
        descricao = request.form.get('descricao', '').strip()

        if not nome or not preco:
            return render_template('produto_form.html', error='Informe nome e preço.', produto=produto, acao='editar')

        try:
            preco_valor = float(str(preco).replace(',', '.'))
        except ValueError:
            return render_template('produto_form.html', error='Preço inválido. Use somente números.', produto=produto, acao='editar')

        produto.nome = nome
        produto.preco = preco_valor
        produto.descricao = descricao
        db.session.commit()
        return redirect(url_for('home'))

    return render_template('produto_form.html', produto=produto, acao='editar')


@app.route('/produtos/<int:produto_id>/excluir', methods=['POST'])
def excluir_produto(produto_id):
    if not session.get('usuario_logado'):
        return redirect(url_for('login'))
    if not usuario_e_admin():
        return redirect(url_for('home'))

    produto = Produto.query.get_or_404(produto_id)
    db.session.delete(produto)
    db.session.commit()
    return redirect(url_for('home'))

@app.route('/perfil', methods=['GET', 'POST'])
def perfil():
    if not session.get('usuario_logado'):
        return redirect(url_for('login'))
    
    dados_usuario = session.get('dados_usuario', {})
    matricula = session.get('matricula')
    info = UsuarioInfo.query.filter_by(matricula=matricula).first()
    
    if request.method == 'POST':
        telefone = request.form.get('telefone', '').strip()
        if not info:
            info = UsuarioInfo(matricula=matricula)
            db.session.add(info)
        info.telefone = telefone or None
        db.session.commit()
        return redirect(url_for('perfil'))

    if not dados_usuario and session.get('token'):
        token = session.get('token')
        dados_usuario = obter_dados_usuario_suap(token)
        if dados_usuario:
            session['dados_usuario'] = dados_usuario
    
    telefone = info.telefone if info else ''
    return render_template('perfil.html', usuario=dados_usuario, telefone=telefone)


@app.route('/usuarios/<matricula>')
def usuario_publico(matricula):
    if not session.get('usuario_logado'):
        return redirect(url_for('login'))

    info = UsuarioInfo.query.filter_by(matricula=matricula).first()
    produtos = Produto.query.filter_by(usuario_matricula=matricula).all()

    if not info and not produtos:
        return render_template('usuario_publico.html', encontrado=False, matricula=matricula)

    nome = None
    if info and info.nome:
        nome = info.nome
    elif produtos:
        nome = produtos[0].usuario_nome

    return render_template(
        'usuario_publico.html',
        encontrado=True,
        matricula=matricula,
        info=info,
        produtos=produtos,
        nome=nome or matricula
    )

# Compatibilidade com Flask 2.x e 3.x: mapeia o decorator de startup correto
if hasattr(app, 'before_serving'):
    before_start = app.before_serving
elif hasattr(app, 'before_first_request'):
    before_start = app.before_first_request
else:
    def before_start(f):
        return f


@before_start
def inicializar():
    db.create_all()
    ensure_schema()


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        ensure_schema()
    app.run(debug=True)
