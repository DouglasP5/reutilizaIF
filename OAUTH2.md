# 🔐 Autenticação OAuth2 (Login com Google)

## 📌 Contexto

Esta implementação atende à demanda da disciplina de **Projetos Integradores**: adicionar autenticação **OAuth2** como método alternativo de login nos sistemas desenvolvidos no ano anterior.

O sistema já possuía dois métodos de login:
- **Login local** (matrícula + senha cadastrados no sistema)
- **Login via SUAP** (validação contra a API do SUAP no primeiro acesso)

Este documento explica o que foi adicionado: um **terceiro método**, via **OAuth2 com o Google**, usado como a alternativa exigida pela disciplina.

---

## ⚙️ Como funciona

O fluxo segue o padrão **OAuth2 Authorization Code Flow** (com OpenID Connect por cima, para obter o e-mail e o nome do usuário):

1. O usuário clica em **"Entrar com Google"** na tela de login (`/login`).
2. A aplicação redireciona o navegador para a tela de consentimento do Google (`/login/google`).
3. O usuário autoriza o acesso com a própria conta Google.
4. O Google redireciona de volta para a aplicação (`/login/google/callback`) com um código de autorização.
5. A aplicação troca esse código por um token e recupera os dados básicos do usuário (e-mail, nome, foto).
6. O sistema busca um usuário existente com aquele e-mail ou cria um novo automaticamente.
7. A sessão é iniciada normalmente, como nos outros métodos de login — a partir daqui, o usuário navega no sistema sem diferença em relação a quem entrou via login local ou SUAP.

```
Usuário          Reutiliza IF               Google
  |  clica "Entrar com Google"  |                     |
  |----------------------------->|                     |
  |         GET /login/google    |                     |
  |----------------------------->| redirect para consentimento
  |                               |-------------------->|
  |                autoriza                             |
  |----------------------------------------------------->|
  |                               | GET /callback + code |
  |                               |<--------------------|
  |                               | troca code por token  |
  |                               | busca dados do usuário |
  |                               | cria/reaproveita conta |
  |                               | inicia sessão          |
  |<----------------------------- redirect /home           |
```

---

## 🧩 O que foi implementado

| Arquivo | O que mudou |
|---|---|
| `requirements.txt` | Adicionada a lib **Authlib**, responsável por implementar o protocolo OAuth2/OpenID Connect no lado do cliente. |
| `config.py` | Novas variáveis `GOOGLE_CLIENT_ID` e `GOOGLE_CLIENT_SECRET`, lidas do `.env`. |
| `services/oauth_service.py` *(novo)* | Registra o provedor OAuth2 (Google) usando as credenciais da configuração. |
| `app.py` | Inicializa o OAuth (`init_oauth(app)`) junto com o resto da aplicação. |
| `routes/auth.py` | Duas rotas novas: `/login/google` (inicia o fluxo) e `/login/google/callback` (recebe o retorno do Google, cria/loga o usuário). |
| `templates/login.html` | Botão **"Entrar com Google"** na tela de login. |
| `env.example` | Placeholders para as credenciais do Google. |

Nenhum método de login existente foi alterado — o OAuth2 foi adicionado como **opção extra**, sem quebrar o login local nem o login via SUAP.

### Reaproveitamento do usuário

Não foi criada uma tabela nova para usuários OAuth. O e-mail retornado pelo Google é usado como identificador (no campo `matricula` do modelo `UsuarioInfo`), e a mesma função que inicia sessão para login local/SUAP (`AuthService.iniciar_sessao`) é reaproveitada — por isso o restante do sistema (perfil, produtos, permissões) funciona sem nenhuma alteração para usuários que entram via Google.

---

## 🔧 Configuração necessária

Para o botão "Entrar com Google" funcionar, é preciso ter um **Client ID** e **Client Secret** OAuth2 do Google:

### 1️⃣ Criar (ou selecionar) um projeto

