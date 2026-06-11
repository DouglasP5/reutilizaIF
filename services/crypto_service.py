import hashlib
from abc import ABC, abstractmethod


class HashStrategy(ABC):
    @abstractmethod
    def hash(self, senha: str) -> str: ...

    @abstractmethod
    def verificar(self, senha: str, hash_armazenado: str) -> bool: ...


class MD5Strategy(HashStrategy):
    def hash(self, senha: str) -> str:
        return hashlib.md5(senha.encode('utf-8')).hexdigest()

    def verificar(self, senha: str, hash_armazenado: str) -> bool:
        return self.hash(senha) == hash_armazenado


_strategy: HashStrategy = MD5Strategy()


def hash_senha(senha: str) -> str:
    return _strategy.hash(senha)


def verificar_senha(senha: str, hash_armazenado: str) -> bool:
    return _strategy.verificar(senha, hash_armazenado)
