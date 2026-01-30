from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Produto(db.Model):
    __tablename__ = 'produto'
    
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    preco = db.Column(db.Float, nullable=False)
    descricao = db.Column(db.String(500))
    usuario_matricula = db.Column(db.String(20))
    usuario_nome = db.Column(db.String(150))
    tipo = db.Column(db.String(20), default='venda')
    status = db.Column(db.String(20), default='disponivel')
    endereco = db.Column(db.String(200))
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    updated_at = db.Column(db.DateTime, server_default=db.func.now(), onupdate=db.func.now())

    def __repr__(self):
        return f'<Produto {self.nome}>'

    def to_dict(self):
        return {
            'id': self.id,
            'nome': self.nome,
            'preco': self.preco,
            'descricao': self.descricao,
            'usuario_matricula': self.usuario_matricula,
            'usuario_nome': self.usuario_nome,
            'tipo': self.tipo,
            'status': self.status
        }


class UsuarioInfo(db.Model):
    __tablename__ = 'usuario_info'
    
    id = db.Column(db.Integer, primary_key=True)
    matricula = db.Column(db.String(20), unique=True, nullable=False, index=True)
    telefone = db.Column(db.String(30))
    nome = db.Column(db.String(150))
    curso = db.Column(db.String(150))
    campus = db.Column(db.String(150))
    foto_url = db.Column(db.String(300))
    senha_hash = db.Column(db.String(255))
    jwt_token = db.Column(db.Text)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    updated_at = db.Column(db.DateTime, server_default=db.func.now(), onupdate=db.func.now())

    def __repr__(self):
        return f'<UsuarioInfo {self.matricula}>'


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
    def calcular_media(produto_id):
        """Calcula a média de avaliações de um produto"""
        avaliacoes = Avaliacao.query.filter_by(produto_id=produto_id).all()
        if not avaliacoes:
            return 0.0
        total = sum(av.nota for av in avaliacoes)
        return round(total / len(avaliacoes), 1)

