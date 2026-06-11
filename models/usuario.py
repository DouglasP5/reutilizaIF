from . import db


def _extrair_nome(dados: dict) -> str | None:
    return (
        dados.get('nome_usual') or dados.get('nome_social') or
        dados.get('nome') or dados.get('nome_registro') or
        f"{dados.get('primeiro_nome', '')} {dados.get('ultimo_nome', '')}".strip() or None
    )


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
    jwt_token  = db.Column(db.Text)
    is_admin   = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    updated_at = db.Column(db.DateTime, server_default=db.func.now(), onupdate=db.func.now())

    def __repr__(self):
        return f'<UsuarioInfo {self.matricula}>'

    @classmethod
    def obter_ou_criar(cls, matricula):
        usuario = cls.query.filter_by(matricula=matricula).first()
        if not usuario:
            usuario = cls(matricula=matricula)
            db.session.add(usuario)
        return usuario

    def atualizar_dados_suap(self, dados):
        nome = _extrair_nome(dados)
        if nome:
            self.nome = nome

        vinculo = dados.get('vinculo') or {}
        if isinstance(vinculo, dict):
            curso = vinculo.get('curso')
            if isinstance(curso, dict):
                curso = curso.get('nome')
            campus = vinculo.get('campus')
            if isinstance(campus, dict):
                campus = campus.get('nome')
            if curso:
                self.curso = curso
            if campus:
                self.campus = campus

        foto = (dados.get('url_foto_150x200') or dados.get('url_foto_75x100') or dados.get('foto'))
        if foto:
            self.foto_url = foto
