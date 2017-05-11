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


# Permissões são definidas com um byte, tendo um dos bits igual a 1 e
# os outros iguais a zero. O nível da permissão é baseado na posição do
# seu bit igual a 1, e aumenta da direita para a esquerda.
# A permissão de "ADMINISTRAR" é especial e tem todos os bits iguais a 1.

class Permissao:
    VISUALIZAR = 0x01
    CADASTRAR = 0x02
    ADMINISTRAR = 0xff


########## Modelos de Acesso ao Sistema ##########


# Cargos (Tipos de Usuários)
class Cargo(db.Model):
    # Nome da tabela no banco de dados
    __tablename__ = 'cargos'

    # Nome formatado no singular e plural (para eventual exibição)
    nome_formatado_singular = 'Cargo'
    nome_formatado_plural = 'Cargos'

    # Endpoint a ser utilizado no painel de administração
    endpoint = 'cargo'

    ### Colunas ###

    # ID na tabela
    id = db.Column(db.Integer, primary_key=True)

    # Nome
    nome = db.Column(db.String(36), index=True, unique=True, nullable=False)

    # Permissões dos usuários do cargo (interpretado como um byte, em que cada
    # bit representa uma permissão, e o estado do bit indica se o usuário tem (1) ou
    # não (0) tal permissão)
    permissoes = db.Column(db.Integer, nullable=False)

    # Identifica se o cargo é o padrão
    padrao = db.Column(db.Boolean, default=False, index=True, nullable=False)
    
    # Relação de usuários que possuem o cargo    
    usuarios = db.relationship('Usuario', backref='cargo', lazy='dynamic')

    ### Métodos ###

    # Adicionar os cargos no banco de dados
    @staticmethod
    def criar_cargos():
        # Definição dos cargos e suas permissões
        cargos = {
            u'Usuário': (Permissao.VISUALIZAR, True),
            u'Cadastrador': (Permissao.CADASTRAR | Permissao.VISUALIZAR, False),
            u'Desenvolvedor': (Permissao.ADMINISTRAR, False),
            u'Administrador': (Permissao.ADMINISTRAR, False)
        }

        # Criação dos cargos
        for nome_cargo in cargos:
            cargo = Cargo.query.filter_by(nome=nome_cargo).first()

            if cargo is None:
                cargo = Cargo(nome=nome_cargo)
                cargo.permissoes = cargos[nome_cargo][0]
                cargo.padrao = cargos[nome_cargo][1]
                db.session.add(cargo)

        # Salvando no banco de dados
        db.session.commit()

    # Representação no shell
    def __repr__(self):
        return '<Cargo: %s>' % self.nome

    # Representação na interface
    def __str__(self):
        return self.nome


