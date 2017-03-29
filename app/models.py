# coding: utf-8

################################################################################
## SICEM - UFC
################################################################################
## Modelos do Banco de Dados
################################################################################


import datetime
from flask import current_app
from flask_login import UserMixin, AnonymousUserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from geoalchemy2.types import Geometry

from . import db, login_manager


########## Definição de Permissões dos Usuários ##########


class Permissao:
    VISUALIZAR = 0x01
    CADASTRAR = 0x02
    ADMINISTRAR = 0xff


########## Modelos de Acesso ao Sistema ##########


# Cargos (Tipos de Usuários)
class Cargo(db.Model):
    __tablename__ = 'cargos'

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(36), index=True, unique=True, nullable=False)
    permissoes = db.Column(db.Integer, nullable=False)
    padrao = db.Column(db.Boolean, default=False, index=True, nullable=False)
    usuarios = db.relationship('Usuario', backref='cargo', lazy='dynamic')


    # Método para adicionar os cargos na tabela de cargos
    @staticmethod
    def criar_cargos():
        cargos = {
            u'Usuário': (Permissao.VISUALIZAR, True),
            u'Cadastrador': (Permissao.CADASTRAR, False),
            u'Desenvolvedor': (Permissao.ADMINISTRAR, False),
            u'Administrador': (Permissao.ADMINISTRAR, False)
        }

        for nome_cargo in cargos:
            cargo = Cargo.query.filter_by(nome=nome_cargo).first()

            if cargo is None:
                cargo = Cargo(nome=nome_cargo)
                cargo.permissoes = cargos[nome_cargo][0]
                cargo.padrao = cargos[nome_cargo][1]
                db.session.add(cargo)

        db.session.commit()

    def __repr__(self):
        return '<Cargo: %s>' % self.nome

    def __str__(self):
        return self.nome


# Usuários
class Usuario(UserMixin, db.Model):
    __tablename__ = 'usuarios'

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(64), index=True, nullable=False)
    email = db.Column(db.String(64), index=True, unique=True, nullable=False)
    senha_hash = db.Column(db.String(128))
    verificado = db.Column(db.Boolean, default=False)
    confirmado = db.Column(db.Boolean, default=False)
    id_cargo = db.Column(db.Integer, db.ForeignKey('cargos.id'))


    def __init__(self, **kwargs):
        super(Usuario, self).__init__(**kwargs)
        
        # Definindo dados padrão para novos usuários
        if self.cargo is None:
            self.cargo = Cargo.query.filter_by(padrao=True).first()
            self.verificado = False
            self.confirmado = False
                
    # Método para criar o primeiro administrador, caso não haja um ainda
    @staticmethod
    def criar_administrador():
        if not Usuario.query.join(Cargo).filter(Cargo.nome=='Administrador').first():
            administrador = Usuario(email=current_app.config['ADMIN_EMAIL'])
            administrador.nome = 'Administrador'
            administrador.senha = current_app.config['ADMIN_SENHA']
            administrador.verificado = True
            administrador.confirmado = True
            administrador.cargo = Cargo.query.filter_by(nome='Administrador').first()

            db.session.add(administrador)
            db.session.commit()

    # Bloquear leitura da senha
    @property
    def senha(self):
        raise AttributeError('A senha não pode ser lida!')

    # Armazenar apenas hash da senha cadastrada
    @senha.setter
    def senha(self, senha):
        self.senha_hash = generate_password_hash(senha)

    # Testa se a senha é correta a partir do hash
    def verificar_senha(self, senha):
        return check_password_hash(self.senha_hash, senha)

    # Gera token para confirmação de nova conta
    def gerar_token_confirmacao(self, validade=3600):
        s = Serializer(current_app.config['SECRET_KEY'], validade)
        return s.dumps({'confirmar': self.id})

    # Confirma nova conta se o token recebido for correto
    def confirmar_conta(self, token):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except:
            return False

        if data.get('confirmar') != self.id:
            return False

        self.confirmado = True
        db.session.add(self)

        return True

    # Gera token para recuperação de senha
    def gerar_token_recuperacao_senha(self, validade=3600):
        s = Serializer(current_app.config['SECRET_KEY'], validade)
        return s.dumps({'recuperar': self.id})

    # Atualiza senha se o token recebido for correto
    def recuperar_senha(self, token, senha_nova):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except:
            return False

        if data.get('confirmar') != self.id:
            return False

        self.senha = senha_nova
        db.session.add(self)

        return True

    # Gera token para alteração de email
    def gerar_token_alteracao_email(self, email_novo, validade=3600):
        s = Serializer(current_app.config['SECRET_KEY'], validade)
        return s.dumps({'alterar_email': self.id, 'email_novo': email_novo})

    # Atualiza email se o token recebido for correto
    def alterar_email(self, token):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except:
            return False

        if data.get('alterar_email') != self.id:
            return False

        email_novo = data.get('email_novo')
        
        if email_novo is None:
            return False

        if self.query.filter_by(email=email_novo).first():
            return False

        self.email = email_novo
        db.session.add(self)

        return True

    # Testa se o usuário tem determinadas permissões
    def autorizado(self, permissoes):
        return self.cargo is not None and \
            (self.cargo.permissoes & permissoes) == permissoes

    # Testa se o usuário é administrador ou desenvolvedor
    def administrador(self):
        return self.autorizado(Permissao.ADMINISTRAR)

    # Testa se o usuário é cadastrador
    def cadastrador(self):
        return self.autorizado(Permissao.CADASTRAR)    

    # Gera lista de administradores
    @staticmethod
    def listar_administradores():
        return Usuario.query.join(Cargo).filter(Cargo.nome=='Administrador').all()

    # Gera lista de desenvolvedores
    @staticmethod
    def listar_desenvolvedores():
        return Usuario.query.join(Cargo).filter(Cargo.nome=='Desenvolvedor').all()

    def __repr__(self):
        return '<Usuário: %s [%s]>' % (self.nome, self.cargo.nome)

    def __str__(self):
        return self.nome


