from flask import Blueprint, request, jsonify, session
from models import db, Tag, Produto, UsuarioInfo
from models.tag import _gerar_slug
from routes import login_required, admin_required

tags_bp = Blueprint('tags', __name__)


# ── CRUD de tags (admin only) ─────────────────────────────────────────────────

@tags_bp.route('/admin/tags', methods=['GET'])
@login_required
@admin_required
def listar_tags():
    tags = Tag.query.order_by(Tag.nome).all()
    return jsonify([{'id': t.id, 'nome': t.nome, 'slug': t.slug, 'cor': t.cor} for t in tags])


@tags_bp.route('/admin/tags', methods=['POST'])
@login_required
@admin_required
def criar_tag():
    data = request.get_json(silent=True) or {}
    nome = (data.get('nome') or '').strip()
    if not nome:
        return jsonify({'erro': 'O campo nome é obrigatório.'}), 400

    if Tag.query.filter_by(slug=_gerar_slug(nome)).first():
        return jsonify({'erro': 'Já existe uma tag com esse nome.'}), 409

    tag = Tag.criar(nome, cor=data.get('cor', '#6c757d'))
    db.session.commit()
    return jsonify({'id': tag.id, 'nome': tag.nome, 'slug': tag.slug, 'cor': tag.cor}), 201


@tags_bp.route('/admin/tags/<int:tag_id>', methods=['PATCH'])
@login_required
@admin_required
def atualizar_tag(tag_id):
    tag = Tag.query.get_or_404(tag_id)
    data = request.get_json(silent=True) or {}

    novo_nome = (data.get('nome') or '').strip()
    if novo_nome and novo_nome != tag.nome:
        novo_slug = _gerar_slug(novo_nome)
        if Tag.query.filter(Tag.id != tag_id, Tag.slug == novo_slug).first():
            return jsonify({'erro': 'Já existe uma tag com esse nome.'}), 409
        tag.nome = novo_nome
        tag.slug = novo_slug

    if 'cor' in data and data['cor']:
        tag.cor = data['cor']

    db.session.commit()
    return jsonify({'id': tag.id, 'nome': tag.nome, 'slug': tag.slug, 'cor': tag.cor})


@tags_bp.route('/admin/tags/<int:tag_id>', methods=['DELETE'])
@login_required
@admin_required
def excluir_tag(tag_id):
    tag = Tag.query.get_or_404(tag_id)
    db.session.delete(tag)
    db.session.commit()
    return '', 204


# ── Aplicar / remover tags em produtos (dono ou admin) ───────────────────────

@tags_bp.route('/produtos/<int:produto_id>/tags', methods=['POST'])
@login_required
def aplicar_tag(produto_id):
    produto = Produto.query.get_or_404(produto_id)
    if not produto.pode_ser_modificado_por(session.get('matricula')):
        return jsonify({'erro': 'Sem permissão para modificar este produto.'}), 403

    data = request.get_json(silent=True) or {}
    tag_id = data.get('tag_id')
    if not tag_id:
        return jsonify({'erro': 'tag_id é obrigatório.'}), 400

    tag = Tag.query.get_or_404(tag_id)
    if tag not in produto.tags:
        produto.tags.append(tag)
        db.session.commit()

    return jsonify({'sucesso': True, 'tag': {'id': tag.id, 'nome': tag.nome, 'cor': tag.cor}})


@tags_bp.route('/produtos/<int:produto_id>/tags/<int:tag_id>', methods=['DELETE'])
@login_required
def remover_tag(produto_id, tag_id):
    produto = Produto.query.get_or_404(produto_id)
    if not produto.pode_ser_modificado_por(session.get('matricula')):
        return jsonify({'erro': 'Sem permissão para modificar este produto.'}), 403

    tag = Tag.query.get_or_404(tag_id)
    if tag in produto.tags:
        produto.tags.remove(tag)
        db.session.commit()

    return '', 204


# ── Promoção / rebaixamento de admin ─────────────────────────────────────────

@tags_bp.route('/admin/usuarios/<matricula>/promover', methods=['POST'])
@login_required
@admin_required
def promover_admin(matricula):
    usuario = UsuarioInfo.query.filter_by(matricula=matricula).first_or_404()
    usuario.is_admin = True
    db.session.commit()
    return jsonify({'sucesso': True, 'matricula': matricula, 'is_admin': True})


@tags_bp.route('/admin/usuarios/<matricula>/rebaixar', methods=['POST'])
@login_required
@admin_required
def rebaixar_admin(matricula):
    if matricula == session.get('matricula'):
        return jsonify({'erro': 'Você não pode rebaixar a si mesmo.'}), 403

    usuario = UsuarioInfo.query.filter_by(matricula=matricula).first_or_404()
    usuario.is_admin = False
    db.session.commit()
    return jsonify({'sucesso': True, 'matricula': matricula, 'is_admin': False})
