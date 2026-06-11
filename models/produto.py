import enum
from . import db


class TipoProduto(str, enum.Enum):
    VENDA = 'venda'
    TROCA = 'troca'


class StatusProduto(str, enum.Enum):
    DISPONIVEL = 'disponivel'
    RESERVADO  = 'reservado'
    CONCLUIDO  = 'concluido'


class Produto(db.Model):
    __tablename__ = 'produto'

    id                = db.Column(db.Integer, primary_key=True)
    nome              = db.Column(db.String(100), nullable=False)
    preco             = db.Column(db.Float, nullable=False)
    descricao         = db.Column(db.String(500))
    usuario_matricula = db.Column(db.String(20))
    usuario_nome      = db.Column(db.String(150))
    tipo              = db.Column(db.String(20), default=TipoProduto.VENDA)
    status            = db.Column(db.String(20), default=StatusProduto.DISPONIVEL)
    endereco          = db.Column(db.String(200))
    latitude          = db.Column(db.Float)
    longitude         = db.Column(db.Float)
    created_at        = db.Column(db.DateTime, server_default=db.func.now())
    updated_at        = db.Column(db.DateTime, server_default=db.func.now(), onupdate=db.func.now())

    tags = db.relationship('Tag', secondary='produto_tags', lazy='subquery',
                           backref=db.backref('produtos', lazy=True))

    usuario_info = db.relationship(
        'UsuarioInfo',
        primaryjoin='Produto.usuario_matricula == UsuarioInfo.matricula',
        foreign_keys='Produto.usuario_matricula',
        lazy='select',
    )

    def __repr__(self):
        return f'<Produto {self.nome}>'

    def pode_ser_modificado_por(self, matricula: str) -> bool:
        from routes import is_admin
        return is_admin() or self.usuario_matricula == matricula