# Usuário Anônimo
class UsuarioAnonimo(AnonymousUserMixin):
    # Nenhuma permissão, apenas visualização
    def autorizado(self, permissoes):
        return False

    def cadastrador(self):
        return False

    def administrador(self):
        return False


########## Configurações Adicionais do Sistema de Login ##########


# Definir usuário anônimo
login_manager.anonymous_user = UsuarioAnonimo

# Função para que o sistema de login possa carregar um usuário
@login_manager.user_loader
def load_user(id_usuario):
    return Usuario.query.get(int(id_usuario))


########## Modelos do Sistema ##########


# Instituição (Topo da Hierarquia)
class Instituicao(db.Model):
    __tablename__ = 'instituicoes'

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(64), index=True, unique=True, nullable=False)
    campi = db.relationship('Campus', backref='instituicao', lazy='dynamic')


    def __repr__(self):
        return '<Instituição: %s>' % self.nome

    def __str__(self):
        return self.nome


# Campi
class Campus(db.Model):
    __tablename__ = 'campi'
    
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(64), index=True, unique=True, nullable=False)
    id_instituicao = db.Column(db.Integer, db.ForeignKey('instituicoes.id'))
    mapeamento = db.Column(Geometry("MULTIPOLYGON"), unique=True)
    centros = db.relationship('Centro', backref='campus', lazy='dynamic')


    def __repr__(self):
        return '<Campus: %s [%s]>' % (self.nome, self.instituicao.nome)

    def __str__(self):
        return self.nome


# Centros
class Centro(db.Model):
    __tablename__ = 'centros'

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(64), index=True, nullable=False)
    id_campus = db.Column(db.Integer, db.ForeignKey('campi.id'))
    mapeamento = db.Column(Geometry("MULTIPOLYGON"), unique=True)
    departamentos = db.relationship('Departamento', backref='centro', lazy='dynamic')


    def __repr__(self):
        return '<Centro: %s [%s]>' % (self.nome, self.campus.nome)

    def __str__(self):
        return self.nome


# Departamentos
class Departamento(db.Model):
    __tablename__ = 'departamentos'

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(64), index=True, nullable=False)
    id_centro = db.Column(db.Integer, db.ForeignKey('centros.id'))
    blocos = db.relationship('Bloco', backref='departamento', lazy='dynamic')


    def __repr__(self):
        return '<Departamento: %s [%s]>' % (self.nome, self.centro.nome)

    def __str__(self):
        return self.nome


# Blocos
class Bloco(db.Model):
    __tablename__ = 'blocos'

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(64), index=True, nullable=False)
    localizacao = db.Column(Geometry("POINT"), unique=True)
    id_departamento = db.Column(db.Integer, db.ForeignKey('departamentos.id'))
    ambientes = db.relationship('Ambiente', backref='bloco', lazy='dynamic')   


    def __repr__(self):
        return '<Bloco: %s [%s]>' % (self.nome, self.departamento)

    def __str__(self):
        return self.nome