# Usuários
class Usuario(UserMixin, db.Model):
    # Nome da tabela no banco de dados
    __tablename__ = 'usuarios'

    # Nome formatado no singular e plural (para eventual exibição)
    nome_formatado_singular = 'Usuário'
    nome_formatado_plural = 'Usuários'

    # Endpoint a ser utilizado no painel de administração
    endpoint = 'usuario'

    ### Colunas ###

    # ID na tabela
    id = db.Column(db.Integer, primary_key=True)

    # Nome
    nome = db.Column(db.String(64), index=True, nullable=False)

    # Email
    email = db.Column(db.String(64), index=True, unique=True, nullable=False)

    # Hash da senha (a senha original não é armazenada)
    senha_hash = db.Column(db.String(128))

    # Indica se o usuário foi verificado pelos administradores
    verificado = db.Column(db.Boolean, default=False)

    # Indica se o usuário confirmou se email
    confirmado = db.Column(db.Boolean, default=False)

    # Cargo do usuário
    id_cargo = db.Column(db.Integer, db.ForeignKey('cargos.id'))

    # Unidades pelas quais o usuário é responsável (parte do consumo)
    id_unidade_responsavel = db.Column(db.Integer,
                                       db.ForeignKey('unidadesresponsaveis.id'))


    ### Métodos ###

    # Inicialização
    def __init__(self, **kwargs):
        super(Usuario, self).__init__(**kwargs)
        
        # Definindo dados padrão para novos usuários
        if self.cargo is None:
            self.cargo = Cargo.query.filter_by(padrao=True).first()
            self.verificado = False
            self.confirmado = False
                
    # Criar o primeiro administrador, caso ainda não haja um
    @staticmethod
    def criar_administrador():
        if not Usuario.query.join(Cargo).filter(Cargo.nome=='Administrador').first():
            # Definição dos dados (alguns obtidos em variáveis de ambiente)
            administrador = Usuario(email=current_app.config['ADMIN_EMAIL'])
            administrador.nome = 'Administrador'
            administrador.senha = current_app.config['ADMIN_SENHA']
            administrador.verificado = True
            administrador.confirmado = True
            administrador.cargo = Cargo.query.filter_by(nome='Administrador').first()

            # Salvando no banco de dados
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

    # Testa se a senha é correta a partir do hash armazenado
    def verificar_senha(self, senha):
        return check_password_hash(self.senha_hash, senha)

    # Gera token para confirmação de nova conta
    def gerar_token_confirmacao(self, validade=3600):
        s = Serializer(current_app.config['SECRET_KEY'], validade)

        return s.dumps({'confirmar': self.id})

    # Confirma nova conta se o token recebido for correto
    def confirmar_conta(self, token):
        s = Serializer(current_app.config['SECRET_KEY'])

        # Testar se o token é válido
        try:
            data = s.loads(token)
        except:
            return False

        # Testar se o token corresponde ao usuário correto
        if data.get('confirmar') != self.id:
            return False

        # Confirmar usuário
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

        # Testar se o token é válido
        try:
            data = s.loads(token)
        except:
            return False

        # Testar se o token corresponde ao usuário correto
        if data.get('confirmar') != self.id:
            return False

        # Atualizar senha
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

        # Testar se o token é válido
        try:
            data = s.loads(token)
        except:
            return False

        # Testar se o token corresponde ao usuário correto
        if data.get('alterar_email') != self.id:
            return False

        # Obter novo email armazenado no token
        email_novo = data.get('email_novo')
        
        # Testar se o novo email foi fornecido
        if email_novo is None:
            return False

        # Testar se o email novo é igual ao antigo
        if self.query.filter_by(email=email_novo).first():
            return False

        # Atualizar email
        self.email = email_novo
        db.session.add(self)

        return True

    # Testa se o usuário tem determinadas permissões
    def autorizado(self, permissoes):
        # Uma operação AND (bitwise) é realizada com as permissões do usuário
        # e as permissões sendo testadas. Se os bits das permissões testadas forem 
        # 1 nas permissões do usuário, então ele tem estas permissões

        return self.cargo is not None and \
            (self.cargo.permissoes & permissoes) == permissoes

    # Testa se o usuário tem permissão para administrar
    def pode_administrar(self):
        return self.autorizado(Permissao.ADMINISTRAR)

    # Testa se o usuário tem permissão para cadastrar
    def pode_cadastrar(self):
        return self.autorizado(Permissao.CADASTRAR)

    # Testa se o usuário tem permissão para visualizar
    def pode_visualizar(self):
        return self.autorizado(Permissao.VISUALIZAR)

    # Gera lista de administradores
    @staticmethod
    def listar_administradores():
        return Usuario.query.join(Cargo).filter(Cargo.nome=='Administrador').all()

    # Gera lista de desenvolvedores
    @staticmethod
    def listar_desenvolvedores():
        return Usuario.query.join(Cargo).filter(Cargo.nome=='Desenvolvedor').all()

    # Representação no shell
    def __repr__(self):
        return '<Usuário: %s [%s]>' % (self.nome, self.cargo.nome)

    # Representação na interface
    def __str__(self):
        return self.nome


# Usuário Anônimo
class UsuarioAnonimo(AnonymousUserMixin):
    # Tipo de usuário auxiliar utilizado pelo Flask-Login para identificar
    # usuários que não estão logados no sistema

    # Nenhuma permissão
    def autorizado(self, permissoes):
        return False

    def pode_visualizar(self):
        return False

    def pode_cadastrar(self):
        return False

    def pode_administrar(self):
        return False

    ####################################
    def cadastrador(self):
        return False

    def administrador(self):
        return False
    ####################################


########## Configurações Adicionais do Flask-Login ##########


# Definir usuário anônimo
login_manager.anonymous_user = UsuarioAnonimo

# Função para que o sistema de login possa carregar um usuário
@login_manager.user_loader
def load_user(id_usuario):
    return Usuario.query.get(int(id_usuario))


########## Modelos do Sistema ##########


# Instituição (Topo da Hierarquia)
class Instituicao(db.Model):
    # Nome da tabela no banco de dados
    __tablename__ = 'instituicoes'

    # Nome formatado no singular e plural (para eventual exibição)
    nome_formatado_singular = 'Instituição'
    nome_formatado_plural = 'Instituições'

    # Endpoint a ser utilizado no painel de administração
    endpoint = 'instituicao'

    ### Colunas ###

    # ID na tabela
    id = db.Column(db.Integer, primary_key=True)

    # Nome
    nome = db.Column(db.String(64), index=True, unique=True, nullable=False)

    # Relação dos campi da instituição
    campi = db.relationship('Campus', backref='instituicao', lazy='dynamic')

    ### Métodos ###

    # Representação no shell
    def __repr__(self):
        return '<Instituição: %s>' % self.nome

    # Representação na interface
    def __str__(self):
        return self.nome


