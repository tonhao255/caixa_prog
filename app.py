# =====================================================================
# SEÇÃO 1: IMPORTAÇÕES ESSENCIAIS
# Todas as bibliotecas necessárias para o projeto são importadas aqui.
# =====================================================================
from flask import Flask, render_template, request, redirect, url_for, session, flash, Blueprint
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash
import mysql.connector

# =====================================================================
# SEÇÃO 2: CONFIGURAÇÃO INICIAL DO APLICATIVO
# Configurações essenciais para a aplicação Flask e a conexão com o banco de dados.
# =====================================================================

# Cria a instância principal da aplicação Flask.
app = Flask(__name__)

# Define uma chave secreta para a aplicação, usada para proteger as sessões dos usuários.
# Em um ambiente de produção, esta chave deve ser mais complexa e mantida em segredo.
app.secret_key = 'chave-secreta-muito-segura-para-seu-projeto'

# Dicionário com as credenciais de acesso ao banco de dados MySQL.
db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': '',
    'database': 'caixa_prog'  # Nome do banco de dados utilizado.
}

# =====================================================================
# SEÇÃO 3: DECORADOR DE AUTENTICAÇÃO DE ADMIN
# Garante que apenas usuários administradores logados possam acessar certas rotas.
# =====================================================================
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # 1. Verifica se 'usuario_id' não está na sessão, o que indica que o usuário não está logado.
        if 'usuario_id' not in session:
            flash("Você precisa fazer login para acessar esta página.", "erro")
            return redirect(url_for('login'))
        
        # 2. Verifica se o tipo de usuário na sessão não é '1' (que representa o administrador).
        if session.get('tipo_usuario') != 1:
            flash("Acesso negado. Você não tem permissão para acessar esta página.", "erro")
            # Redireciona para a página inicial se o usuário não for administrador.
            return redirect(url_for('home'))
        
        # 3. Se todas as verificações passarem, a função original (a rota) é executada.
        return f(*args, **kwargs)
    return decorated_function

# =====================================================================
# SEÇÃO 4: ROTAS PRINCIPAIS E DE AUTENTICAÇÃO
# Controlam o acesso, login, cadastro e logout dos usuários.
# =====================================================================

@app.route('/')
def home():
    """ Rota principal. Redireciona o usuário com base no seu status de login. """
    if 'usuario_id' in session:
        # Se for administrador, vai para o dashboard.
        if session.get('tipo_usuario') == 1:
            return redirect(url_for('admin.dashboard'))
        # Se for um usuário comum, é deslogado, pois não tem acesso ao painel.
        flash("Sua conta não tem permissão de acesso ao painel.", "info")
        return redirect(url_for('logout'))
    # Se não estiver logado, vai para a página de login.
    return redirect(url_for('login'))