# Ambientes
class Ambiente(db.Model):
    __tablename__ = 'ambientes'

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(64), index=True, nullable=False)
    tipo = db.Column(db.String(64), index=True)
    id_bloco = db.Column(db.Integer, db.ForeignKey('blocos.id'))
    detalhe_localizacao = db.Column(db.Text)
    equipamentos = db.relationship('Equipamento', backref='ambiente', lazy='dynamic')

    __mapper_args__ = {
        'polymorphic_identity': u'Ambiente',
        'polymorphic_on': tipo
    }


    def __repr__(self):
        return '<Ambiente: %s>' % self.nome

    def __str__(self):
        return self.nome


# Ambientes Internos (Subclasse de Ambientes)
class AmbienteInterno(Ambiente):
    __tablename__ = 'ambientes_internos'

    id = db.Column(db.Integer, db.ForeignKey('ambientes.id'), primary_key=True)
    andar = db.Column(db.String(15))
    area = db.Column(db.Float)
    populacao = db.Column(db.Integer)

    __mapper_args__ = { 'polymorphic_identity': u'Ambiente Interno' }


    def __init__(self, **kwargs):
        super(AmbienteInterno, self).__init__(**kwargs)
        self.tipo = 'Ambiente Interno'

    def __repr__(self):
        return '<Ambiente Interno: %s [%s - %s - %s - %s]>' % \
            (self.nome, self.bloco.nome, self.bloco.departamento.nome,
             self.bloco.departamento.centro.nome,
             self.bloco.departamento.centro.campus.nome)

    def __str__(self):
        return '%s [%s - %s - %s - %s]' % \
            (self.nome, self.bloco.nome, self.bloco.departamento.nome,
             self.bloco.departamento.centro.nome,
             self.bloco.departamento.centro.campus.nome)


# Ambientes Externos (Subclasse de Ambientes)
class AmbienteExterno(Ambiente):
    __tablename__ = 'ambientes_externos'
    
    id = db.Column(db.Integer, db.ForeignKey('ambientes.id'), primary_key=True)

    __mapper_args__ = { 'polymorphic_identity': u'Ambiente Externo' }


    def __init__(self, **kwargs):
        super(AmbienteExterno, self).__init__(**kwargs)
        self.tipo = 'Ambiente Externo'

    def __repr__(self):
        return '<Ambiente Externo: %s [%s - %s - %s - %s]>' % \
            (self.nome, self.bloco.nome, self.bloco.departamento.nome,
             self.bloco.departamento.centro.nome,
             self.bloco.departamento.centro.campus.nome)

    def __str__(self):
        return '%s [%s - %s - %s - %s]' % \
            (self.nome, self.bloco.nome, self.bloco.departamento.nome,
             self.bloco.departamento.centro.nome,
             self.bloco.departamento.centro.campus.nome)


# Subestações Abrigadas (Subclasse de Ambientes)
class SubestacaoAbrigada(Ambiente):
    __tablename__ = 'subestacoes_abrigadas'
    
    id = db.Column(db.Integer, db.ForeignKey('ambientes.id'), primary_key=True)
    localizacao = db.Column(Geometry("POINT"), unique=True)

    __mapper_args__ = { 'polymorphic_identity': u'Subestação Abrigada' }


    def __init__(self, **kwargs):
        super(SubestacaoAbrigada, self).__init__(**kwargs)
        self.tipo = 'Subestação Abrigada'

    def __repr__(self):
        return '<Subestação Abrigada: %s [%s]>' % \
            (self.nome, self.bloco.departamento.centro.campus.nome)

    def __str__(self):
        return '%s [%s]' % \
            (self.nome, self.bloco.departamento.centro.campus.nome)


# Subestações Aéreas (Subclasse de Ambientes)
class SubestacaoAerea(Ambiente):
    __tablename__ = 'subestacoes_aereas'
    
    id = db.Column(db.Integer, db.ForeignKey('ambientes.id'), primary_key=True)
    localizacao = db.Column(Geometry("POINT"), unique=True)

    __mapper_args__ = { 'polymorphic_identity': u'Subestação Aérea' }


    def __init__(self, **kwargs):
        super(SubestacaoAerea, self).__init__(**kwargs)
        self.tipo = 'Subestação Aérea'

    def __repr__(self):
        return '<Subestação Aérea: %s [%s]>' % \
            (self.nome, self.bloco.departamento.centro.campus.nome)

    def __str__(self):
        return '%s [%s]' % \
            (self.nome, self.bloco.departamento.centro.campus.nome)