# Campi
class Campus(db.Model):
    # Nome da tabela no banco de dados
    __tablename__ = 'campi'

    # Nome formatado no singular e plural (para eventual exibição)
    nome_formatado_singular = 'Campus'
    nome_formatado_plural = 'Campi'

    # Endpoint a ser utilizado no painel de administração
    endpoint = 'campus'

    ### Colunas ###

    # ID na tabela
    id = db.Column(db.Integer, primary_key=True)

    # Nome
    nome = db.Column(db.String(64), index=True, unique=True, nullable=False)

    # Instituição do campus
    id_instituicao = db.Column(db.Integer, db.ForeignKey('instituicoes.id'))

    # Mapeamento do campus (seleção da área no mapa)
    mapeamento = db.Column(Geometry("MULTIPOLYGON"), unique=True)

    # Relação de centros do campus
    centros = db.relationship('Centro', backref='campus', lazy='dynamic')

    ### Métodos ###

    # Representação no shell
    def __repr__(self):
        return '<Campus: %s [%s]>' % (self.nome, self.instituicao.nome)

    # Representação na interface
    def __str__(self):
        return self.nome


# Centros
class Centro(db.Model):
    # Nome da tabela no banco de dados
    __tablename__ = 'centros'

    # Nome formatado no singular e plural (para eventual exibição)
    nome_formatado_singular = 'Centro'
    nome_formatado_plural = 'Centros'

    # Endpoint a ser utilizado no painel de administração
    endpoint = 'centro'

    ### Colunas ###

    # ID na tabela
    id = db.Column(db.Integer, primary_key=True)

    # Nome
    nome = db.Column(db.String(64), index=True, nullable=False)

    # Campus do qual o centro faz parte
    id_campus = db.Column(db.Integer, db.ForeignKey('campi.id'))

    # Mapeamento do centro (seleção da área no mapa)
    mapeamento = db.Column(Geometry("MULTIPOLYGON"), unique=True)

    # Relação de departamentos do centro
    departamentos = db.relationship('Departamento', backref='centro', lazy='dynamic')

    ### Métodos ###

    # Representação no shell
    def __repr__(self):
        return '<Centro: %s [%s]>' % (self.nome, self.campus.nome)

    # Representação na interface
    def __str__(self):
        return '%s [%s]' % (self.nome, self.campus.nome)


# Departamentos
class Departamento(db.Model):
    # Nome da tabela no banco de dados
    __tablename__ = 'departamentos'

    # Nome formatado no singular e plural (para eventual exibição)
    nome_formatado_singular = 'Departamento'
    nome_formatado_plural = 'Departamentos'

    # Endpoint a ser utilizado no painel de administração
    endpoint = 'departamento'

    ### Colunas ###

    # ID na tabela
    id = db.Column(db.Integer, primary_key=True)

    # Nome
    nome = db.Column(db.String(64), index=True, nullable=False)

    # Centro do qual o departamento é parte
    id_centro = db.Column(db.Integer, db.ForeignKey('centros.id'))

    # Relação de blocos do departamento
    blocos = db.relationship('Bloco', backref='departamento', lazy='dynamic')

    ### Métodos ###

    # Representação no shell
    def __repr__(self):
        return '<Departamento: %s [%s - %s]>' % \
            (self.nome, self.centro.nome, self.centro.campus.nome)

    # Representação na interface
    def __str__(self):
        return '%s [%s - %s]' % \
            (self.nome, self.centro.nome, self.centro.campus.nome)


# Blocos
class Bloco(db.Model):
    # Nome da tabela no banco de dados
    __tablename__ = 'blocos'

    # Nome formatado no singular e plural (para eventual exibição)
    nome_formatado_singular = 'Bloco'
    nome_formatado_plural = 'Blocos'

    # Endpoint a ser utilizado no painel de administração
    endpoint = 'bloco'

    ### Colunas ###

    # ID na tabela
    id = db.Column(db.Integer, primary_key=True)

    # Nome
    nome = db.Column(db.String(64), index=True, nullable=False)

    # Georeferenciamento do bloco (marcador no mapa)
    localizacao = db.Column(Geometry("POINT"), unique=True)

    # Departamento do qual o bloco faz parte
    id_departamento = db.Column(db.Integer, db.ForeignKey('departamentos.id'))

    # Relação de ambientes do bloco
    ambientes = db.relationship('Ambiente', backref='bloco', lazy='dynamic')   

    ### Métodos ###

    # Representação no shell
    def __repr__(self):
        return '<Bloco: %s [%s - %s - %s]>' % \
            (self.nome, self.departamento.nome, self.departamento.centro.nome,
             self.departamento.centro.campus.nome)

    # Representação na interface
    def __str__(self):
        return '%s [%s - %s - %s]' % \
            (self.nome, self.departamento.nome, self.departamento.centro.nome,
             self.departamento.centro.campus.nome)