1. Acesse [console.cloud.google.com](https://console.cloud.google.com/).
2. No topo da página, clique no seletor de projetos → **Novo Projeto**.
3. Dê um nome (ex: `reutiliza-if`) e clique em **Criar**.
4. Com o projeto criado, garanta que ele esteja selecionado no seletor do topo.

### 2️⃣ Configurar a tela de consentimento OAuth

Antes de criar as credenciais, o Google exige configurar a tela que o usuário vê ao autorizar o login:

1. No menu lateral, vá em **APIs e Serviços → Tela de permissão OAuth** (*OAuth consent screen*).
2. Escolha o tipo **Externo** (External) e clique em **Criar**.
3. Preencha os campos obrigatórios:
   - Nome do app: `Reutiliza IF`
   - E-mail de suporte do usuário: seu e-mail
   - E-mail de contato do desenvolvedor: seu e-mail
4. Na etapa de **Escopos**, adicione `email`, `profile` e `openid` (ou apenas avance — são escopos padrão).
5. Na etapa **Usuários de teste**, clique em **Adicionar usuários** e cadastre o **e-mail do professor** (e o seu, para testar antes).

   > ⚠️ **Importante:** enquanto o app estiver em modo **"Em teste" (Testing)** — o que é o padrão e suficiente para essa entrega — **somente e-mails cadastrados como usuários de teste conseguem fazer login**. Se o e-mail do professor não estiver nessa lista, o Google vai bloquear o acesso com a mensagem "app não verificado" / "acesso negado". Não é necessário publicar o app nem passar por verificação do Google para essa simulação.

6. Salve e finalize.

### 3️⃣ Criar as credenciais OAuth 2.0

1. No menu lateral, vá em **APIs e Serviços → Credenciais** (*Credentials*).
2. Clique em **Criar Credenciais → ID do cliente OAuth** (*OAuth client ID*).
3. Em **Tipo de aplicativo**, escolha **Aplicativo da Web**.
4. Dê um nome (ex: `Reutiliza IF - Web`).
5. Em **URIs de redirecionamento autorizados**, clique em **Adicionar URI** e insira exatamente:
   ```
   http://localhost:5000/login/google/callback
   ```
6. Deixe o campo **Origens JavaScript autorizadas** em branco — não é usado aqui (veja nota abaixo).
7. Clique em **Criar**.

O Google exibirá o **Client ID** e o **Client Secret** em uma janela — copie os dois.

> **Por que não precisa de "Origens JavaScript autorizadas"?** Esse campo só é usado em fluxos onde o próprio JavaScript no navegador chama a API do Google diretamente (ex: Google Identity Services / "Sign In with Google" client-side). Aqui o fluxo é todo *server-side*: o Flask redireciona o navegador para o Google (HTTP 302) e recebe o retorno em `/login/google/callback`; a troca do código por token acontece direto entre o servidor e o Google, sem chamada de JS. Só o **redirect URI** importa.

### 4️⃣ Colocar as credenciais no `.env`

```
GOOGLE_CLIENT_ID=seu-client-id
GOOGLE_CLIENT_SECRET=seu-client-secret
```

Sem essas credenciais, o restante do sistema continua funcionando normalmente — apenas o login via Google não completa a autenticação.

### ❗ Dicas para não travar na hora da entrega

- O redirect URI cadastrado no Google precisa ser **idêntico** ao usado pela aplicação (`http://localhost:5000/login/google/callback`, com essa porta e esse caminho exatos). Qualquer diferença gera o erro `redirect_uri_mismatch`.
- Se o computador do laboratório usar outra porta ou rodar em `127.0.0.1` em vez de `localhost`, cadastre as duas variantes como URIs autorizadas para evitar surpresas.
- Cadastre o e-mail do professor como usuário de teste **com antecedência** — criar a credencial e adicionar o teste user levam poucos minutos, mas não dá para fazer isso durante os 20 minutos cronometrados da simulação.
- Se aparecer o erro `mismatching_state: CSRF Warning!`, a sessão do navegador se perdeu entre a ida e a volta do Google (cookie bloqueado por extensão, aba/host trocado no meio do fluxo, ou duplo clique no botão). Peça para o professor tentar em **uma aba anônima/nova**, acessando `http://localhost:5000/login` diretamente e clicando **uma única vez** em "Entrar com Google", sem usar o botão voltar.
- Certifique-se de que **apenas um processo do servidor** está rodando antes da demonstração (`python app.py` uma única vez). Rodar mais de um ao mesmo tempo pode fazer a aplicação responder com configurações antigas do `.env`.

> As instruções completas de instalação e execução do projeto estão no [README.md](README.md).

---

## ✅ Simulação de entrega

Para a simulação em sala (clonar → preparar ambiente → instalar dependências → executar → autenticação feita pelo professor):

1. Siga os passos 1 a 7 do [README.md](README.md) para clonar, preparar o ambiente virtual, instalar dependências e configurar o `.env` (incluindo as credenciais do Google do passo 6).
2. Rode `python app.py` e acesse `http://localhost:5000/login`.
3. Peça ao professor para clicar em **"Entrar com Google"** e autenticar com a própria conta.
4. Um redirecionamento para `/home` já logado confirma que a autenticação OAuth2 funcionou.
