CREATE DATABASE caixa;

USE caixa;

-- =====================================================================
-- Criação das tabelas
-- =====================================================================

CREATE TABLE usuario (
    cod_usuario INT AUTO_INCREMENT PRIMARY KEY,
    nome_usuario VARCHAR(100) NOT NULL,
    username_usuario VARCHAR(100) UNIQUE NOT NULL,
    email_usuario VARCHAR(100) UNIQUE NOT NULL,
    password_usuario VARCHAR(255) NOT NULL,
    foto_usuario VARCHAR(100),  -- arquivo da imagem do usuário
    conta_ativa BOOLEAN NOT NULL DEFAULT TRUE,
    criacao_usuario TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    tipo_usuario INT NOT NULL  -- 1 = Admin, 2 = Usuário      
);

CREATE TABLE pvp (
    cod_pvp INT AUTO_INCREMENT PRIMARY KEY,
    nome_pvp VARCHAR(100) NOT NULL,
    percentual DECIMAL(5,2) NOT NULL,
    tipo_pvp ENUM('global', 'categoria') NOT NULL,
    data_inicio TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    data_fim DATETIME DEFAULT NULL,
    ativo BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE TABLE categoria_produto (
    cod_categoria INT AUTO_INCREMENT PRIMARY KEY,
    nome_categoria VARCHAR(100) NOT NULL,
    pvp_categoria INT NOT NULL,
    descricao_categoria TEXT,
    FOREIGN KEY (pvp_categoria) REFERENCES pvp(cod_pvp)
);

CREATE TABLE unidade_medida (
    cod_unidade INT AUTO_INCREMENT PRIMARY KEY,
    nome_unidade VARCHAR(50) NOT NULL,
    sigla_unidade VARCHAR(10) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=latin1 COLLATE=latin1_swedish_ci;

CREATE TABLE produto (
    cod_produto INT AUTO_INCREMENT PRIMARY KEY,
    nome_produto VARCHAR(100) NOT NULL,
    descricao_produto TEXT,
    preco_compra DECIMAL(10,2) NOT NULL,
    preco_venda DECIMAL(10,2) NOT NULL,
    quantidade INT NOT NULL DEFAULT 0,
    cod_unidade INT NOT NULL,
    codigo_barras VARCHAR(13) UNIQUE NOT NULL,
    ativo BOOLEAN NOT NULL DEFAULT TRUE,
    cod_categoria INT NOT NULL,
    cod_pvp INT NOT NULL,
    data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (cod_categoria) REFERENCES categoria_produto(cod_categoria),
    FOREIGN KEY (cod_pvp) REFERENCES pvp(cod_pvp),
    FOREIGN KEY (cod_unidade) REFERENCES unidade_medida(cod_unidade)
);

CREATE TABLE venda (
    cod_venda INT AUTO_INCREMENT PRIMARY KEY,
    cod_usuario INT NOT NULL,
    data_venda TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    total DECIMAL(10,2) NOT NULL,
    FOREIGN KEY (cod_usuario) REFERENCES usuario(cod_usuario)
);

CREATE TABLE item_venda (
    cod_item INT AUTO_INCREMENT PRIMARY KEY,
    cod_venda INT NOT NULL,
    cod_produto INT NOT NULL,
    quantidade INT NOT NULL,
    preco_unitario DECIMAL(10,2) NOT NULL,
    FOREIGN KEY (cod_venda) REFERENCES venda(cod_venda),
    FOREIGN KEY (cod_produto) REFERENCES produto(cod_produto)
);

DELIMITER $$
CREATE TRIGGER after_venda_insert
AFTER INSERT ON item_venda
FOR EACH ROW
BEGIN
    UPDATE produto 
    SET quantidade = quantidade - NEW.quantidade
    WHERE cod_produto = NEW.cod_produto;
END;
$$
DELIMITER ;

CREATE TABLE caixa (
    cod_caixa INT AUTO_INCREMENT PRIMARY KEY,
    tipo ENUM('entrada', 'saida') NOT NULL,
    valor DECIMAL(10,2) NOT NULL,
    descricao TEXT,
    data_movimentacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    cod_usuario INT NOT NULL,
    FOREIGN KEY (cod_usuario) REFERENCES usuario(cod_usuario)
);

-- =====================================================================
-- Inserts iniciais
-- =====================================================================

-- Unidade de Medida
INSERT INTO unidade_medida (nome_unidade, sigla_unidade) VALUES
('Quilograma','kg'),('Grama','g'),('Litro','L'),('Mililitro','mL'),('Metro','m'),
('Centímetro','cm'),('Unidade','un'),('Caixa','cx'),('Pacote','pct'),('Dúzia','dz');

-- PVP
INSERT INTO pvp (nome_pvp, percentual, tipo_pvp, ativo) VALUES
('PVP Alimentos Básicos',1.20,'categoria',TRUE),
('PVP Carnes e Aves',1.25,'categoria',TRUE),
('PVP Global Padrão',1.20,'global',TRUE);

-- Categoria Produto
INSERT INTO categoria_produto (nome_categoria, pvp_categoria, descricao_categoria) VALUES
('Alimentos Básicos',1,'Arroz, feijão, macarrão, farinha, açúcar, sal e outros itens essenciais.'),
('Carnes e Aves',2,'Carne bovina, suína, frango, peixe e derivados.');

-- Produtos de exemplo
INSERT INTO produto (nome_produto, descricao_produto, preco_compra, preco_venda, quantidade, cod_unidade, codigo_barras, ativo, cod_categoria, cod_pvp) VALUES
('Arroz Branco 5kg','Arroz tipo 1, embalagem 5kg',20.00,25.00,50,1,'1234567890123',TRUE,1,1),
('Feijão Carioca 1kg','Feijão tipo 1, pacote 1kg',7.00,9.00,100,2,'1234567890124',TRUE,1,1),
('Frango Congelado 1kg','Peito de frango congelado 1kg',12.00,15.00,80,1,'1234567890125',TRUE,2,2);
