from flask import Blueprint, render_template, request, redirect, url_for, session
from models import db, UsuarioInfo, Produto
from services.suap_service import obter_dados_usuario_suap
from routes import login_required

perfil_bp = Blueprint('perfil', __name__)


def _montar_perfil_publico(info, produtos):
    if info:
        return {
            'matricula': info.matricula,
            'nome': info.nome,
            'foto': info.foto_url,
            'url_foto_150x200': info.foto_url,
            'vinculo': {
                'curso': {'nome': info.curso} if info.curso else None,
                'campus': {'nome': info.campus} if info.campus else None,
            },
        }
    matricula = produtos[0].usuario_matricula if produtos else ''
    return {'matricula': matricula, 'nome': produtos[0].usuario_nome if produtos else matricula}


@perfil_bp.route('/perfil', methods=['GET', 'POST'])
@login_required
def perfil():
    matricula = session.get('matricula')
    info = UsuarioInfo.query.filter_by(matricula=matricula).first()

    if request.method == 'POST':
        usuario = UsuarioInfo.obter_ou_criar(matricula)
        usuario.telefone = request.form.get('telefone', '').strip() or None
        db.session.commit()
        return redirect(url_for('perfil.perfil'))

    dados_usuario = session.get('dados_usuario', {})
    if not dados_usuario and session.get('token'):
        dados_usuario = obter_dados_usuario_suap(session['token']) or {}
        session['dados_usuario'] = dados_usuario

    return render_template('perfil.html',
        usuario=dados_usuario,
        telefone=info.telefone if info else '')


@perfil_bp.route('/usuarios/<matricula>')
@login_required
def usuario_publico(matricula):
    info = UsuarioInfo.query.filter_by(matricula=matricula).first()
    produtos = Produto.query.filter_by(usuario_matricula=matricula).all()

    if not info and not produtos:
        return render_template('perfil.html', usuario=None, telefone='')

    return render_template('perfil.html',
        usuario=_montar_perfil_publico(info, produtos),
        telefone=info.telefone if info else '')
