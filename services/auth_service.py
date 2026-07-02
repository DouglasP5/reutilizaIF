from flask import session
from models import db, UsuarioInfo
from services.crypto_service import verificar_senha, hash_senha


class AuthService:
    @staticmethod
    def login_local(matricula, senha) -> dict:
        """{'sucesso': bool, 'usuario': UsuarioInfo|None, 'erro': str|None}"""
        usuario = UsuarioInfo.query.filter_by(matricula=matricula).first()
        if not usuario or not usuario.senha_hash:
            return {'sucesso': False, 'usuario': None, 'erro': None}
        if not verificar_senha(senha, usuario.senha_hash):
            return {'sucesso': False, 'usuario': None, 'erro': 'Senha incorreta.'}
        return {'sucesso': True, 'usuario': usuario, 'erro': None}

    @staticmethod
    def cadastrar_local(nome, matricula, senha, curso=None) -> dict:
        """Cria uma conta nova diretamente (sem validar contra o SUAP).

        {'sucesso': bool, 'usuario': UsuarioInfo|None, 'erro': str|None}
        """
        usuario = UsuarioInfo.query.filter_by(matricula=matricula).first()
        if usuario and usuario.senha_hash:
            return {'sucesso': False, 'usuario': None, 'erro': 'Matrícula já cadastrada. Faça login.'}

        usuario = usuario or UsuarioInfo(matricula=matricula)
        usuario.nome = nome
        if curso:
            usuario.curso = curso
        usuario.senha_hash = hash_senha(senha)
        db.session.add(usuario)
        db.session.commit()
        return {'sucesso': True, 'usuario': usuario, 'erro': None}

    @staticmethod
    def registrar(matricula, senha, token, dados_suap) -> UsuarioInfo:
        """Cria/atualiza usuário com hash de senha e token."""
        usuario = UsuarioInfo.obter_ou_criar(matricula)
        usuario.atualizar_dados_suap(dados_suap)
        usuario.jwt_token = token
        usuario.senha_hash = hash_senha(senha)
        db.session.commit()
        return usuario

    @staticmethod
    def iniciar_sessao(usuario: UsuarioInfo, token=None):
        """Popula session com dados do usuário, incluindo is_admin."""
        session['usuario_logado'] = True
        session['matricula'] = usuario.matricula
        session['is_admin'] = usuario.is_admin
        session['dados_usuario'] = {
            'nome_usual': usuario.nome,
            'nome': usuario.nome,
            'matricula': usuario.matricula,
        }
        if token:
            session['token'] = token
