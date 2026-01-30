from flask import Blueprint, render_template, request, redirect, url_for, session, jsonify
from models import db, Produto, Avaliacao
from config import Config
from sqlalchemy import func

produtos_bp = Blueprint('produtos', __name__)

def usuario_e_admin():
    return session.get('matricula') in Config.ADMIN_MATRICULAS

@produtos_bp.route('/produtos/novo', methods=['GET', 'POST'])
def novo_produto():
    if not session.get('usuario_logado'):
        return redirect(url_for('auth.login'))

    if request.method == 'POST':
        nome = request.form.get('nome', '').strip()
        preco = request.form.get('preco', '').strip()
        descricao = request.form.get('descricao', '').strip()
        tipo = request.form.get('tipo', 'venda').strip()
        endereco = request.form.get('endereco', '').strip()
        latitude = request.form.get('latitude', '').strip()
        longitude = request.form.get('longitude', '').strip()

        if not nome:
            return render_template('produto_form.html', error='Informe o nome do produto.', produto=None, acao='novo')

        preco_valor = 0.0
        if tipo == 'venda':
            if not preco:
                return render_template('produto_form.html', error='Informe o preço para produtos à venda.', produto=None, acao='novo')
            try:
                preco_valor = float(str(preco).replace(',', '.'))
            except ValueError:
                return render_template('produto_form.html', error='Preço inválido. Use somente números.', produto=None, acao='novo')

        lat_val = None
        lon_val = None
        if latitude and longitude:
            try:
                lat_val = float(latitude.replace(',', '.'))
                lon_val = float(longitude.replace(',', '.'))
            except ValueError:
                pass

        dados_usuario = session.get('dados_usuario', {})
        nome_usuario = dados_usuario.get('nome_usual') or dados_usuario.get('nome') or 'Usuário'
        matricula_usuario = session.get('matricula')

        produto = Produto(
            nome=nome,
            preco=preco_valor,
            descricao=descricao,
            usuario_nome=nome_usuario,
            usuario_matricula=matricula_usuario,
            tipo=tipo,
            endereco=endereco if endereco else None,
            latitude=lat_val,
            longitude=lon_val
        )
        db.session.add(produto)
        db.session.commit()
        return redirect(url_for('produtos.meus_produtos'))

    return render_template('produto_form.html', produto=None, acao='novo')


@produtos_bp.route('/meus-produtos')
def meus_produtos():
    if not session.get('usuario_logado'):
        return redirect(url_for('auth.login'))
    
    matricula = session.get('matricula')
    produtos = Produto.query.filter_by(usuario_matricula=matricula).order_by(Produto.created_at.desc()).all()
    
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
    
    dados_usuario = session.get('dados_usuario', {})
    return render_template(
        'meus_produtos.html',
        produtos_com_avaliacoes=produtos_com_avaliacoes,
        usuario=dados_usuario,
        is_admin=usuario_e_admin()
    )


@produtos_bp.route('/produtos/<int:produto_id>/editar', methods=['GET', 'POST'])
def editar_produto(produto_id):
    if not session.get('usuario_logado'):
        return redirect(url_for('auth.login'))
    
    produto = Produto.query.get_or_404(produto_id)
    matricula = session.get('matricula')
    
    if not usuario_e_admin() and produto.usuario_matricula != matricula:
        return redirect(url_for('main.home'))

    if request.method == 'POST':
        nome = request.form.get('nome', '').strip()
        preco = request.form.get('preco', '').strip()
        descricao = request.form.get('descricao', '').strip()
        tipo = request.form.get('tipo', 'venda').strip()
        endereco = request.form.get('endereco', '').strip()
        latitude = request.form.get('latitude', '').strip()
        longitude = request.form.get('longitude', '').strip()

        if not nome:
            return render_template('produto_form.html', error='Informe o nome do produto.', produto=produto, acao='editar')

        if tipo == 'venda':
            if not preco:
                return render_template('produto_form.html', error='Informe o preço para produtos à venda.', produto=produto, acao='editar')
            try:
                preco_valor = float(str(preco).replace(',', '.'))
            except ValueError:
                return render_template('produto_form.html', error='Preço inválido. Use somente números.', produto=produto, acao='editar')
        else:
            preco_valor = 0.0

        lat_val = None
        lon_val = None
        if latitude and longitude:
            try:
                lat_val = float(latitude.replace(',', '.'))
                lon_val = float(longitude.replace(',', '.'))
            except ValueError:
                pass

        produto.nome = nome
        produto.preco = preco_valor
        produto.descricao = descricao
        produto.tipo = tipo
        produto.endereco = endereco if endereco else None
        produto.latitude = lat_val
        produto.longitude = lon_val
        db.session.commit()
        return redirect(url_for('produtos.meus_produtos'))

    return render_template('produto_form.html', produto=produto, acao='editar')