# Ambientes
class Ambiente(db.Model):
    # Nome da tabela no banco de dados
    __tablename__ = 'ambientes'

    # Nome formatado no singular e plural (para eventual exibição)
    nome_formatado_singular = 'Ambiente'
    nome_formatado_plural = 'Ambientes'

    # Endpoint a ser utilizado no painel de administração
    endpoint = 'ambiente'

    ### Colunas ###

    # ID na tabela
    id = db.Column(db.Integer, primary_key=True)

    # Nome
    nome = db.Column(db.String(64), index=True, nullable=False)

    # Tipo de ambiente (interno, externo, subestação abrigada, subestação aérea, ...)
    tipo = db.Column(db.String(64), index=True)

    # Bloco do qual este ambiente faz parte
    id_bloco = db.Column(db.Integer, db.ForeignKey('blocos.id'))

    # Detalhes sobre a localização do ambiente
    detalhe_localizacao = db.Column(db.Text)

    # Relação de equipamentos do ambiente
    equipamentos = db.relationship('Equipamento', backref='ambiente', lazy='dynamic')

    # Como Ambiente é uma superclasse de cada tipo específico de ambiente,
    # (interno, externo, ...), é necessário explicitar essa relação para o banco de
    # dados. Isso é feito através do dicionário __mapper_args__, em que:
    # polymorphic_identity - Identificação da classe
    # polymorphic_on - Coluna da tabela que contém a identificação da classe

    __mapper_args__ = {
        'polymorphic_identity': u'Ambiente',    # Deve ser a versão formatada do endpoint!
        'polymorphic_on': tipo
    }

    ### Métodos ###

    # Representação no shell
    def __repr__(self):
        return '<Ambiente: %s [%s - %s - %s - %s]>' % \
            (self.nome, self.bloco.nome, self.bloco.departamento.nome,
             self.bloco.departamento.centro.nome, self.departamento.centro.campus.nome)

    # Representação na interface
    def __str__(self):
        return '%s [%s - %s - %s - %s]' % \
            (self.nome, self.bloco.nome, self.bloco.departamento.nome,
             self.bloco.departamento.centro.nome,
             self.departamento.centro.campus.nome)


# Ambientes Internos (Subclasse de Ambiente)
class AmbienteInterno(Ambiente):
    # Nome da tabela no banco de dados
    __tablename__ = 'ambientes_internos'

    # Nome formatado no singular e plural (para eventual exibição)
    nome_formatado_singular = 'Ambiente Interno'
    nome_formatado_plural = 'Ambientes Internos'

    # Endpoint a ser utilizado no painel de administração
    endpoint = 'ambienteinterno'

    ### Colunas ###

    # ID na tabela
    id = db.Column(db.Integer, db.ForeignKey('ambientes.id'), primary_key=True)

    # Andar do ambiente no bloco
    andar = db.Column(db.String(15))

    # Área do ambiente [m²]
    area = db.Column(db.Float)

    # Quantidade normal de pessoas no ambiente
    populacao = db.Column(db.Integer)

    # AmbienteInterno é uma subclasse de Ambiente, portanto, esta relação
    # deve ser explicitada para o banco de dados através do dicionário
    # __mapper_args__.
    # Apenas 'polymorphic_identity' precisa ser definida, pois já foi
    # definido na superclasse que a coluna da identidade é 'tipo'.
    # Deve ser a versão formatada do endpoint!

    __mapper_args__ = { 'polymorphic_identity': u'Ambiente Interno' }

    ### Métodos ###

    # Inicialização
    def __init__(self, **kwargs):
        super(AmbienteInterno, self).__init__(**kwargs)

        # Definição do tipo do ambiente (constante)
        # Deve ser o mesmo que o que foi definido em 'polymorphic_identity'!
        self.tipo = 'Ambiente Interno'

    # Representação no shell
    def __repr__(self):
        return '<Ambiente Interno: %s [%s - %s - %s - %s]>' % \
            (self.nome, self.bloco.nome, self.bloco.departamento.nome,
             self.bloco.departamento.centro.nome,
             self.bloco.departamento.centro.campus.nome)

    # Representação na interface
    def __str__(self):
        return '%s [%s - %s - %s - %s]' % \
            (self.nome, self.bloco.nome, self.bloco.departamento.nome,
             self.bloco.departamento.centro.nome,
             self.bloco.departamento.centro.campus.nome)