@app.route('/cadastro', methods=['GET', 'POST'])
def cadastro():
    """ Rota para a página de cadastro de novos usuários. """
    # Se o formulário for enviado (método POST).
    if request.method == 'POST':
        # Coleta os dados do formulário.
        nome = request.form['nome']
        username = request.form['username']
        email = request.form['email']
        # Gera um hash seguro para a senha antes de salvar no banco.
        senha = generate_password_hash(request.form['senha'])
        
        # Conecta ao banco de dados.
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor(buffered=True)
        
        # Verifica se o nome de usuário ou e-mail já existem para evitar duplicatas.
        cursor.execute("SELECT * FROM usuario WHERE username_usuario = %s OR email_usuario = %s", (username, email))
        if cursor.fetchone():
            flash("Nome de usuário ou e-mail já cadastrado.", "erro")
            cursor.close()
            conn.close()
            return redirect(url_for('cadastro'))
        
        # Insere o novo usuário no banco. Por padrão, tipo_usuario=2 (usuário comum) e conta_ativa=True.
        cursor.execute("""INSERT INTO usuario (nome_usuario, username_usuario, password_usuario, email_usuario, tipo_usuario, conta_ativa)
                          VALUES (%s, %s, %s, %s, %s, %s)""", (nome, username, senha, email, 2, True))
        conn.commit()  # Confirma a transação.
        cursor.close()
        conn.close()
        
        flash("Cadastro realizado com sucesso! Você já pode fazer login.", "sucesso")
        return redirect(url_for('login'))
        
    # Se for uma requisição GET, apenas renderiza a página de cadastro.
    return render_template('cadastro.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    """ Rota para a página de login do sistema. """
    if request.method == 'POST':
        username = request.form['username'].strip()
        senha = request.form['senha'].strip()
        
        conn = mysql.connector.connect(**db_config)
        # `dictionary=True` faz o cursor retornar os resultados como dicionários (útil para acessar colunas pelo nome).
        cursor = conn.cursor(dictionary=True, buffered=True)
        
        # Busca o usuário pelo nome de usuário fornecido.
        cursor.execute("SELECT * FROM usuario WHERE username_usuario = %s", (username,))
        usuario = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        # Verifica se o usuário existe e se a senha fornecida corresponde ao hash salvo no banco.
        if usuario and check_password_hash(usuario['password_usuario'], senha):
            # Verifica se a conta não está desativada.
            if not usuario['conta_ativa']:
                flash("Esta conta está desativada. Entre em contato com o administrador.", "erro")
                return redirect(url_for('login'))
            
            # Salva os dados do usuário na sessão para mantê-lo logado.
            session['usuario_id'] = usuario['cod_usuario']
            session['usuario_nome'] = usuario['nome_usuario']
            session['tipo_usuario'] = usuario['tipo_usuario']
            
            # Redireciona para o dashboard se for administrador.
            if usuario['tipo_usuario'] == 1:
                return redirect(url_for('admin.dashboard'))
            else:
                # Se não for admin, exibe um erro e volta para o login.
                flash("Acesso permitido apenas para administradores.", "erro")
                return redirect(url_for('login'))
        else:
            # Se o usuário não existir ou a senha estiver incorreta.
            flash("Usuário ou senha inválidos.", "erro")
            return redirect(url_for('login'))
            
    return render_template('login.html')


@app.route('/logout')
def logout():
    """ Rota para remover os dados do usuário da sessão (logout). """
    session.pop('usuario_id', None)
    session.pop('usuario_nome', None)
    session.pop('tipo_usuario', None)
    flash("Você saiu da sua conta.", "sucesso")
    return redirect(url_for('login'))

# ==========================
# UNIDADES DE MEDIDA - CRUD
# ==========================

@app.route('/sistema/admin/unidades')
def listar_unidades():
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM unidade_medida")
    unidades = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('unidades.html', unidades=unidades)

@app.route('/sistema/admin/unidades/nova', methods=['GET', 'POST'])
def nova_unidade():
    if request.method == 'POST':
        nome = request.form['nome_unidade']
        sigla = request.form['sigla_unidade']
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO unidade_medida (nome_unidade, sigla_unidade) VALUES (%s, %s)",
            (nome, sigla)
        )
        conn.commit()
        cursor.close()
        conn.close()
        return redirect(url_for('listar_unidades'))
    return render_template('unidades_form.html', acao='Nova')

@app.route('/sistema/admin/unidades/editar/<int:id>', methods=['GET', 'POST'])
def editar_unidade(id):
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor(dictionary=True)

    if request.method == 'POST':
        nome = request.form['nome_unidade']
        sigla = request.form['sigla_unidade']
        cursor.execute(
            "UPDATE unidade_medida SET nome_unidade=%s, sigla_unidade=%s WHERE cod_unidade=%s",
            (nome, sigla, id)
        )
        conn.commit()
        cursor.close()
        conn.close()
        return redirect(url_for('listar_unidades'))

    cursor.execute("SELECT * FROM unidade_medida WHERE cod_unidade = %s", (id,))
    unidade = cursor.fetchone()
    cursor.close()
    conn.close()
    return render_template('unidades_form.html', unidade=unidade, acao='Editar')

@app.route('/sistema/admin/unidades/excluir/<int:id>')
def excluir_unidade(id):
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM unidade_medida WHERE cod_unidade = %s", (id,))
    conn.commit()
    cursor.close()
    conn.close()
    return redirect(url_for('listar_unidades'))

