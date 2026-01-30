from flask import Blueprint, render_template, request, redirect, url_for, session
from models import db, UsuarioInfo, Produto
from utils import obter_dados_usuario_suap
from config import Config

perfil_bp = Blueprint('perfil', __name__)

def usuario_e_admin():
    return session.get('matricula') in Config.ADMIN_MATRICULAS

@perfil_bp.route('/perfil', methods=['GET', 'POST'])
def perfil():
    if not session.get('usuario_logado'):
        return redirect(url_for('auth.login'))
    
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
        return redirect(url_for('perfil.perfil'))

    if not dados_usuario and session.get('token'):
        token = session.get('token')
        dados_usuario = obter_dados_usuario_suap(token)
        if dados_usuario:
            session['dados_usuario'] = dados_usuario
    
    telefone = info.telefone if info else ''
    return render_template('perfil.html', usuario=dados_usuario, telefone=telefone, is_admin=usuario_e_admin())


@perfil_bp.route('/usuarios/<matricula>', methods=['GET', 'POST'])
def usuario_publico(matricula):
    if not session.get('usuario_logado'):
        return redirect(url_for('auth.login'))

    if request.method == 'POST':
        if not usuario_e_admin():
            return redirect(url_for('perfil.usuario_publico', matricula=matricula))
        telefone = request.form.get('telefone', '').strip() or None
        info = UsuarioInfo.query.filter_by(matricula=matricula).first()
        if not info:
            info = UsuarioInfo(matricula=matricula)
            db.session.add(info)
        info.telefone = telefone
        db.session.commit()
        return redirect(url_for('perfil.usuario_publico', matricula=matricula))

    info = UsuarioInfo.query.filter_by(matricula=matricula).first()
    produtos = Produto.query.filter_by(usuario_matricula=matricula).all()

    if not info and not produtos:
        return render_template('perfil.html', usuario=None, telefone='', is_admin=usuario_e_admin())

    usuario = {}
    if info:
        usuario['matricula'] = info.matricula
        usuario['nome'] = info.nome
        usuario['foto'] = info.foto_url
        usuario['url_foto_150x200'] = info.foto_url
        usuario['url_foto_75x100'] = info.foto_url
        usuario['vinculo'] = {
            'curso': {'nome': info.curso} if info.curso else None,
            'campus': {'nome': info.campus} if info.campus else None
        }
    else:
        nome = produtos[0].usuario_nome if produtos else matricula
        usuario['matricula'] = matricula
        usuario['nome'] = nome

    telefone = info.telefone if info else ''

    return render_template(
        'perfil.html',
        usuario=usuario,
        telefone=telefone,
        is_admin=usuario_e_admin()
    )