# Ambientes Externos (Subclasse de Ambiente)
class AmbienteExterno(Ambiente):
    # Nome da tabela no banco de dados
    __tablename__ = 'ambientes_externos'

    # Nome formatado no singular e plural (para eventual exibição)
    nome_formatado_singular = 'Ambiente Externo'
    nome_formatado_plural = 'Ambientes Externos'

    # Endpoint a ser utilizado no painel de administração
    endpoint = 'ambienteexterno'

    ### Colunas ###

    # ID na tabela
    id = db.Column(db.Integer, db.ForeignKey('ambientes.id'), primary_key=True)

    # AmbienteExterno é uma subclasse de Ambiente, portanto, esta relação
    # deve ser explicitada para o banco de dados através do dicionário
    # __mapper_args__.
    # Apenas 'polymorphic_identity' precisa ser definida, pois já foi
    # definido na superclasse que a coluna da identidade é 'tipo'.
    # Deve ser a versão formatada do endpoint!

    __mapper_args__ = { 'polymorphic_identity': u'Ambiente Externo' }

    ### Métodos ###

    # Inicialização
    def __init__(self, **kwargs):
        super(AmbienteExterno, self).__init__(**kwargs)

        # Definição do tipo do ambiente (constante)
        # Deve ser o mesmo que o que foi definido em 'polymorphic_identity'!
        self.tipo = 'Ambiente Externo'

    # Representação no shell
    def __repr__(self):
        return '<Ambiente Externo: %s [%s - %s - %s - %s]>' % \
            (self.nome, self.bloco.nome, self.bloco.departamento.nome,
             self.bloco.departamento.centro.nome,
             self.bloco.departamento.centro.campus.nome)

    # Representação na interface
    def __str__(self):
        return '%s [%s - %s - %s - %s]' % \
            (self.nome, self.bloco.nome, self.bloco.departamento.nome,
             self.bloco.departamento.centro.nome,
             self.bloco.departamento.centro.campus.nome)


# Subestações Abrigadas (Subclasse de Ambiente)
class SubestacaoAbrigada(Ambiente):
    # Nome da tabela no banco de dados
    __tablename__ = 'subestacoes_abrigadas'

    # Nome formatado no singular e plural (para eventual exibição)
    nome_formatado_singular = 'Subestação Abrigada'
    nome_formatado_plural = 'Subestações Abrigadas'

    # Endpoint a ser utilizado no painel de administração
    endpoint = 'subestacaoabrigada'

    ### Colunas ###

    # ID na tabela
    id = db.Column(db.Integer, db.ForeignKey('ambientes.id'), primary_key=True)

    # Georeferenciamento do bloco (marcador no mapa)
    localizacao = db.Column(Geometry("POINT"), unique=True)

    # SubestacaoAbrigada é uma subclasse de Ambiente, portanto, esta relação
    # deve ser explicitada para o banco de dados através do dicionário
    # __mapper_args__.
    # Apenas 'polymorphic_identity' precisa ser definida, pois já foi
    # definido na superclasse que a coluna da identidade é 'tipo'.
    # Deve ser a versão formatada do endpoint!

    __mapper_args__ = { 'polymorphic_identity': u'Subestação Abrigada' }

    ### Métodos ###

    # Inicialização
    def __init__(self, **kwargs):
        super(SubestacaoAbrigada, self).__init__(**kwargs)

        # Definição do tipo do ambiente (constante)
        # Deve ser o mesmo que o que foi definido em 'polymorphic_identity'!
        self.tipo = 'Subestação Abrigada'

    # Representação no shell
    def __repr__(self):
        return '<Subestação Abrigada: %s [%s]>' % \
            (self.nome, self.bloco.departamento.centro.campus.nome)

    # Representação na interface
    def __str__(self):
        return '%s [%s]' % \
            (self.nome, self.bloco.departamento.centro.campus.nome)


# Subestações Aéreas (Subclasse de Ambiente)
class SubestacaoAerea(Ambiente):
    # Nome da tabela no banco de dados
    __tablename__ = 'subestacoes_aereas'
    
    # Nome formatado no singular e plural (para eventual exibição)
    nome_formatado_singular = 'Subestação Aérea'
    nome_formatado_plural = 'Subestações Aéreas'

    # Endpoint a ser utilizado no painel de administração
    endpoint = 'subestacaoaerea'

    ### Colunas ###

    # ID na tabela
    id = db.Column(db.Integer, db.ForeignKey('ambientes.id'), primary_key=True)

    # Georeferenciamento do bloco (marcador no mapa)
    localizacao = db.Column(Geometry("POINT"), unique=True)

    # SubestacaoAerea é uma subclasse de Ambiente, portanto, esta relação
    # deve ser explicitada para o banco de dados através do dicionário
    # __mapper_args__.
    # Apenas 'polymorphic_identity' precisa ser definida, pois já foi
    # definido na superclasse que a coluna da identidade é 'tipo'.
    # Deve ser a versão formatada do endpoint!

    __mapper_args__ = { 'polymorphic_identity': u'Subestação Aérea' }

    ### Métodos ###

    # Inicialização
    def __init__(self, **kwargs):
        super(SubestacaoAerea, self).__init__(**kwargs)

        # Definição do tipo do ambiente (constante)
        # Deve ser o mesmo que o que foi definido em 'polymorphic_identity'!        
        self.tipo = 'Subestação Aérea'

    # Representação no shell
    def __repr__(self):
        return '<Subestação Aérea: %s [%s]>' % \
            (self.nome, self.bloco.departamento.centro.campus.nome)

    # Representação na interface
    def __str__(self):
        return '%s [%s]' % \
            (self.nome, self.bloco.departamento.centro.campus.nome)