# =====================================================================
# SEÇÃO 5: ÁREA ADMINISTRATIVA (/sistema/admin/)
# Um Blueprint organiza um grupo de rotas relacionadas em um módulo.
# =====================================================================
admin_bp = Blueprint('admin', __name__, url_prefix='/sistema/admin')

@admin_bp.route('/')
@admin_required
def index():
    """ Rota raiz do admin, que apenas redireciona para o dashboard. """
    return redirect(url_for('admin.dashboard'))

@admin_bp.route('/dashboard')
@admin_required
def dashboard():
    """ Rota do painel de controle (dashboard) com estatísticas do sistema. """
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor(dictionary=True)
    
    # Coleta de dados para os cards de resumo.
    cursor.execute("SELECT COUNT(*) as total FROM produto")
    total_produtos = cursor.fetchone()['total']
    cursor.execute("SELECT COUNT(*) as total FROM categoria_produto")
    total_categorias = cursor.fetchone()['total']
    cursor.execute("SELECT COUNT(*) as total FROM venda")
    total_vendas = cursor.fetchone()['total']
    
    # Cálculo do saldo atual do caixa (entradas - saídas).
    cursor.execute("""
        SELECT 
            COALESCE((SELECT SUM(valor) FROM caixa WHERE tipo = 'entrada'), 0) - 
            COALESCE((SELECT SUM(valor) FROM caixa WHERE tipo = 'saida'), 0) 
        AS saldo
    """)
    saldo_caixa = cursor.fetchone()['saldo']

    # Busca as últimas 5 vendas para exibir na tabela de vendas recentes.
    cursor.execute("""
        SELECT v.cod_venda, v.total, v.data_venda, u.nome_usuario 
        FROM venda v JOIN usuario u ON v.cod_usuario = u.cod_usuario 
        ORDER BY v.data_venda DESC LIMIT 5
    """)
    vendas_recentes = cursor.fetchall()
    
    cursor.close()
    conn.close()

    # Renderiza a página do dashboard, passando todos os dados coletados para o template.
    return render_template('dashboard.html', 
                           total_produtos=total_produtos,
                           total_categorias=total_categorias,
                           total_vendas=total_vendas,
                           saldo_caixa=saldo_caixa,
                           vendas_recentes=vendas_recentes)

# --- CRUD para Usuários ---
@admin_bp.route('/usuarios')
@admin_required
def usuarios():
    """ Rota para listar todos os usuários do sistema. """
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT cod_usuario, nome_usuario, username_usuario, email_usuario, tipo_usuario, conta_ativa FROM usuario ORDER BY nome_usuario ASC")
    lista_usuarios = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('usuarios.html', usuarios=lista_usuarios)

@admin_bp.route('/usuarios/editar/<int:cod>', methods=['GET', 'POST'])
@admin_required
def editar_usuario(cod):
    """ Rota para editar o tipo e o status de um usuário. """
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor(dictionary=True)

    if request.method == 'POST':
        tipo_usuario = request.form['tipo_usuario']
        # Verifica se o checkbox 'conta_ativa' foi marcado no formulário.
        conta_ativa = 'conta_ativa' in request.form

        cursor.execute("UPDATE usuario SET tipo_usuario = %s, conta_ativa = %s WHERE cod_usuario = %s", (tipo_usuario, conta_ativa, cod))
        conn.commit()
        cursor.close()
        conn.close()
        flash("Usuário atualizado com sucesso!", "sucesso")
        return redirect(url_for('admin.usuarios'))

    # Se GET, busca os dados do usuário para preencher o formulário de edição.
    cursor.execute("SELECT cod_usuario, nome_usuario, username_usuario, email_usuario, tipo_usuario, conta_ativa FROM usuario WHERE cod_usuario = %s", (cod,))
    usuario = cursor.fetchone()
    cursor.close()
    conn.close()
    if not usuario:
        flash("Usuário não encontrado.", "erro")
        return redirect(url_for('admin.usuarios'))
        
    return render_template('editar_usuario.html', usuario=usuario)

# --- CRUD para PVP ---
@admin_bp.route('/pvps')
@admin_required
def pvps():
    """ Rota para listar todos os PVPs. """
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM pvp ORDER BY nome_pvp ASC")
    lista_pvps = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('pvps.html', pvps=lista_pvps)

