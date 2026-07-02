# Reutiliza IF

## 📌 Intuito do Projeto

O **Reutiliza IF** é um projeto desenvolvido com o objetivo de incentivar a **economia circular**, o **consumo consciente** e a **reutilização de produtos** dentro do ambiente educacional do Instituto Federal.

A proposta surge a partir da necessidade de reduzir o desperdício de materiais que ainda possuem utilidade, como roupas, calçados, livros, cadernos e outros itens comuns no dia a dia dos estudantes. Muitos desses produtos são descartados ou ficam sem uso, enquanto outros alunos podem precisar deles.

Dessa forma, o Reutiliza IF busca unir **tecnologia, sustentabilidade e colaboração**, promovendo uma cultura mais responsável e consciente entre os estudantes.

---

## 💡 Sobre o Projeto

O Reutiliza IF é uma **plataforma digital com características de e-commerce**, onde os alunos podem:

- Anunciar produtos que desejam **vender ou trocar**
- Visualizar itens disponíveis por outros estudantes
- Facilitar a negociação entre estudantes do IF

A plataforma atua como um ambiente colaborativo, permitindo que produtos sejam reutilizados, prolongando sua vida útil e reduzindo impactos ambientais causados pelo descarte inadequado.

Além do aspecto ambiental, o projeto também gera impacto **social e econômico**, ao estimular a colaboração, a economia e o acesso a produtos reutilizáveis.

---

## 🌱 Temas Relacionados

- Economia circular  
- Sustentabilidade  
- Consumo consciente  
- Economia colaborativa  
- Tecnologia no ambiente educacional  

---

## 🎯 Público-alvo

Estudantes do Instituto Federal interessados em:
- Trocar ou vender produtos
- Economizar
- Praticar o consumo consciente
- Contribuir para a sustentabilidade no ambiente escolar

---

## 👥 Membros do Projeto

Membros antigos: Alexsander Bastos, Allyfh Pontes e Douglas Pierry
Membros novos: Allyfh Pontes, Diego de Andrade, Douglas Pierry, Maria julianne, Ryann Deyv's e Willemberg Lopes

---

## ⚙️ Como Rodar o Projeto

O backend é uma aplicação **Flask (Python)**, com banco de dados **SQLite** por padrão (ou **MySQL**, opcionalmente).

### 1️⃣ Pré-requisitos

Antes de iniciar, certifique-se de ter instalado em sua máquina:

- Git
- Python 3.12+
- (Opcional) MySQL, caso não queira usar o SQLite padrão

### 2️⃣ Clonar o Repositório

Abra o terminal ou prompt de comando e execute:

```bash
git clone https://github.com/seu-usuario/reutiliza-if.git
cd reutiliza-if
```

### 3️⃣ Criar e ativar o ambiente virtual

**Windows (PowerShell):**
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

**Linux/macOS:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### 4️⃣ Instalar as dependências

```bash
pip install -r requirements.txt
```

### 5️⃣ Configurar as variáveis de ambiente

Copie o arquivo de exemplo:

**Windows (PowerShell):**
```powershell
Copy-Item env.example .env
```

**Linux/macOS:**
```bash
cp env.example .env
```

Por padrão, a aplicação usa **SQLite** (`sqlite:///reutilizaif.db`) e não exige configuração adicional. Caso queira usar **MySQL**, defina a variável `DATABASE_URL` no `.env`, por exemplo:

```
DATABASE_URL=mysql+pymysql://root:senha@localhost/reutilizaif
```

### 6️⃣ Configurar login com Google (OAuth2) — opcional

Além do login local, o sistema oferece **"Entrar com Google"** como método alternativo de autenticação (OAuth2). Para habilitá-lo:

1. Acesse o [Google Cloud Console](https://console.cloud.google.com/apis/credentials) e crie uma credencial do tipo **OAuth 2.0 Client ID** (tipo "Aplicativo da Web").
2. Em **URIs de redirecionamento autorizados**, adicione:
   ```
   http://localhost:5000/login/google/callback
   ```
3. Copie o **Client ID** e o **Client Secret** gerados e cole no seu `.env`:
   ```
   GOOGLE_CLIENT_ID=seu-client-id
   GOOGLE_CLIENT_SECRET=seu-client-secret
   ```

Sem essas variáveis configuradas, o restante do sistema (login local, cadastro, etc.) continua funcionando normalmente — apenas o botão "Entrar com Google" não completará a autenticação.

### 7️⃣ Rodar a aplicação

```bash
python app.py
```

As tabelas do banco de dados são criadas automaticamente na primeira execução. A aplicação sobe em modo debug na porta `5000`.

### 8️⃣ Acessar

Abra o navegador em:

```
http://localhost:5000
```
