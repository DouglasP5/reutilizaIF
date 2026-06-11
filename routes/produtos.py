from flask import Blueprint, render_template, request, redirect, url_for, session, jsonify
from models import db, Produto, Avaliacao
from routes import login_required

produtos_bp = Blueprint('produtos', __name__)



def _parse_preco(tipo, preco_str):
    if tipo != 'venda':
        return 0.0, None
    if not preco_str:
        return None, 'Informe o preço para produtos à venda.'
    try:
        return float(preco_str.replace(',', '.')), None
    except ValueError:
        return None, 'Preço inválido. Use somente números.'


def _parse_coordenadas(lat_str, lon_str):
    try:
        return float(lat_str.replace(',', '.')), float(lon_str.replace(',', '.'))
    except (ValueError, AttributeError):
        return None, None


def _dados_form():
    lat, lon = _parse_coordenadas(request.form.get('latitude', ''), request.form.get('longitude', ''))
    return {
        'nome': request.form.get('nome', '').strip(),
        'tipo': request.form.get('tipo', 'venda').strip(),
        'preco_str': request.form.get('preco', '').strip(),
        'descricao': request.form.get('descricao', '').strip(),
        'endereco': request.form.get('endereco', '').strip() or None,
        'lat': lat,
        'lon': lon,
    }


def _aplicar_form_ao_produto(produto, f):
    """Aplica dados do formulário ao objeto Produto. Retorna mensagem de erro ou None."""
    preco, erro = _parse_preco(f['tipo'], f['preco_str'])
    if erro:
        return erro
    produto.nome      = f['nome']
    produto.preco     = preco
    produto.descricao = f['descricao']
    produto.tipo      = f['tipo']
    produto.endereco  = f['endereco']
    produto.latitude  = f['lat']
    produto.longitude = f['lon']
    return None


@produtos_bp.route('/produtos/novo', methods=['GET', 'POST'])
@login_required
def novo_produto():
    if request.method != 'POST':
        return render_template('produto_form.html', produto=None, acao='novo')

    f = _dados_form()
    if not f['nome']:
        return render_template('produto_form.html', error='Informe o nome do produto.', produto=None, acao='novo')

    dados = session.get('dados_usuario', {})
    produto = Produto(
        usuario_nome=dados.get('nome_usual') or dados.get('nome') or 'Usuário',
        usuario_matricula=session.get('matricula'),
    )
    erro = _aplicar_form_ao_produto(produto, f)
    if erro:
        return render_template('produto_form.html', error=erro, produto=None, acao='novo')

    db.session.add(produto)
    db.session.commit()
    return redirect(url_for('produtos.meus_produtos'))


@produtos_bp.route('/meus-produtos')
@login_required
def meus_produtos():
    matricula = session.get('matricula')
    produtos = Produto.query.filter_by(usuario_matricula=matricula).order_by(Produto.created_at.desc()).all()
    ids = [p.id for p in produtos]
    resumo = Avaliacao.resumo_por_produtos(ids)

    produtos_com_avaliacoes = [{
        'produto': p,
        'media_avaliacao': resumo.get(p.id, {}).get('media', 0),
        'total_avaliacoes': resumo.get(p.id, {}).get('total', 0),
    } for p in produtos]

    return render_template('meus_produtos.html',
        produtos_com_avaliacoes=produtos_com_avaliacoes)


@produtos_bp.route('/produtos/<int:produto_id>/editar', methods=['GET', 'POST'])
@login_required
def editar_produto(produto_id):
    produto = Produto.query.get_or_404(produto_id)
    if not produto.pode_ser_modificado_por(session.get('matricula')):
        return redirect(url_for('main.home'))

    if request.method != 'POST':
        return render_template('produto_form.html', produto=produto, acao='editar')

    f = _dados_form()
    if not f['nome']:
        return render_template('produto_form.html', error='Informe o nome do produto.', produto=produto, acao='editar')

    erro = _aplicar_form_ao_produto(produto, f)
    if erro:
        return render_template('produto_form.html', error=erro, produto=produto, acao='editar')

    db.session.commit()
    return redirect(url_for('produtos.meus_produtos'))


@produtos_bp.route('/produtos/<int:produto_id>/excluir', methods=['POST'])
@login_required
def excluir_produto(produto_id):
    produto = Produto.query.get_or_404(produto_id)
    if not produto.pode_ser_modificado_por(session.get('matricula')):
        return redirect(url_for('main.home'))
    db.session.delete(produto)
    db.session.commit()
    return redirect(url_for('produtos.meus_produtos'))


@produtos_bp.route('/venda')
@login_required
def venda():
    produtos = Produto.query.filter_by(tipo='venda', status='disponivel').all()
    return render_template('venda.html', produtos=produtos)


@produtos_bp.route('/troca')
@login_required
def troca():
    produtos = Produto.query.filter_by(tipo='troca', status='disponivel').all()
    return render_template('troca.html', produtos=produtos)


@produtos_bp.route('/produtos/<int:produto_id>/avaliar', methods=['POST'])
@login_required
def avaliar_produto(produto_id):
    produto = Produto.query.get_or_404(produto_id)
    matricula = session.get('matricula')

    if produto.usuario_matricula == matricula:
        return jsonify({'erro': 'Você não pode avaliar seu próprio produto.'}), 403

    nota = request.form.get('nota', type=int)
    if not nota or not (1 <= nota <= 5):
        return jsonify({'erro': 'Nota inválida. Deve ser entre 1 e 5.'}), 400

    comentario = request.form.get('comentario', '').strip()
    avaliacao = Avaliacao.query.filter_by(produto_id=produto_id, avaliador_matricula=matricula).first()

    if avaliacao:
        avaliacao.nota = nota
        avaliacao.comentario = comentario
    else:
        db.session.add(Avaliacao(
            produto_id=produto_id, avaliador_matricula=matricula,
            nota=nota, comentario=comentario,
        ))

    db.session.commit()

    return jsonify({
        'sucesso': True,
        'media': Avaliacao.calcular_media(produto_id),
        'total_avaliacoes': Avaliacao.query.filter_by(produto_id=produto_id).count(),
    })