@admin_bp.route('/pvps/cadastrar', methods=['GET', 'POST'])
@admin_required
def cadastrar_pvp():
    """ Rota para cadastrar um novo PVP. """
    if request.method == 'POST':
        nome = request.form['nome_pvp']
        percentual = request.form['percentual']
        tipo = request.form['tipo_pvp']
        
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor(dictionary=True)

        # Validação para impedir o cadastro de mais de um PVP Global ativo.
        if tipo == 'global':
            cursor.execute("SELECT cod_pvp FROM pvp WHERE tipo_pvp = 'global' AND ativo = TRUE")
            if cursor.fetchone():
                flash("Já existe um PVP Global ativo. Inative o PVP existente antes de cadastrar um novo.", "erro")
                cursor.close()
                conn.close()
                return redirect(url_for('admin.cadastrar_pvp'))

        query = "INSERT INTO pvp (nome_pvp, percentual, tipo_pvp) VALUES (%s, %s, %s)"
        cursor.execute(query, (nome, percentual, tipo))
        conn.commit()
        cursor.close()
        conn.close()
        flash("PVP cadastrado com sucesso!", "sucesso")
        return redirect(url_for('admin.pvps'))

    return render_template('cadastrar_pvp.html')

@admin_bp.route('/pvps/editar/<int:cod>', methods=['GET', 'POST'])
@admin_required
def editar_pvp(cod):
    """ Rota para editar um PVP existente. """
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor(dictionary=True)

    if request.method == 'POST':
        nome = request.form['nome_pvp']
        percentual = request.form['percentual']
        tipo = request.form['tipo_pvp']
        ativo = 'ativo' in request.form
        
        # Validação para impedir que mais de um PVP Global seja ativado.
        if tipo == 'global' and ativo:
            # Procura por outro PVP global ativo que não seja o que está sendo editado.
            cursor.execute("SELECT cod_pvp FROM pvp WHERE tipo_pvp = 'global' AND ativo = TRUE AND cod_pvp != %s", (cod,))
            if cursor.fetchone():
                flash("Já existe outro PVP Global ativo. Inative o PVP existente antes de ativar este.", "erro")
                cursor.close()
                conn.close()
                return redirect(url_for('admin.editar_pvp', cod=cod))

        query = """
            UPDATE pvp SET nome_pvp = %s, percentual = %s, tipo_pvp = %s, ativo = %s
            WHERE cod_pvp = %s
        """
        cursor.execute(query, (nome, percentual, tipo, ativo, cod))
        conn.commit()
        cursor.close()
        conn.close()
        flash("PVP atualizado com sucesso!", "sucesso")
        return redirect(url_for('admin.pvps'))

    # Se GET, busca dados do PVP para preencher o formulário.
    cursor.execute("SELECT * FROM pvp WHERE cod_pvp = %s", (cod,))
    pvp = cursor.fetchone()
    if not pvp:
        flash("PVP não encontrado.", "erro")
        return redirect(url_for('admin.pvps'))
    
    cursor.close()
    conn.close()
    return render_template('editar_pvp.html', pvp=pvp)

@admin_bp.route('/pvps/excluir/<int:cod>', methods=['POST'])
@admin_required
def excluir_pvp(cod):
    """ Rota para excluir um PVP. """
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM pvp WHERE cod_pvp = %s", (cod,))
        conn.commit()
        cursor.close()
        conn.close()
        flash("PVP excluído com sucesso!", "sucesso")
    except mysql.connector.Error as err:
        # Captura erro se o PVP estiver em uso por uma categoria (chave estrangeira).
        flash(f"Não foi possível excluir o PVP. Verifique se ele não está em uso por uma categoria. Erro: {err}", "erro")
    return redirect(url_for('admin.pvps'))