@produtos_bp.route('/produtos/<int:produto_id>/excluir', methods=['POST'])
def excluir_produto(produto_id):
    if not session.get('usuario_logado'):
        return redirect(url_for('auth.login'))
    
    produto = Produto.query.get_or_404(produto_id)
    matricula = session.get('matricula')
    
    if not usuario_e_admin() and produto.usuario_matricula != matricula:
        return redirect(url_for('main.home'))

    db.session.delete(produto)
    db.session.commit()
    return redirect(url_for('produtos.meus_produtos'))


@produtos_bp.route('/venda')
def venda():
    if not session.get('usuario_logado'):
        return redirect(url_for('auth.login'))
    
    produtos = Produto.query.filter_by(tipo='venda', status='disponivel').all()
    dados_usuario = session.get('dados_usuario', {})
    return render_template(
        'venda.html',
        produtos=produtos,
        usuario=dados_usuario,
        is_admin=usuario_e_admin()
    )


@produtos_bp.route('/troca')
def troca():
    if not session.get('usuario_logado'):
        return redirect(url_for('auth.login'))
    
    produtos = Produto.query.filter_by(tipo='troca', status='disponivel').all()
    dados_usuario = session.get('dados_usuario', {})
    return render_template(
        'troca.html',
        produtos=produtos,
        usuario=dados_usuario,
        is_admin=usuario_e_admin()
    )


@produtos_bp.route('/produtos/<int:produto_id>/avaliar', methods=['POST'])
def avaliar_produto(produto_id):
    if not session.get('usuario_logado'):
        return jsonify({'erro': 'Usuário não autenticado'}), 401
    
    produto = Produto.query.get_or_404(produto_id)
    matricula = session.get('matricula')
    
    if not matricula:
        return jsonify({'erro': 'Usuário não identificado'}), 401
    
    avaliacao_existente = Avaliacao.query.filter_by(
        produto_id=produto_id,
        avaliador_matricula=matricula
    ).first()
    
    nota = request.form.get('nota', type=int)
    comentario = request.form.get('comentario', '').strip()
    
    if not nota or nota < 1 or nota > 5:
        return jsonify({'erro': 'Nota inválida. Deve ser entre 1 e 5.'}), 400
    
    if avaliacao_existente:
        avaliacao_existente.nota = nota
        avaliacao_existente.comentario = comentario
    else:
        avaliacao = Avaliacao(
            produto_id=produto_id,
            avaliador_matricula=matricula,
            nota=nota,
            comentario=comentario
        )
        db.session.add(avaliacao)
    
    db.session.commit()
    
    total_avaliacoes = Avaliacao.query.filter_by(produto_id=produto_id).count()
    soma_notas = sum(av.nota for av in Avaliacao.query.filter_by(produto_id=produto_id).all())
    media = round(soma_notas / total_avaliacoes, 1) if total_avaliacoes > 0 else 0
    
    return jsonify({
        'sucesso': True,
        'media': media,
        'total_avaliacoes': total_avaliacoes
    })

