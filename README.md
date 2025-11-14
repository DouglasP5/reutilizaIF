# PROJETO INTEGRADOR REUTILIZAIF

## Configuração do Banco de Dados

### Programas Necessários

Este projeto utiliza **SQLite**, que é um banco de dados embutido e **não requer instalação de programas adicionais**. O SQLite já vem incluído com Python.

### Dependências Python

As seguintes bibliotecas Python são necessárias:

- **Flask** - Framework web
- **Flask-SQLAlchemy** - ORM para trabalhar com banco de dados

### Passo a Passo para Configuração

#### 1. Instalar Python (se ainda não tiver)

Verifique se o Python está instalado:
```bash
python3 --version
```

Se não estiver instalado, instale o Python 3.8 ou superior.

#### 2. Criar um ambiente virtual (recomendado)

```bash
# No diretório do projeto
python3 -m venv venv

# Ativar o ambiente virtual
# No Linux/Mac:
source venv/bin/activate
# No Windows:
venv\Scripts\activate
```

#### 3. Instalar as dependências

```bash
pip install -r requirements.txt
```

Ou instale manualmente:
```bash
pip install Flask Flask-SQLAlchemy
```

#### 4. Configuração do Banco de Dados

O banco de dados SQLite será criado automaticamente quando você executar a aplicação pela primeira vez. O arquivo `site.db` será gerado no diretório raiz do projeto.

**Configuração atual no `app.py`:**
```python
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
```

#### 5. Executar a aplicação

```bash
python app.py
```

Na primeira execução, o banco de dados será criado automaticamente com a tabela `produto`.

### Estrutura do Banco de Dados

**Tabela: Produto**
- `id` (Integer, Primary Key)
- `nome` (String 100, Not Null)
- `preco` (Float, Not Null)
- `descricao` (String 200)

### Visualizar o Banco de Dados

Para visualizar e gerenciar o banco de dados SQLite, você pode usar:

1. **DB Browser for SQLite** (GUI):
   - Download: https://sqlitebrowser.org/
   - Abra o arquivo `site.db` com este programa

2. **Via linha de comando**:
   ```bash
   sqlite3 site.db
   .tables          # Listar tabelas
   SELECT * FROM produto;  # Ver produtos
   ```

### Alternativa: Usar PostgreSQL ou MySQL

Se preferir usar um banco de dados mais robusto (PostgreSQL ou MySQL), você precisará:

1. **Instalar o banco de dados:**
   - PostgreSQL: https://www.postgresql.org/download/
   - MySQL: https://dev.mysql.com/downloads/

2. **Instalar o driver Python:**
   ```bash
   # Para PostgreSQL
   pip install psycopg2-binary
   
   # Para MySQL
   pip install pymysql
   ```

3. **Alterar a configuração no `app.py`:**
   ```python
   # PostgreSQL
   app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://usuario:senha@localhost/nome_banco'
   
   # MySQL
   app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://usuario:senha@localhost/nome_banco'
   ```

### Comandos Úteis

**Criar o banco de dados manualmente:**
```python
python
>>> from app import app, db
>>> with app.app_context():
...     db.create_all()
```

**Resetar o banco de dados (apagar e recriar):**
```python
python
>>> from app import app, db
>>> with app.app_context():
...     db.drop_all()
...     db.create_all()
```