# --- CRUD para Categorias ---
@admin_bp.route('/categorias')
@admin_required
def categorias():
    """ Lista todas as categorias cadastradas. """
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT c.cod_categoria, c.nome_categoria, c.descricao_categoria, 
               p.nome_pvp AS nome_pvp
        FROM categoria_produto c
        LEFT JOIN pvp p ON c.pvp_categoria = p.cod_pvp
        ORDER BY c.nome_categoria ASC
    """)
    lista_categorias = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('categorias.html', categorias=lista_categorias)


@admin_bp.route('/categorias/cadastrar', methods=['GET', 'POST'])
@admin_required
def cadastrar_categoria():
    """ Cadastra uma nova categoria de produto. """
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor(dictionary=True)

    # Busca lista de PVPs para o select do formulário
    cursor.execute("SELECT cod_pvp, nome_pvp FROM pvp WHERE ativo = TRUE ORDER BY nome_pvp ASC")
    lista_pvps = cursor.fetchall()

    if request.method == 'POST':
        nome = request.form['nome_categoria']
        descricao = request.form['descricao_categoria']
        pvp = request.form.get('pvp_categoria') or None

        cursor.execute("""
            INSERT INTO categoria_produto (nome_categoria, descricao_categoria, pvp_categoria)
            VALUES (%s, %s, %s)
        """, (nome, descricao, pvp))
        conn.commit()
        cursor.close()
        conn.close()
        flash("Categoria cadastrada com sucesso!", "sucesso")
        return redirect(url_for('admin.categorias'))

    cursor.close()
    conn.close()
    return render_template('cadastrar_categoria.html', pvps=lista_pvps)


@admin_bp.route('/categorias/editar/<int:cod>', methods=['GET', 'POST'])
@admin_required
def editar_categoria(cod):
    """ Edita uma categoria existente. """
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor(dictionary=True)

    # Busca lista de PVPs
    cursor.execute("SELECT cod_pvp, nome_pvp FROM pvp ORDER BY nome_pvp ASC")
    lista_pvps = cursor.fetchall()

    # Busca categoria atual
    cursor.execute("SELECT * FROM categoria_produto WHERE cod_categoria = %s", (cod,))
    categoria = cursor.fetchone()

    if not categoria:
        cursor.close()
        conn.close()
        flash("Categoria não encontrada.", "erro")
        return redirect(url_for('admin.categorias'))

    if request.method == 'POST':
        nome = request.form['nome_categoria']
        descricao = request.form['descricao_categoria']
        pvp = request.form.get('pvp_categoria') or None

        cursor.execute("""
            UPDATE categoria_produto
            SET nome_categoria=%s, descricao_categoria=%s, pvp_categoria=%s
            WHERE cod_categoria=%s
        """, (nome, descricao, pvp, cod))
        conn.commit()
        cursor.close()
        conn.close()
        flash("Categoria atualizada com sucesso!", "sucesso")
        return redirect(url_for('admin.categorias'))

    cursor.close()
    conn.close()
    return render_template('editar_categoria.html', categoria=categoria, pvps=lista_pvps)


@admin_bp.route('/categorias/excluir/<int:cod>', methods=['POST'])
@admin_required
def excluir_categoria(cod):
    """ Exclui uma categoria do banco. """
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM categoria_produto WHERE cod_categoria = %s", (cod,))
        conn.commit()
        cursor.close()
        conn.close()
        flash("Categoria excluída com sucesso!", "sucesso")
    except mysql.connector.Error as err:
        flash(f"Erro ao excluir categoria: {err}", "erro")
    return redirect(url_for('admin.categorias'))

# =====================================================================
# SEÇÃO 6: REGISTRO DO BLUEPRINT E EXECUÇÃO
# Finaliza a configuração e inicia a aplicação.
# =====================================================================

# Registra o blueprint administrativo na aplicação principal para que as rotas funcionem.
app.register_blueprint(admin_bp)

# Bloco de execução principal: só roda o servidor se o script for executado diretamente.
if __name__ == '__main__':
    # `debug=True` ativa o modo de depuração, que recarrega o servidor a cada alteração
    # e mostra mensagens de erro detalhadas no navegador. É muito útil para desenvolvimento.
    # Lembre-se de desativar (mudar para False) em um ambiente de produção.
    app.run(debug=True)

from sistema.admin.unidades import unidades_bp
app.register_blueprint(unidades_bp)