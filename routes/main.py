from flask import Blueprint, render_template
from sqlalchemy import func
from models import db, Produto, UsuarioInfo, Avaliacao
from routes import login_required

main_bp = Blueprint('main', __name__)


@main_bp.route('/')
def index():
    try:
        total_usuarios = db.session.query(func.count(UsuarioInfo.id)).scalar() or 0
        total_produtos = db.session.query(func.count(Produto.id)).scalar() or 0
        stats = db.session.query(Produto.tipo, func.count(Produto.id)).filter_by(
            status='disponivel').group_by(Produto.tipo).all()
        contagem = dict(stats)
    except Exception:
        total_usuarios = total_produtos = 0
        contagem = {}

    return render_template('index.html',
        total_usuarios=total_usuarios,
        total_produtos=total_produtos,
        produtos_venda=contagem.get('venda', 0),
        produtos_troca=contagem.get('troca', 0))


@main_bp.route('/home')
@login_required
def home():
    produtos = Produto.query.filter_by(status='disponivel').all()
    ids = [p.id for p in produtos]
    resumo = Avaliacao.resumo_por_produtos(ids)

    produtos_com_avaliacoes = [{
        'produto': p,
        'media_avaliacao': resumo.get(p.id, {}).get('media', 0),
        'total_avaliacoes': resumo.get(p.id, {}).get('total', 0),
    } for p in produtos]

    return render_template('home.html',
        produtos=produtos,
        produtos_com_avaliacoes=produtos_com_avaliacoes,
        produtos_mapa=[p for p in produtos if p.latitude and p.longitude],
        pode_criar=True)
