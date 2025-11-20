## Resumo rápido

Este repositório é uma aplicação Flask simples que oferece um pequeno mercado para estudantes do IFRN. O ponto de entrada principal é `app.py` — a maior parte da lógica do servidor, modelos e integrações ficam ali.

**Arquivos-chave**
- `app.py`: aplicação Flask, modelos `Produto` e `UsuarioInfo`, autenticação via SUAP, rotas e lógica de CRUD.
- `requirements.txt`: dependências — atualmente `Flask==3.0.0`, `Flask-SQLAlchemy`, `requests`.
- `init_db.py`: script para criar o banco (`site.db`) via `db.create_all()`.
- `templates/` e `static/`: views e recursos estáticos (HTML, imagens).
- `iniciar.sh`: script local útil para desenvolvimento (ativa venv e roda `python app.py`).

## Arquitetura / fluxo principal

- Monolito simples (único módulo `app.py`) — não há serviços separados. Tudo (modelos, rotas, integração com SUAP) está no mesmo arquivo.
- Banco: SQLite por padrão (`sqlite:///site.db`). `db.create_all()` é chamado na inicialização.
- Autenticação: usa o SUAP via chamadas HTTP (`requests`) e armazena `token` + `dados_usuario` na `session` do Flask.
- Sessão: chaves usadas são `session['usuario_logado']`, `session['matricula']`, `session['dados_usuario']`, `session['token']`.
- Admin: `ADMIN_MATRICULAS` (set) define usuários com privilégios de edição e exclusão.

## Convenções específicas do projeto

- Rotas REST/HTML: usam padrões simples de CRUD, por exemplo:
  - Criar produto: `POST /produtos/novo`
  - Editar: `POST /produtos/<int:produto_id>/editar`
  - Excluir: `POST /produtos/<int:produto_id>/excluir`
  - Perfil público: `GET /usuarios/<matricula>`
- Modelos: `Produto` tem campos `usuario_matricula` e `usuario_nome` — ao criar produtos, o app popula esses campos a partir da `session`.
- Migração de esquema: `ensure_schema()` em `app.py` adiciona colunas ausentes com `ALTER TABLE` (SQLite). Ao modificar modelos, atualize `ensure_schema()` apropriadamente.

## Integrações externas e pontos sensíveis

- SUAP API: URL base definida em `SUAP_API_BASE_URL = "https://suap.ifrn.edu.br/api/v2"`.
  - Tenha cuidado: há vários endpoints tentados na função `autenticar_suap()` (payload `data` vs `json`).
  - Requests usam `timeout=10` — mantenha esse timeout em chamadas externas para evitar travar o servidor.
- Evite logar tokens completos em produção. Atualmente o app imprime alguns debug logs durante autenticação.

## Compatibilidade Flask 2.x / 3.x

- O repositório foi atualizado para suportar Flask 3.x. Para compatibilidade, `app.py` usa um mapeamento condicional para chamar a função de inicialização correta:
  - `app.before_serving` (Flask 3.x) ou `app.before_first_request` (Flask 2.x).
- Se for fazer mudanças que dependam do ciclo de vida do servidor, siga o padrão condicional já presente.

## Comandos úteis (desenvolvimento)

1. Criar e ativar venv (Linux):
```bash
python3 -m venv venv
source venv/bin/activate
```
2. Instalar dependências:
```bash
pip install -r requirements.txt
```
3. Inicializar banco (opções):
```bash
# script dedicado
python init_db.py

# ou diretamente
python -c "from app import app, db; import sys
with app.app_context():
    db.create_all(); print('ok')"
```
4. Rodar servidor (dev):
```bash
python app.py
# ou usar iniciar.sh (ajuste caminho se necessário)
./iniciar.sh
```

## Boas práticas específicas aqui

- Não altere `app.config['SQLALCHEMY_DATABASE_URI']` sem documentar (muda a localização do `site.db`).
- Ao alterar modelos, mantenha `ensure_schema()` sincronizado — o projeto não usa migrations automáticas (Alembic).
- Evite remover prints de debug nas funções de autenticação sem substituir por logs controlados (o debug auxilia em entender respostas do SUAP).
- Para deploy em produção, remova `app.run(debug=True)` e use um servidor WSGI (Gunicorn/uvicorn) — documente o comando de deploy em PRs.

## Padrões de PR / alterações que o Copilot deve sugerir

- Prefira mudanças pequenas e focadas (ex.: separar lógica SUAP para uma função/module próprio antes de grandes refactors).
- Se sugerir mudança de dependência (ex.: Flask 2.x → 3.x), indique impacto no ciclo de vida do app (`before_serving` vs `before_first_request`).
- Ao propor alterações de DB, inclua um plano de migração (ex.: atualização de `ensure_schema()` ou adicionar um script `migrate.py`).

## Onde procurar exemplos no código

- Uso da sessão e autenticação: veja `login()` em `app.py`.
- Lógica de criação/edição de produto: `novo_produto()` e `editar_produto()`.
- Migração/ajuste de colunas: `ensure_schema()`.

Se algo estiver pouco claro ou você quiser que eu escreva um script de migração/ALEMBIC, diga e eu gero um rascunho.

---
Por favor revise: quer que eu também rode os testes manuais (`python app.py`) agora, ou prefere executar localmente depois de revisar o arquivo?