# Equipamentos
class Equipamento(db.Model):
    __tablename__ = 'equipamentos'

    id = db.Column(db.Integer, primary_key=True)
    tombamento = db.Column(db.Integer)
    id_ambiente = db.Column(db.Integer, db.ForeignKey('ambientes.id'))
    categoria_equipamento = db.Column(db.String(64), index=True)
    tipo_equipamento = db.Column(db.String(64), index=True)
    fabricante = db.Column(db.String(64), index=True)
    intervalo_manutencao = db.Column(db.Integer)    # Valor em meses
    manutencoes = db.relationship('Manutencao', backref='equipamento', lazy='dynamic')
    proxima_manutencao = db.Column(db.Date, index=True)
    info_adicional = db.Column(db.Text)
    em_uso = db.Column(db.Boolean, default=True, index=True)
    em_manutencao = db.Column(db.Boolean, default=False, index=True)    # Se houver manutenção aberta
    inicio_manutencao = db.Column(db.Date, index=True)  # Data de abertura da manutenção atual

    __mapper_args__ = {
        'polymorphic_identity': u'Equipamento',
        'polymorphic_on': tipo_equipamento
    }


    def __repr__(self):
        return '<%s: %d [%s]>' % \
            (self.tipo_equipamento, self.tombamento, self.ambiente)

    def __str__(self):
        return '%s %d [%s]' % \
            (self.tipo_equipamento, self.tombamento, self.ambiente)


# Extintores (Subclasse de Equipamentos)
class Extintor(Equipamento):
    __tablename__ = 'extintores'
    
    id = db.Column(db.Integer, db.ForeignKey('equipamentos.id'), primary_key=True)
    classificacao = db.Column(db.String(64))    # Agente extintor e classe de fogo
    carga_nominal = db.Column(db.Float)         # Valor em kg

    __mapper_args__ = { 'polymorphic_identity': u'Extintor' }


    def __init__(self, **kwargs):
        super(Extintor, self).__init__(**kwargs)
        self.tipo_equipamento = 'Extintor'
        self.categoria_equipamento = 'Combate a Incêndio'


# Condicionadores de Ar (Subclasse de Equipamentos)
class CondicionadorAr(Equipamento):
    __tablename__ = 'condicionadores_ar'
    
    id = db.Column(db.Integer, db.ForeignKey('equipamentos.id'), primary_key=True)
    classificacao = db.Column(db.String(64))    # Janela, split, teto, ...
    pot_nominal = db.Column(db.Integer)         # Em W (valor inteiro)
    cap_refrigeracao = db.Column(db.Integer)    # Em Btu/h (valor inteiro)
    tensao_alimentacao = db.Column(db.Integer)  # Em V (valor inteiro)
    eficiencia = db.Column(db.String(1))        # Selo Procel (A, B, C, D, E, F, G)

    __mapper_args__ = { 'polymorphic_identity': u'Condicionador de Ar' }


    def __init__(self, **kwargs):
        super(CondicionadorAr, self).__init__(**kwargs)
        self.tipo_equipamento = 'Condicionador de Ar'
        self.categoria_equipamento = 'Equipamento Elétrico'


# Manutenções
class Manutencao(db.Model):
    __tablename__ = 'manutencoes'
    
    id = db.Column(db.Integer, primary_key=True)
    num_ordem_servico = db.Column(db.Integer, nullable=False)
    id_equipamento = db.Column(db.Integer, db.ForeignKey('equipamentos.id'))
    data_abertura = db.Column(db.Date, index=True, nullable=False)
    data_conclusao = db.Column(db.Date, index=True)
    tipo_manutencao = db.Column(db.String(64), index=True)
    descricao_servico = db.Column(db.Text)
    status = db.Column(db.String(64), index=True)


    def __repr__(self):
        if self.data_conclusao:
            data = self.data_conclusao
        else:
            data = self.data_abertura

        return '<Manutenção: %d [%s %d] em %s>' % (self.num_ordem_servico, 
            self.equipamento.tipo_equipamento, self.equipamento.tombamento,
            data.strftime("%d.%m.%Y"))

    def __str__(self):
        if self.data_conclusao:
            data = self.data_conclusao
        else:
            data = self.data_abertura

        return '%d [%s %d] em %s' % (self.num_ordem_servico, 
            self.equipamento.tipo_equipamento, self.equipamento.tombamento,
            data.strftime("%d.%m.%Y"))