# Equipamentos
class Equipamento(db.Model):
    # Nome da tabela no banco de dados
    __tablename__ = 'equipamentos'

    # Nome formatado no singular e plural (para eventual exibição)
    nome_formatado_singular = 'Equipamento'
    nome_formatado_plural = 'Equipamentos'

    # Endpoint a ser utilizado no painel de administração
    endpoint = 'equipamento'

    ### Colunas ###

    # ID na tabela
    id = db.Column(db.Integer, primary_key=True)

    # Tombamento (etiqueta da divisão de patrimônio)
    tombamento = db.Column(db.Integer)

    # Ambiente em que o equipamento se encontra
    id_ambiente = db.Column(db.Integer, db.ForeignKey('ambientes.id'))

    # Categoria do equipamento (elétrico, combate a incêndio, ...)
    categoria_equipamento = db.Column(db.String(64), index=True)

    # Tipo de equipamento (extintor, condicionador de ar, ...)
    tipo_equipamento = db.Column(db.String(64), index=True)

    # Fabricante (ou marca)
    fabricante = db.Column(db.String(64), index=True)

    # Intervalo entre manutenções preventivas [meses]
    intervalo_manutencao = db.Column(db.Integer)

    # Relação de manutenções realizadas no equipamento
    manutencoes = db.relationship('Manutencao', backref='equipamento', lazy='dynamic')

    # Data da próxima manutenção preventiva [dd.mm.aaaa]
    # Calculada com base na última manutenção e no intervalo entre manutenções
    proxima_manutencao = db.Column(db.Date, index=True)

    # Informações adicionais sobre o equipamento
    info_adicional = db.Column(db.Text)

    # Indica se o equipamento está em uso
    em_uso = db.Column(db.Boolean, default=True, index=True)

    # Indica se existe uma manutenção aberta para o equipamento
    em_manutencao = db.Column(db.Boolean, default=False, index=True)

    # Data de início da manutenção aberta atual, caso haja [dd.mm.aaaa]
    inicio_manutencao = db.Column(db.Date, index=True)

    # Como Equipamento é uma superclasse de cada tipo específico de equipamento
    # (extintor, condicionador de ar, ...), é necessário explicitar essa relação 
    # para o banco de dados.
    # Isso é feito através do dicionário __mapper_args__, em que:
    # polymorphic_identity - Identificação da classe
    # polymorphic_on - Coluna da tabela que contém a identificação da classe

    __mapper_args__ = {
        'polymorphic_identity': u'Equipamento', # Deve ser a versão formatada do endpoint!
        'polymorphic_on': tipo_equipamento
    }

    ### Métodos ###

    # Representação no shell
    def __repr__(self):
        return '<%s: %d [%s]>' % \
            (self.tipo_equipamento, self.tombamento, self.ambiente)

    # Representação na interface
    def __str__(self):
        return '%s %d [%s]' % \
            (self.tipo_equipamento, self.tombamento, self.ambiente)


# Extintores (Subclasse de Equipamento)
class Extintor(Equipamento):
    # Nome da tabela no banco de dados
    __tablename__ = 'extintores'
    
    # Nome formatado no singular e plural (para eventual exibição)
    nome_formatado_singular = 'Extintor'
    nome_formatado_plural = 'Extintores'

    # Endpoint a ser utilizado no painel de administração
    endpoint = 'extintor'

    ### Colunas ###

    # ID na tabela
    id = db.Column(db.Integer, db.ForeignKey('equipamentos.id'), primary_key=True)

    # Classificação do extintor (agente extintor e classe de fogo)
    classificacao = db.Column(db.String(64))

    # Carga nominal do extintor [kg]
    carga_nominal = db.Column(db.Float)

    # Extintor é uma subclasse de Equipamento, portanto, esta relação
    # deve ser explicitada para o banco de dados através do dicionário
    # __mapper_args__.
    # Apenas 'polymorphic_identity' precisa ser definida, pois já foi
    # definido na superclasse que a coluna da identidade é 'tipo_equipamento'.
    # Deve ser a versão formatada do endpoint!

    __mapper_args__ = { 'polymorphic_identity': u'Extintor' }

    ### Métodos ###

    # Inicialização
    def __init__(self, **kwargs):
        super(Extintor, self).__init__(**kwargs)

        # Definição do tipo de equipamento (constante)
        # Deve ser o mesmo que o que foi definido em 'polymorphic_identity'!
        self.tipo_equipamento = 'Extintor'

        # Definição da categoria do equipamento (constante)
        self.categoria_equipamento = 'Combate a Incêndio'


