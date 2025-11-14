from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy



app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

class Produto(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    preco = db.Column(db.Float, nullable=False)
    descricao = db.Column(db.String(200))

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        senha = request.form.get('senha')
        
        # Aqui você pode adicionar a lógica de autenticação
        # Por enquanto, apenas redireciona para a home
        # Exemplo básico: verificar se email e senha foram fornecidos
        if email and senha:
            # Lógica de autenticação aqui
            return redirect(url_for('home'))
        else:
            return render_template('login.html', error='Por favor, preencha todos os campos')
    
    return render_template('login.html')

@app.route('/cadastro-usuario')
def cadastro_usuario():
    # Por enquanto, redireciona para login
    # Você pode criar uma página de cadastro de usuário depois
    return redirect(url_for('login'))

@app.route('/home')
def home():
    produtos = Produto.query.all()
    return render_template('home.html', produtos=produtos)

@app.route('/cadastro-produto')
def exibir_formulario():
    return render_template('cadastro.html')

@app.route('/cadastrar', methods=['POST'])
def cadastrar_produto():
    nome = request.form['nome']
    preco = request.form['preco']
    descricao = request.form['descricao']

    novo_produto = Produto(nome=nome, preco=preco, descricao=descricao)
    db.session.add(novo_produto)
    db.session.commit()

    return redirect(url_for('home'))
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)


