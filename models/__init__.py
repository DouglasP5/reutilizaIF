from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

from .usuario import UsuarioInfo, _extrair_nome
from .tag import Tag, produto_tags
from .produto import Produto, TipoProduto, StatusProduto
from .avaliacao import Avaliacao

__all__ = ['db', 'UsuarioInfo', '_extrair_nome', 'Tag', 'produto_tags', 'Produto', 'TipoProduto', 'StatusProduto', 'Avaliacao']
