from flask import Blueprint, render_template, redirect, url_for, session
from models import Produto, UsuarioInfo, Avaliacao, db
from config import Config
from sqlalchemy import func

main_bp = Blueprint('main', __name__)

def usuario_e_admin():
    return session.get('matricula') in Config.ADMIN_MATRICULAS

@main_bp.route('/')
def index():
    try:
        total_usuarios = db.session.query(func.count(UsuarioInfo.id)).scalar() or 0
        total_produtos = db.session.query(func.count(Produto.id)).scalar() or 0
        
        produtos_stats = db.session.query(
            Produto.tipo,
            func.count(Produto.id)
        ).filter_by(status='disponivel').group_by(Produto.tipo).all()
        
        produtos_venda = 0
        produtos_troca = 0
        for tipo, count in produtos_stats:
            if tipo == 'venda':
                produtos_venda = count
            elif tipo == 'troca':
                produtos_troca = count
    except Exception as e:
        total_usuarios = 0
        total_produtos = 0
        produtos_venda = 0
        produtos_troca = 0
    
    return render_template(
        'index.html',
        total_usuarios=total_usuarios,
        total_produtos=total_produtos,
        produtos_venda=produtos_venda,
        produtos_troca=produtos_troca
    )

@main_bp.route('/home')
def home():
    if not session.get('usuario_logado'):
        return redirect(url_for('auth.login'))
    
    produtos = Produto.query.filter_by(status='disponivel').all()
    dados_usuario = session.get('dados_usuario', {})
    
    produtos_com_localizacao = [p for p in produtos if p.latitude and p.longitude]
    
    produto_ids = [p.id for p in produtos]
    
    if produto_ids:
        avaliacoes_data = db.session.query(
            Avaliacao.produto_id,
            func.count(Avaliacao.id).label('total'),
            func.avg(Avaliacao.nota).label('media')
        ).filter(Avaliacao.produto_id.in_(produto_ids)).group_by(Avaliacao.produto_id).all()
        
        avaliacoes_dict = {prod_id: {'total': total, 'media': round(float(media), 1)} 
                          for prod_id, total, media in avaliacoes_data}
    else:
        avaliacoes_dict = {}
    
    produtos_com_avaliacoes = []
    for produto in produtos:
        aval_info = avaliacoes_dict.get(produto.id, {'total': 0, 'media': 0})
        produtos_com_avaliacoes.append({
            'produto': produto,
            'media_avaliacao': aval_info['media'],
            'total_avaliacoes': aval_info['total']
        })
    
    return render_template(
        'home.html',
        produtos=produtos,
        produtos_com_avaliacoes=produtos_com_avaliacoes,
        produtos_mapa=produtos_com_localizacao,
        usuario=dados_usuario,
        is_admin=usuario_e_admin(),
        pode_criar=session.get('usuario_logado', False)
    )

