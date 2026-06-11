from sqlalchemy import func
from . import db


class Avaliacao(db.Model):
    __tablename__ = 'avaliacao'

    id = db.Column(db.Integer, primary_key=True)
    produto_id = db.Column(db.Integer, db.ForeignKey('produto.id'), nullable=False)
    avaliador_matricula = db.Column(db.String(20), nullable=False)
    nota = db.Column(db.Integer, nullable=False)
    comentario = db.Column(db.String(500))
    created_at = db.Column(db.DateTime, server_default=db.func.now())

    produto = db.relationship('Produto', backref='avaliacoes')

    def __repr__(self):
        return f'<Avaliacao {self.nota} estrelas para produto {self.produto_id}>'

    @staticmethod
    def resumo_por_produtos(produto_ids):
        if not produto_ids:
            return {}
        data = db.session.query(
            Avaliacao.produto_id,
            func.count(Avaliacao.id).label('total'),
            func.avg(Avaliacao.nota).label('media')
        ).filter(Avaliacao.produto_id.in_(produto_ids)).group_by(Avaliacao.produto_id).all()
        return {pid: {'total': total, 'media': round(float(media), 1)} for pid, total, media in data}

    @staticmethod
    def enriquecer_produtos(produtos):
        ids = [p.id for p in produtos]
        resumo = Avaliacao.resumo_por_produtos(ids)
        return [
            {
                'produto': p,
                'media_avaliacao': resumo.get(p.id, {}).get('media', 0),
                'total_avaliacoes': resumo.get(p.id, {}).get('total', 0),
            }
            for p in produtos
        ]

    @staticmethod
    def calcular_media(produto_id):
        resultado = db.session.query(
            func.avg(Avaliacao.nota)
        ).filter_by(produto_id=produto_id).scalar()
        return round(float(resultado), 1) if resultado else 0.0
