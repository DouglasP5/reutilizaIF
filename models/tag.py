import unicodedata
import re
from . import db

produto_tags = db.Table(
    'produto_tags',
    db.Column('produto_id', db.Integer, db.ForeignKey('produto.id', ondelete='CASCADE'), primary_key=True),
    db.Column('tag_id',     db.Integer, db.ForeignKey('tag.id',     ondelete='CASCADE'), primary_key=True),
)


def _gerar_slug(nome: str) -> str:
    normalizado = unicodedata.normalize('NFKD', nome).encode('ascii', 'ignore').decode('ascii')
    return re.sub(r'[^a-z0-9]+', '-', normalizado.lower()).strip('-')


class Tag(db.Model):
    __tablename__ = 'tag'

    id   = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(50), unique=True, nullable=False)
    slug = db.Column(db.String(50), unique=True, nullable=False)
    cor  = db.Column(db.String(7), default='#6c757d')

    def __repr__(self):
        return f'<Tag {self.nome}>'

    @classmethod
    def criar(cls, nome: str, cor: str = '#6c757d') -> 'Tag':
        tag = cls(nome=nome.strip(), slug=_gerar_slug(nome), cor=cor)
        db.session.add(tag)
        return tag