# Condicionadores de Ar (Subclasse de Equipamento)
class CondicionadorAr(Equipamento):
    # Nome da tabela no banco de dados
    __tablename__ = 'condicionadores_ar'

    # Nome formatado no singular e plural (para eventual exibição)
    nome_formatado_singular = 'Condicionador de Ar'
    nome_formatado_plural = 'Condicionadores de Ar'

    # Endpoint a ser utilizado no painel de administração
    endpoint = 'condicionadordear'

    ### Colunas ###

    # ID na tabela
    id = db.Column(db.Integer, db.ForeignKey('equipamentos.id'), primary_key=True)

    # Classificação (Janela, split, teto aparente, piso aparente, ...)
    classificacao = db.Column(db.String(64))

    # Potência nominal de entrada [W] (Valor inteiro)
    pot_nominal = db.Column(db.Integer)

    # Capacidade de refrigeração [Btu/h] (Valor inteiro)
    cap_refrigeracao = db.Column(db.Integer)

    # Tensão de alimentação [V] (110, 220, 380)
    tensao_alimentacao = db.Column(db.Integer)

    # Eficiência do equipamento (Selo Procel - A, B, C, D, E, F, G)
    eficiencia = db.Column(db.String(1))


    # CondicionadorAr é uma subclasse de Equipamento, portanto, esta relação
    # deve ser explicitada para o banco de dados através do dicionário
    # __mapper_args__.
    # Apenas 'polymorphic_identity' precisa ser definida, pois já foi
    # definido na superclasse que a coluna da identidade é 'tipo_equipamento'.
    # Deve ser a versão formatada do endpoint!

    __mapper_args__ = { 'polymorphic_identity': u'Condicionador de Ar' }

    ### Métodos ###

    # Inicialização
    def __init__(self, **kwargs):
        super(CondicionadorAr, self).__init__(**kwargs)

        # Definição do tipo de equipamento (constante)
        # Deve ser o mesmo que o que foi definido em 'polymorphic_identity'!
        self.tipo_equipamento = 'Condicionador de Ar'

        # Definição da categoria do equipamento (constante)
        self.categoria_equipamento = 'Equipamento Elétrico'


# Manutenções
class Manutencao(db.Model):
    # Nome da tabela no banco de dados
    __tablename__ = 'manutencoes'

    # Nome formatado no singular e plural (para eventual exibição)
    nome_formatado_singular = 'Manutenção'
    nome_formatado_plural = 'Manutenções'

    # Endpoint a ser utilizado no painel de administração
    endpoint = 'manutencao'

    ### Colunas ###

    # ID na tabela
    id = db.Column(db.Integer, primary_key=True)

    # Número da ordem de serviço (0, caso não haja)
    num_ordem_servico = db.Column(db.Integer, nullable=False)

    # Equipamento em que a manutenção foi realizada
    id_equipamento = db.Column(db.Integer, db.ForeignKey('equipamentos.id'))

    # Data de abertura da manutenção [dd.mm.aaaa]
    data_abertura = db.Column(db.Date, index=True, nullable=False)

    # Data de conclusão da manutenção [dd.mm.aaaa]
    data_conclusao = db.Column(db.Date, index=True)

    # Tipo de manutenção (inicial, preventiva, corretiva, troca)
    tipo_manutencao = db.Column(db.String(64), index=True)

    # Descrição do serviço realizado
    descricao_servico = db.Column(db.Text)

    # Status da manutenção (aberta, concluída)
    status = db.Column(db.String(64), index=True)

    ### Métodos ###

    # Representação no shell
    def __repr__(self):
        # Caso a manutenção esteja aberta, mostrar data de abertura,
        # caso contrário, mostrar data de conclusão
        if self.data_conclusao:
            data = self.data_conclusao
            str_status = 'concluída'
        else:
            data = self.data_abertura
            str_status = 'aberta'

        return '<Manutenção: %d [%s %d] %s em %s>' % (self.num_ordem_servico, 
            self.equipamento.tipo_equipamento, self.equipamento.tombamento,
            str_status, data.strftime("%d.%m.%Y"))

    # Representação na interface
    def __str__(self):
        # Caso a manutenção esteja aberta, mostrar data de abertura,
        # caso contrário, mostrar data de conclusão
        if self.data_conclusao:
            data = self.data_conclusao
            str_status = 'concluída'
        else:
            data = self.data_abertura
            str_status = 'aberta'

        return '%d [%s %d] %s em %s' % (self.num_ordem_servico, 
            self.equipamento.tipo_equipamento, self.equipamento.tombamento,
            str_status, data.strftime("%d.%m.%Y"))

