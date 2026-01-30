from flask import Blueprint, render_template, request, redirect, url_for, session
from models import db, UsuarioInfo
from utils import autenticar_suap, obter_dados_usuario_suap, salvar_info_usuario
from config import Config
from werkzeug.security import generate_password_hash, check_password_hash

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        try:
            matricula = request.form.get('matricula', '').strip()
            senha = request.form.get('senha', '').strip()
            
            if not matricula or not senha:
                return render_template('login.html', error='Por favor, preencha todos os campos')
            
            usuario_info = UsuarioInfo.query.filter_by(matricula=matricula).first()
            
            if usuario_info and usuario_info.senha_hash:
                if check_password_hash(usuario_info.senha_hash, senha):
                    session['usuario_logado'] = True
                    session['matricula'] = matricula
                    session['dados_usuario'] = {
                        'nome_usual': usuario_info.nome,
                        'nome': usuario_info.nome,
                        'matricula': matricula
                    }
                    if usuario_info.jwt_token:
                        session['token'] = usuario_info.jwt_token
                    return redirect(url_for('main.home'))
                else:
                    return render_template('login.html', error='Senha incorreta.')
            else:
                resultado = autenticar_suap(matricula, senha)
                
                if resultado['sucesso']:
                    if resultado.get('is_aluno'):
                        session['registro_matricula'] = matricula
                        session['registro_token'] = resultado.get('token')
                        session['registro_dados'] = resultado.get('dados_usuario', {})
                        return redirect(url_for('auth.registro'))
                    else:
                        return render_template('login.html', error='Acesso restrito apenas para alunos com matrícula ativa no IFRN')
                else:
                    erro = resultado.get('erro', 'Erro ao autenticar. Verifique suas credenciais.')
                    if 'parse' in erro.lower() or 'cannot parse' in erro.lower():
                        erro = 'Erro na comunicação com o SUAP. Por favor, tente novamente ou verifique suas credenciais.'
                    return render_template('login.html', error=erro)
        except Exception as e:
            return render_template('login.html', error='Erro inesperado. Por favor, tente novamente.')
    
    return render_template('login.html')


@auth_bp.route('/registro', methods=['GET', 'POST'])
def registro():
    if not session.get('registro_matricula'):
        return redirect(url_for('auth.login'))
    
    matricula = session.get('registro_matricula')
    token = session.get('registro_token')
    dados_usuario = session.get('registro_dados', {})
    
    if request.method == 'POST':
        try:
            senha = request.form.get('senha', '').strip()
            confirmar_senha = request.form.get('confirmar_senha', '').strip()
            
            if not senha or not confirmar_senha:
                return render_template('registro.html', error='Por favor, preencha todos os campos', 
                                     matricula=matricula, dados_usuario=dados_usuario)
            
            if senha != confirmar_senha:
                return render_template('registro.html', error='As senhas não coincidem', 
                                     matricula=matricula, dados_usuario=dados_usuario)
            
            if len(senha) < 6:
                return render_template('registro.html', error='A senha deve ter pelo menos 6 caracteres', 
                                     matricula=matricula, dados_usuario=dados_usuario)
            
            usuario_info = UsuarioInfo.query.filter_by(matricula=matricula).first()
            if not usuario_info:
                usuario_info = UsuarioInfo(matricula=matricula)
                db.session.add(usuario_info)
            
            nome = (dados_usuario.get('nome_usual') or 
                   dados_usuario.get('nome_social') or 
                   dados_usuario.get('nome') or 
                   dados_usuario.get('nome_registro') or
                   (dados_usuario.get('primeiro_nome', '') + ' ' + dados_usuario.get('ultimo_nome', '')).strip() or
                   None)
            
            if nome:
                usuario_info.nome = nome
            usuario_info.jwt_token = token
            usuario_info.senha_hash = generate_password_hash(senha)
            
            vinculo = dados_usuario.get('vinculo') or {}
            if isinstance(vinculo, dict):
                curso = vinculo.get('curso')
                if isinstance(curso, dict):
                    curso = curso.get('nome')
                campus = vinculo.get('campus')
                if isinstance(campus, dict):
                    campus = campus.get('nome')
                if curso:
                    usuario_info.curso = curso
                if campus:
                    usuario_info.campus = campus
            
            foto = dados_usuario.get('url_foto_150x200') or dados_usuario.get('url_foto_75x100') or dados_usuario.get('foto')
            if foto:
                usuario_info.foto_url = foto
            
            db.session.commit()
            
            session.pop('registro_matricula', None)
            session.pop('registro_token', None)
            session.pop('registro_dados', None)
            
            session['usuario_logado'] = True
            session['matricula'] = matricula
            session['dados_usuario'] = dados_usuario
            session['token'] = token
            
            return redirect(url_for('main.home'))
        except Exception as e:
            return render_template('registro.html', error='Erro ao criar conta. Por favor, tente novamente.', 
                                 matricula=matricula, dados_usuario=dados_usuario)
    
    return render_template('registro.html', matricula=matricula, dados_usuario=dados_usuario)


@auth_bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('auth.login'))