########## Modelos para a parte de Consumo ##########

# Unidade Responsável (Topo da Hierarquia)
class UnidadeResponsavel(db.Model):
    # Nome da tabela no banco de dados
    __tablename__ = 'unidadesresponsaveis'

    # Nome formatado no singular e plural (para eventual exibição)
    nome_formatado_singular = 'Unidade Responsável'
    nome_formatado_plural = 'Unidades Responsáveis'

    # Endpoint a ser utilizado no painel de administração
    endpoint = 'unidaderesponsavel'

    ### Colunas ###

    # ID na tabela
    id = db.Column(db.Integer, primary_key=True)

    # Nome
    nome = db.Column(db.String(64), index=True, unique=True, nullable=False)

    # Relação de responsáveis pela unidade
    responsaveis = db.relationship('Usuario', backref='responsavel_unidade',
                                   lazy='dynamic')

    # Relação de unidades consumidoras
    unidades_consumidoras = db.relationship('UnidadeConsumidora',
                                            backref='unidade_responsavel',
                                            lazy='dynamic')

    ### Métodos ###

    # Representação no shell
    def __repr__(self):
        return '<Unidade Responsável: %s>' % self.nome

    # Representação na interface
    def __str__(self):
        return self.nome


# Unidade Consumidora
class UnidadeConsumidora(db.Model):
    # Nome da tabela no banco de dados
    __tablename__ = 'unidadesconsumidoras'

    # Nome formatado no singular e plural (para eventual exibição)
    nome_formatado_singular = 'Unidade Consumidora'
    nome_formatado_plural = 'Unidades Consumidoras'

    # Endpoint a ser utilizado no painel de administração
    endpoint = 'unidadeconsumidora'

    ### Colunas ###

    # ID na tabela
    id = db.Column(db.Integer, primary_key=True)

    # Nome
    nome = db.Column(db.String(64), index=True, unique=True, nullable=False)

    # Unidade responsável pela unidade consumidora
    id_unidade_responsavel = db.Column(db.Integer,
                                       db.ForeignKey('unidadesresponsaveis.id'))

    # Georeferenciamento (marcador no mapa)
    localizacao = db.Column(Geometry("POINT"))

    # Número do cliente
    num_cliente = db.Column(db.Integer, unique=True, nullable=False)

    # Endereço
    endereco = db.Column(db.String(300))

    # Modalidade tarifária
    mod_tarifaria = db.Column(db.String(64), nullable=False)

    # Números dos medidores
    num_medidores = db.Column(db.Integer, unique=True, nullable=False)

    # Relação de contas de energia da unidade consumidora
    hist_contas = db.relationship('Conta', backref='unidade_consumidora',
                                  lazy='dynamic')

    ### Métodos ###

    # Representação no shell
    def __repr__(self):
        return '<Unidade Consumidora: %s [%s]>' % \
                (self.nome, self.unidade_responsavel.nome)

    # Representação na interface
    def __str__(self):
        return self.nome


# Conta de Energia
class Conta(db.Model):
    # Nome da tabela no banco de dados
    __tablename__ = 'contas'

    # Nome formatado no singular e plural (para eventual exibição)
    nome_formatado_singular = 'Conta'
    nome_formatado_plural = 'Contas'

    # Endpoint a ser utilizado no painel de administração
    endpoint = 'conta'

    ### Colunas ###

    # ID na tabela
    id = db.Column(db.Integer, primary_key=True)

    # Unidade consumidora
    id_unidade_consumidora = db.Column(db.Integer,
                                       db.ForeignKey('unidadesconsumidoras.id'))

    # Data da leitura [dd.mm.aaaa]
    data_leitura = db.Column(db.Date, index=True, nullable=False)

    # Consumo fora de ponta [kWh]
    cons_fora_ponta = db.Column(db.Integer, nullable=False)

    # Consumo hora ponta [kWh]
    cons_hora_ponta = db.Column(db.Integer, nullable=False)

    # Valor faturado de fora ponta [R$]
    valor_fora_ponta = db.Column(db.Float, nullable=False)

    # Valor faturado de hora ponta [R$]
    valor_hora_ponta = db.Column(db.Float, nullable=False)

    # Valor total da conta [R$]
    valor_total = db.Column(db.Float, nullable=False)


    ### Métodos ###

    # Representação no shell
    def __repr__(self):
        return '<Conta: %s [%s]>' % \
                (self.unidade_consumidora.nome, self.data_leitura.strftime("%d.%m.%Y"))

    # Representação na interface
    def __str__(self):
        return '%s [%s]' % \
                (self.unidade_consumidora.nome, self.data_leitura.strftime("%d.%m.%Y"))

