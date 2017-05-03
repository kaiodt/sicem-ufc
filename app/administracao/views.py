# coding: utf-8

################################################################################
## SICEM - UFC
################################################################################
## Views do Painel de Administração
################################################################################


from datetime import date, timedelta
from flask import url_for, redirect, request
from flask_login import current_user
from flask_admin import BaseView, expose
from flask_admin.contrib.geoa import ModelView

from . import admin, typefmt
from .. import db
from .forms import *
from .filters import *
from ..models import *
from ..util import email


########## View Base ##########


class ModelViewBase(ModelView):
    # Definição dos formatos de tipos de dados
    # (Alguns modificados no arquivo 'typefmt.py')
    column_type_formatters = typefmt.FORMATOS_PADRAO

    # Usar templates personalizados
    list_template = 'administracao/listar.html'         # View de listagem
    details_template = 'administracao/detalhes.html'    # View de detalhes
    edit_template = 'administracao/editar.html'         # View de edição
    create_template = 'administracao/criar.html'        # View de criação
    
    # Quantidade de itens exibidos por página
    page_size = 10

    # Habilitando outras permissões
    can_export = True           # Eportação dos dados
    can_view_details = True     # View de detalhes


########## Views Restritas ##########


# Somente Administradores
class ModelViewAdministrador(ModelViewBase):
    def is_accessible(self):
        return current_user.pode_administrar()


# Administradores e Cadastradores
class ModelViewCadastrador(ModelViewBase):
    def is_accessible(self):
        return current_user.pode_cadastrar()


########## Views dos Modelos do Sistema ##########


# Cargos (Somente administradores)
class ModelViewCargo(ModelViewAdministrador):
    # Desabilitar criação e exclusão
    can_create = False
    can_delete = False

    # Colunas exibidas na view de listagem (em ordem)
    # Caso a coluna seja uma referência a outro modelo, indicar que
    # coluna do modelo referenciado deve ser exibida usando notação de ponto
    column_list = ['nome', 'permissoes', 'padrao']

    # Coluna padrão usada para ordenar itens
    column_default_sort = 'nome'

    # Colunas que podem ser utilizadas para ordenar os itens
    column_sortable_list = ['nome', 'permissoes']

    # Colunas em que pode ser feita busca
    column_searchable_list = ['nome']

    # Colunas exibidas na view de detalhes (em ordem)
    column_details_list = ['nome', 'permissoes', 'padrao', 'usuarios']

    # Exibição dos nomes das colunas (necessário adicionar os acentos)
    # Colunas referenciadas de outros modelos devem ter seus nomes corrigidos
    column_labels = {'permissoes': 'Permissões',
                     'padrao': 'Padrão',
                     'usuarios': 'Usuários'}

    # Colunas que possuem um formato modificado (arquivo 'typefmt.py')
    column_formatters = dict(usuarios=typefmt.formato_relacao)
    
    # Definição dos formulários utilizados
    edit_form = FormEditarCargo


# Usuários (Somente administradores)
class ModelViewUsuario(ModelViewAdministrador):
    # Colunas exibidas na view de listagem (em ordem)
    # Caso a coluna seja uma referência a outro modelo, indicar que
    # coluna do modelo referenciado deve ser exibida usando notação de ponto
    column_list = ['nome', 'email', 'cargo.nome', 'verificado', 'confirmado']

    # Coluna padrão usada para ordenar itens
    column_default_sort = 'nome'

    # Colunas que podem ser utilizadas para ordenar os itens
    column_sortable_list = ['nome', 'cargo.nome']

    # Colunas em que pode ser feita busca
    column_searchable_list = ['nome', 'cargo.nome']

    # Colunas exibidas na view de detalhes (em ordem)
    column_details_list = ['nome', 'email', 'cargo.nome', 'verificado', 'confirmado']

    # Exibição dos nomes das colunas (necessário adicionar os acentos)
    # Colunas referenciadas de outros modelos devem ter seus nomes corrigidos
    column_labels = {'cargo.nome': 'Cargo'}

    # Lista de filtros que podem ser aplicados em cada coluna
    # Deve-se indicar a coluna e o nome de exibição do filtro
    # Note também que alguns tipos de dados possuem mais de um filtro ('filters.py')
    column_filters = FiltrosStrings(Cargo.nome, 'Cargo')
    column_filters.append(BooleanEqualFilter(Usuario.verificado, 'Verificado'))
    column_filters.append(BooleanEqualFilter(Usuario.confirmado, 'Confirmado'))

    # Definição dos formulários utilizados
    create_form = FormCriarUsuario
    edit_form = FormEditarUsuario


    # Procedimentos adicionais após criação
    def after_model_change(self, form, model, is_created):
        if is_created:
            # Verificar usuário
            model.verificado = True

            # Salvar no banco de dados
            db.session.add(model)
            db.session.commit()

            # Se o usuário não foi confirmado na criação, enviar email para
            # que este possa confirmar seu email
            if model.confirmado is False:
                email.enviar_email(model.email,
                                   'Confirme Seu Cadastro',
                                   'autenticacao/email/confirmacao',
                                   usuario=model,
                                   token=model.gerar_token_confirmacao())


##### Locais #####


# Instituições
class ModelViewInstituicao(ModelViewCadastrador):
    # Colunas exibidas na view de listagem (em ordem)
    # Caso a coluna seja uma referência a outro modelo, indicar que
    # coluna do modelo referenciado deve ser exibida usando notação de ponto
    column_list = ['nome']

    # Coluna padrão usada para ordenar itens
    column_default_sort = 'nome'

    # Colunas que podem ser utilizadas para ordenar os itens
    column_sortable_list = ['nome']

    # Colunas em que pode ser feita busca
    column_searchable_list = ['nome']

    # Colunas exibidas na view de detalhes (em ordem)
    column_details_list = ['nome', 'campi']

    # Colunas que possuem um formato modificado (arquivo 'typefmt.py')
    column_formatters = dict(campi=typefmt.formato_relacao)
    
    # Definição dos formulários utilizados
    create_form = FormCriarInstituicao
    edit_form = FormEditarInstituicao


# Campi
class ModelViewCampus(ModelViewCadastrador):
    # Colunas exibidas na view de listagem (em ordem)
    # Caso a coluna seja uma referência a outro modelo, indicar que
    # coluna do modelo referenciado deve ser exibida usando notação de ponto
    column_list = ['nome', 'instituicao.nome', 'mapeamento']

    # Coluna padrão usada para ordenar itens
    column_default_sort = 'nome'

    # Colunas que podem ser utilizadas para ordenar os itens
    column_sortable_list = ['nome', 'instituicao.nome']

    # Colunas em que pode ser feita busca
    column_searchable_list = ['nome', 'instituicao.nome']

    # Colunas exibidas na view de detalhes (em ordem)
    column_details_list = ['nome', 'instituicao.nome', 'mapeamento', 'centros']

    # Exibição dos nomes das colunas (necessário adicionar os acentos)
    # Colunas referenciadas de outros modelos devem ter seus nomes corrigidos
    column_labels = {'instituicao.nome': 'Instituição'}

    # Colunas que possuem um formato modificado (arquivo 'typefmt.py')
    column_formatters = dict(centros=typefmt.formato_relacao)

    # Definição dos formulários utilizados
    create_form = FormCriarCampus
    edit_form = FormEditarCampus


    # Após ciração do Campus, criar Centro, Departamento e Bloco especiais
    # para alocar suas subestações
    def after_model_change(self, form, model, is_created):
        # Testar se houve criação
        if is_created:
            # Criação do centro para subestações
            centro = Centro()
            centro.nome = 'Subestações ' + model.nome
            centro.campus = model

            db.session.add(centro)
            db.session.commit()

            # Criação do departamento para subestações
            departamento = Departamento()
            departamento.nome = 'Subestações ' + model.nome
            departamento.centro = centro

            db.session.add(departamento)
            db.session.commit()

            # Criação do bloco para subestações
            bloco = Bloco()
            bloco.nome = 'Subestações ' + model.nome
            bloco.departamento = departamento

            db.session.add(bloco)
            db.session.commit()


# Centros
class ModelViewCentro(ModelViewCadastrador):
    # Colunas exibidas na view de listagem (em ordem)
    # Caso a coluna seja uma referência a outro modelo, indicar que
    # coluna do modelo referenciado deve ser exibida usando notação de ponto
    column_list = ['nome', 'campus.nome', 'mapeamento']

    # Coluna padrão usada para ordenar itens
    column_default_sort = 'nome'

    # Colunas que podem ser utilizadas para ordenar os itens
    column_sortable_list = ['nome', 'campus.nome']

    # Colunas em que pode ser feita busca
    column_searchable_list = ['nome', 'campus.nome']

    # Colunas exibidas na view de detalhes (em ordem)
    column_details_list = ['nome', 'campus.nome', 'mapeamento', 'departamentos']   

    # Colunas que possuem um formato modificado (arquivo 'typefmt.py')
    column_formatters = dict(departamentos=typefmt.formato_relacao)

    # Exibição dos nomes das colunas (necessário adicionar os acentos)
    # Colunas referenciadas de outros modelos devem ter seus nomes corrigidos
    column_labels = {'campus.nome': 'Campus'}

    # Lista de filtros que podem ser aplicados em cada coluna
    # Deve-se indicar a coluna e o nome de exibição do filtro
    # Note também que alguns tipos de dados possuem mais de um filtro ('filters.py')    
    column_filters = FiltrosStrings(Campus.nome, 'Campus')

    # Definição dos formulários utilizados
    create_form = FormCriarCentro
    edit_form = FormEditarCentro


# Departamentos
class ModelViewDepartamento(ModelViewCadastrador):
    # Colunas exibidas na view de listagem (em ordem)
    # Caso a coluna seja uma referência a outro modelo, indicar que
    # coluna do modelo referenciado deve ser exibida usando notação de ponto
    column_list = ['nome', 'centro.nome', 'centro.campus.nome']

    # Coluna padrão usada para ordenar itens
    column_default_sort = 'nome'

    # Colunas que podem ser utilizadas para ordenar os itens
    column_sortable_list = ['nome', 'centro.nome', 'centro.campus.nome']

    # Colunas em que pode ser feita busca
    column_searchable_list = ['nome', 'centro.nome', 'centro.campus.nome']

    # Colunas exibidas na view de detalhes (em ordem)
    column_details_list = ['nome', 'centro.nome', 'centro.campus.nome', 'blocos'] 

    # Exibição dos nomes das colunas (necessário adicionar os acentos)
    # Colunas referenciadas de outros modelos devem ter seus nomes corrigidos
    column_labels = {'centro.nome': 'Centro',
                     'centro.campus.nome': 'Campus'}

    # Colunas que possuem um formato modificado (arquivo 'typefmt.py')
    column_formatters = dict(blocos=typefmt.formato_relacao)

    # Lista de filtros que podem ser aplicados em cada coluna
    # Deve-se indicar a coluna e o nome de exibição do filtro
    # Note também que alguns tipos de dados possuem mais de um filtro ('filters.py')
    column_filters = FiltrosStrings(Centro.nome, 'Centro')
    column_filters.extend(FiltrosStrings(Campus.nome, 'Campus'))

    # Definição dos formulários utilizados
    create_form = FormCriarDepartamento
    edit_form = FormEditarDepartamento


    # Inicialização
    def __init__(self, *args, **kwargs):
        super(ModelViewDepartamento, self).__init__(*args, **kwargs)

        # Consertar geração automática de joins para as queries dos filtros

        self._filter_joins[Campus.nome] = [Centro.__table__, Campus.__table__]


# Blocos
class ModelViewBloco(ModelViewCadastrador):
    # Colunas exibidas na view de listagem (em ordem)
    # Caso a coluna seja uma referência a outro modelo, indicar que
    # coluna do modelo referenciado deve ser exibida usando notação de ponto
    column_list = ['nome', 'departamento.nome', 'departamento.centro.nome',
                   'departamento.centro.campus.nome', 'localizacao']

    # Coluna padrão usada para ordenar itens
    column_default_sort = 'nome'

    # Colunas que podem ser utilizadas para ordenar os itens
    column_sortable_list = ['nome', 'departamento.nome',
                            'departamento.centro.nome',
                            'departamento.centro.campus.nome']

    # Colunas em que pode ser feita busca
    column_searchable_list = ['nome', 'departamento.nome', 'departamento.centro.nome', 
                              'departamento.centro.campus.nome']

    # Colunas exibidas na view de detalhes (em ordem)
    column_details_list = ['nome', 'departamento.nome', 'departamento.centro.nome',
                           'departamento.centro.campus.nome', 'localizacao',
                           'ambientes']

    # Exibição dos nomes das colunas (necessário adicionar os acentos)
    # Colunas referenciadas de outros modelos devem ter seus nomes corrigidos
    column_labels = {'departamento.nome': 'Departamento',
                     'departamento.centro.nome': 'Centro',
                     'departamento.centro.campus.nome': 'Campus',
                     'localizacao': 'Localização'}

    # Colunas que possuem um formato modificado (arquivo 'typefmt.py')
    column_formatters = dict(ambientes=typefmt.formato_relacao_ambientes)

    # Lista de filtros que podem ser aplicados em cada coluna
    # Deve-se indicar a coluna e o nome de exibição do filtro
    # Note também que alguns tipos de dados possuem mais de um filtro ('filters.py')
    column_filters = FiltrosStrings(Departamento.nome, 'Departamento')
    column_filters.extend(FiltrosStrings(Centro.nome, 'Centro'))
    column_filters.extend(FiltrosStrings(Campus.nome, 'Campus'))

    # Definição dos formulários utilizados
    create_form = FormCriarBloco
    edit_form = FormEditarBloco


    # Inicialização
    def __init__(self, *args, **kwargs):
        super(ModelViewBloco, self).__init__(*args, **kwargs)

        # Consertar geração automática de joins para as queries dos filtros

        self._filter_joins[Centro.nome] = [Departamento.__table__, Centro.__table__]

        self._filter_joins[Campus.nome] = [Departamento.__table__, Centro.__table__,
                                           Campus.__table__]


##### Ambientes #####


# Ambientes
class ModelViewAmbiente(ModelViewCadastrador):
    # Nesta view são mostrados todos os tipos de ambientes (interno, externo, ...)

    # Colunas exibidas na view de listagem (em ordem)
    # Caso a coluna seja uma referência a outro modelo, indicar que
    # coluna do modelo referenciado deve ser exibida usando notação de ponto
    column_list = ['nome', 'tipo', 'bloco.nome',
                   'bloco.departamento.nome',
                   'bloco.departamento.centro.nome', 
                   'bloco.departamento.centro.campus.nome']

    # Coluna padrão usada para ordenar itens
    column_default_sort = 'nome'

    # Colunas que podem ser utilizadas para ordenar os itens
    column_sortable_list = ['nome', 'tipo', 'bloco.nome',
                            'bloco.departamento.nome',
                            'bloco.departamento.centro.nome',
                            'bloco.departamento.centro.campus.nome']

    # Colunas em que pode ser feita busca
    column_searchable_list = ['nome', 'tipo', 'bloco.nome', 'bloco.departamento.nome',
                              'bloco.departamento.centro.nome',
                              'bloco.departamento.centro.campus.nome']

    # Exibição dos nomes das colunas (necessário adicionar os acentos)
    # Colunas referenciadas de outros modelos devem ter seus nomes corrigidos
    column_labels = {'bloco.nome': 'Bloco',
                     'bloco.departamento.nome': 'Departamento',
                     'bloco.departamento.centro.nome': 'Centro',
                     'bloco.departamento.centro.campus.nome': 'Campus'}

    # Lista de filtros que podem ser aplicados em cada coluna
    # Deve-se indicar a coluna e o nome de exibição do filtro
    # Note também que alguns tipos de dados possuem mais de um filtro ('filters.py')
    column_filters = FiltrosStrings(Ambiente.tipo, 'Tipo')
    column_filters.extend(FiltrosStrings(Bloco.nome, 'Bloco'))
    column_filters.extend(FiltrosStrings(Departamento.nome, 'Departamento'))
    column_filters.extend(FiltrosStrings(Centro.nome, 'Centro'))
    column_filters.extend(FiltrosStrings(Campus.nome, 'Campus'))


    # Inicialização
    def __init__(self, *args, **kwargs):
        super(ModelViewAmbiente, self).__init__(*args, **kwargs)

        # Consertar geração automática de joins para as queries dos filtros

        self._filter_joins[Departamento.nome] = [Bloco.__table__, Departamento.__table__]

        self._filter_joins[Centro.nome] = [Bloco.__table__, Departamento.__table__,
                                           Centro.__table__]

        self._filter_joins[Campus.nome] = [Bloco.__table__, Departamento.__table__,
                                           Centro.__table__, Campus.__table__]


    # View de criação modificada
    # Escolha do tipo de ambiente e redirecionamento para view de criação correspondente
    @expose('/new/', methods=['GET', 'POST'])
    def create_view(self):
        # Formulário para escolha do tipo de ambiente a ser criado
        form = FormCriarAmbiente()

        if form.validate_on_submit():
            # Redirecionar para a view de criação do tipo de ambiente escolhido
            return redirect(url_for(form.tipo_ambiente.data + '.create_view',
                            url=url_for('ambiente.index_view')))
            
        return self.render('administracao/criar_ambiente.html', form=form,
                           return_url=url_for('ambiente.index_view'))


    # View de edição modificada
    # Redirecionamento para view de edição correspondente a partir do id do ambiente
    @expose('/edit/')
    def edit_view(self):
        # Obter id do ambiente a partir da query string
        id_ambiente = request.args.get('id')

        # Obter o endpoint para o tipo de ambiente do ambiente representado pelo id
        tipo_ambiente = Ambiente.query.get(id_ambiente).endpoint

        # Redirecionar para view de edição do ambiente representado pelo id
        return redirect(url_for(tipo_ambiente + '.edit_view',
                                url=url_for('ambiente.index_view'),
                                id=id_ambiente))


    # View de detalhes modificada
    # Redirecionamento para view de detalhes correspondente a partir do id do ambiente
    @expose('/details/')
    def details_view(self):
        # Obter id do ambiente a partir da query string
        id_ambiente = request.args.get('id')

        # Obter o endpoint para o tipo de ambiente do ambiente representado pelo id
        tipo_ambiente = Ambiente.query.get(id_ambiente).endpoint

        # Redirecionar para view de detalhes do ambiente representado pelo id
        return redirect(url_for(tipo_ambiente + '.details_view',
                                url=url_for('ambiente.index_view'),
                                id=id_ambiente))


# Ambientes Internos
class ModelViewAmbienteInterno(ModelViewCadastrador):
    # Colunas exibidas na view de listagem (em ordem)
    # Caso a coluna seja uma referência a outro modelo, indicar que
    # coluna do modelo referenciado deve ser exibida usando notação de ponto
    column_list = ['nome', 'andar', 'bloco.nome',
                   'bloco.departamento.nome',
                   'bloco.departamento.centro.nome',
                   'bloco.departamento.centro.campus.nome']

    # Coluna padrão usada para ordenar itens
    column_default_sort = 'nome'

    # Colunas que podem ser utilizadas para ordenar os itens
    column_sortable_list = ['nome', 'andar', 'bloco.nome',
                            'bloco.departamento.nome',
                            'bloco.departamento.centro.nome', 
                            'bloco.departamento.centro.campus.nome']

    # Colunas em que pode ser feita busca
    column_searchable_list = ['nome', 'andar', 'bloco.nome',
                              'bloco.departamento.nome', 
                              'bloco.departamento.centro.nome',
                              'bloco.departamento.centro.campus.nome']

    # Colunas exibidas na view de detalhes (em ordem)
    column_details_list = ['nome', 'tipo', 'andar', 'bloco.nome',
                           'bloco.departamento.nome',
                           'bloco.departamento.centro.nome',
                           'bloco.departamento.centro.campus.nome',
                           'detalhe_localizacao', 'area', 'populacao', 'equipamentos']

    # Exibição dos nomes das colunas (necessário adicionar os acentos)
    # Colunas referenciadas de outros modelos devem ter seus nomes corrigidos
    column_labels = {'bloco.nome': 'Bloco',
                     'bloco.departamento.nome': 'Departamento',
                     'bloco.departamento.centro.nome': 'Centro',
                     'bloco.departamento.centro.campus.nome': 'Campus',
                     'detalhe_localizacao': 'Detalhe de Localização',
                     'area': 'Área (m²)',
                     'populacao': 'População'}

    # Colunas que possuem um formato modificado (arquivo 'typefmt.py')
    column_formatters = dict(equipamentos=typefmt.formato_relacao_equipamentos)

    # Lista de filtros que podem ser aplicados em cada coluna
    # Deve-se indicar a coluna e o nome de exibição do filtro
    # Note também que alguns tipos de dados possuem mais de um filtro ('filters.py')
    column_filters = FiltrosStrings(Bloco.nome, 'Bloco')
    column_filters.extend(FiltrosStrings(AmbienteInterno.andar, 'Andar'))
    column_filters.extend(FiltrosStrings(Departamento.nome, 'Departamento'))
    column_filters.extend(FiltrosStrings(Centro.nome, 'Centro'))
    column_filters.extend(FiltrosStrings(Campus.nome, 'Campus'))

    # Definição dos formulários utilizados
    create_form = FormCriarAmbienteInterno
    edit_form = FormEditarAmbienteInterno


    # Inicialização
    def __init__(self, *args, **kwargs):
        super(ModelViewAmbienteInterno, self).__init__(*args, **kwargs)

        # Consertar geração automática de joins para as queries dos filtros

        self._filter_joins[Departamento.nome] = [Bloco.__table__, Departamento.__table__]

        self._filter_joins[Centro.nome] = [Bloco.__table__, Departamento.__table__,
                                           Centro.__table__]

        self._filter_joins[Campus.nome] = [Bloco.__table__, Departamento.__table__,
                                           Centro.__table__, Campus.__table__]


# Ambientes Externos
class ModelViewAmbienteExterno(ModelViewCadastrador):
    # Colunas exibidas na view de listagem (em ordem)
    # Caso a coluna seja uma referência a outro modelo, indicar que
    # coluna do modelo referenciado deve ser exibida usando notação de ponto
    column_list = ['nome', 'bloco.nome',
                   'bloco.departamento.nome',
                   'bloco.departamento.centro.nome',
                   'bloco.departamento.centro.campus.nome']

    # Coluna padrão usada para ordenar itens
    column_default_sort = 'nome'

    # Colunas que podem ser utilizadas para ordenar os itens
    column_sortable_list = ['nome', 'bloco.nome',
                            'bloco.departamento.nome',
                            'bloco.departamento.centro.nome', 
                            'bloco.departamento.centro.campus.nome']

    # Colunas em que pode ser feita busca
    column_searchable_list = ['nome', 'bloco.nome',
                              'bloco.departamento.nome', 
                              'bloco.departamento.centro.nome',
                              'bloco.departamento.centro.campus.nome']

    # Colunas exibidas na view de detalhes (em ordem)
    column_details_list = ['nome', 'tipo', 'bloco.nome',
                           'bloco.departamento.nome',
                           'bloco.departamento.centro.nome',
                           'bloco.departamento.centro.campus.nome',
                           'detalhe_localizacao', 'equipamentos']

    # Exibição dos nomes das colunas (necessário adicionar os acentos)
    # Colunas referenciadas de outros modelos devem ter seus nomes corrigidos
    column_labels = {'bloco.nome': 'Bloco',
                     'bloco.departamento.nome': 'Departamento',
                     'bloco.departamento.centro.nome': 'Centro',
                     'bloco.departamento.centro.campus.nome': 'Campus',
                     'detalhe_localizacao': 'Detalhe de Localização'}

    # Colunas que possuem um formato modificado (arquivo 'typefmt.py')
    column_formatters = dict(equipamentos=typefmt.formato_relacao_equipamentos)

    # Lista de filtros que podem ser aplicados em cada coluna
    # Deve-se indicar a coluna e o nome de exibição do filtro
    # Note também que alguns tipos de dados possuem mais de um filtro ('filters.py')
    column_filters = FiltrosStrings(Bloco.nome, 'Bloco')
    column_filters.extend(FiltrosStrings(Departamento.nome, 'Departamento'))
    column_filters.extend(FiltrosStrings(Centro.nome, 'Centro'))
    column_filters.extend(FiltrosStrings(Campus.nome, 'Campus'))

    # Definição dos formulários utilizados
    create_form = FormCriarAmbienteExterno
    edit_form = FormEditarAmbienteExterno


    # Inicialização
    def __init__(self, *args, **kwargs):
        super(ModelViewAmbienteExterno, self).__init__(*args, **kwargs)

        # Consertar geração automática de joins para as queries dos filtros

        self._filter_joins[Departamento.nome] = [Bloco.__table__, Departamento.__table__]

        self._filter_joins[Centro.nome] = [Bloco.__table__, Departamento.__table__,
                                           Centro.__table__]

        self._filter_joins[Campus.nome] = [Bloco.__table__, Departamento.__table__,
                                           Centro.__table__, Campus.__table__]


# Subestações Abrigadas
class ModelViewSubestacaoAbrigada(ModelViewCadastrador):
    # Colunas exibidas na view de listagem (em ordem)
    # Caso a coluna seja uma referência a outro modelo, indicar que
    # coluna do modelo referenciado deve ser exibida usando notação de ponto
    column_list = ['nome', 'bloco.departamento.centro.campus.nome', 'localizacao']

    # Coluna padrão usada para ordenar itens
    column_default_sort = 'nome'

    # Colunas que podem ser utilizadas para ordenar os itens
    column_sortable_list = ['nome',
                            'bloco.departamento.centro.campus.nome']

    # Colunas em que pode ser feita busca
    column_searchable_list = ['nome', 'bloco.departamento.centro.campus.nome']

    # Colunas exibidas na view de detalhes (em ordem)
    column_details_list = ['nome', 'tipo', 'bloco.nome',
                           'bloco.departamento.nome',
                           'bloco.departamento.centro.nome',
                           'bloco.departamento.centro.campus.nome',
                           'localizacao', 'detalhe_localizacao', 'equipamentos']

    # Exibição dos nomes das colunas (necessário adicionar os acentos)
    # Colunas referenciadas de outros modelos devem ter seus nomes corrigidos
    column_labels = {'bloco.nome': 'Bloco',
                     'bloco.departamento.nome': 'Departamento',
                     'bloco.departamento.centro.nome': 'Centro',
                     'bloco.departamento.centro.campus.nome': 'Campus',
                     'localizacao': 'Localização',
                     'detalhe_localizacao': 'Detalhe de Localização'}

    # Colunas que possuem um formato modificado (arquivo 'typefmt.py')
    column_formatters = dict(equipamentos=typefmt.formato_relacao_equipamentos)

    # Lista de filtros que podem ser aplicados em cada coluna
    # Deve-se indicar a coluna e o nome de exibição do filtro
    # Note também que alguns tipos de dados possuem mais de um filtro ('filters.py')
    column_filters = FiltrosStrings(Campus.nome, 'Campus')

    # Definição dos formulários utilizados
    create_form = FormCriarSubestacaoAbrigada
    edit_form = FormEditarSubestacaoAbrigada


    # Inicialização
    def __init__(self, *args, **kwargs):
        super(ModelViewSubestacaoAbrigada, self).__init__(*args, **kwargs)

        # Consertar geração automática de joins para as queries dos filtros

        self._filter_joins[Campus.nome] = [Bloco.__table__, Departamento.__table__,
                                           Centro.__table__, Campus.__table__]


# Subestações Aéreas
class ModelViewSubestacaoAerea(ModelViewCadastrador):
    # Colunas exibidas na view de listagem (em ordem)
    # Caso a coluna seja uma referência a outro modelo, indicar que
    # coluna do modelo referenciado deve ser exibida usando notação de ponto
    column_list = ['nome', 'bloco.departamento.centro.campus.nome', 'localizacao']

    # Coluna padrão usada para ordenar itens
    column_default_sort = 'nome'

    # Colunas que podem ser utilizadas para ordenar os itens
    column_sortable_list = ['nome',
                            'bloco.departamento.centro.campus.nome']

    # Colunas em que pode ser feita busca
    column_searchable_list = ['nome', 'bloco.departamento.centro.campus.nome']

    # Colunas exibidas na view de detalhes (em ordem)
    column_details_list = ['nome', 'tipo', 'bloco.nome',
                           'bloco.departamento.nome',
                           'bloco.departamento.centro.nome',
                           'bloco.departamento.centro.campus.nome',
                           'localizacao', 'detalhe_localizacao', 'equipamentos']

    # Exibição dos nomes das colunas (necessário adicionar os acentos)
    # Colunas referenciadas de outros modelos devem ter seus nomes corrigidos
    column_labels = {'bloco.nome': 'Bloco',
                     'bloco.departamento.nome': 'Departamento',
                     'bloco.departamento.centro.nome': 'Centro',
                     'bloco.departamento.centro.campus.nome': 'Campus',
                     'localizacao': 'Localização',
                     'detalhe_localizacao': 'Detalhe de Localização'}

    # Colunas que possuem um formato modificado (arquivo 'typefmt.py')
    column_formatters = dict(equipamentos=typefmt.formato_relacao_equipamentos)

    # Lista de filtros que podem ser aplicados em cada coluna
    # Deve-se indicar a coluna e o nome de exibição do filtro
    # Note também que alguns tipos de dados possuem mais de um filtro ('filters.py')
    column_filters = FiltrosStrings(Campus.nome, 'Campus')

    # Definição dos formulários utilizados
    create_form = FormCriarSubestacaoAerea
    edit_form = FormEditarSubestacaoAerea


    # Inicialização
    def __init__(self, *args, **kwargs):
        super(ModelViewSubestacaoAerea, self).__init__(*args, **kwargs)

        # Consertar geração automática de joins para as queries dos filtros

        self._filter_joins[Campus.nome] = [Bloco.__table__, Departamento.__table__,
                                           Centro.__table__, Campus.__table__]


##### Equipamentos #####


# Equipamentos
class ModelViewEquipamento(ModelViewCadastrador):
    # Nesta view são mostrados todos os tipos de equipamentos
    # (extintores, condicionadores de ar...)

    # Colunas exibidas na view de listagem (em ordem)
    # Caso a coluna seja uma referência a outro modelo, indicar que
    # coluna do modelo referenciado deve ser exibida usando notação de ponto
    column_list = ['tombamento', 'tipo_equipamento', 'categoria_equipamento',
                   'fabricante', 'ambiente.nome', 'ambiente.bloco.nome',
                   'ambiente.bloco.departamento.nome',
                   'ambiente.bloco.departamento.centro.nome',
                   'ambiente.bloco.departamento.centro.campus.nome',
                   'em_uso', 'em_manutencao']

    # Coluna padrão usada para ordenar itens
    column_default_sort = 'tombamento'

    # Colunas que podem ser utilizadas para ordenar os itens
    column_sortable_list = ['tombamento', 'tipo_equipamento', 'categoria_equipamento', 
                            'fabricante', 'ambiente.nome',
                            'ambiente.bloco.nome',
                            'ambiente.bloco.departamento.nome',
                            'ambiente.bloco.departamento.centro.nome',
                            'ambiente.bloco.departamento.centro.campus.nome']

    # Colunas em que pode ser feita busca
    column_searchable_list = ['tombamento', 'tipo_equipamento', 'categoria_equipamento',
                              'fabricante', 'ambiente.nome', 'ambiente.bloco.nome',
                              'ambiente.bloco.departamento.nome',
                              'ambiente.bloco.departamento.centro.nome',
                              'ambiente.bloco.departamento.centro.campus.nome']

    # Exibição dos nomes das colunas (necessário adicionar os acentos)
    # Colunas referenciadas de outros modelos devem ter seus nomes corrigidos
    column_labels = {'ambiente.nome': 'Ambiente',
                     'tipo_equipamento': 'Tipo',
                     'categoria_equipamento': 'Categoria',
                     'ambiente.bloco.nome': 'Bloco',
                     'ambiente.bloco.departamento.nome': 'Departamento',
                     'ambiente.bloco.departamento.centro.nome': 'Centro',
                     'ambiente.bloco.departamento.centro.campus.nome': 'Campus',
                     'em_manutencao': 'Em Manutenção'}

    # Lista de filtros que podem ser aplicados em cada coluna
    # Deve-se indicar a coluna e o nome de exibição do filtro
    # Note também que alguns tipos de dados possuem mais de um filtro ('filters.py')
    column_filters = FiltrosStrings(Equipamento.tipo_equipamento, 'Tipo')
    column_filters.extend(FiltrosStrings(Equipamento.categoria_equipamento, 'Categoria'))
    column_filters.extend(FiltrosStrings(Equipamento.fabricante, 'Fabricante'))
    column_filters.extend(FiltrosStrings(Ambiente.nome, 'Ambiente'))
    column_filters.extend(FiltrosStrings(Bloco.nome, 'Bloco'))
    column_filters.extend(FiltrosStrings(Departamento.nome, 'Departamento'))
    column_filters.extend(FiltrosStrings(Centro.nome, 'Centro'))
    column_filters.extend(FiltrosStrings(Campus.nome, 'Campus'))    
    column_filters.append(BooleanEqualFilter(Equipamento.em_uso, 'Em Uso'))
    column_filters.append(BooleanEqualFilter(Equipamento.em_uso, 'Em Manutenção'))


    # Inicialização
    def __init__(self, *args, **kwargs):
        super(ModelViewEquipamento, self).__init__(*args, **kwargs)

        # Consertar geração automática de joins para as queries dos filtros

        self._filter_joins[Bloco.nome] = [Ambiente.__table__, Bloco.__table__]

        self._filter_joins[Departamento.nome] = [Ambiente.__table__, Bloco.__table__,
                                                 Departamento.__table__]

        self._filter_joins[Centro.nome] = [Ambiente.__table__, Bloco.__table__,
                                           Departamento.__table__, Centro.__table__]

        self._filter_joins[Campus.nome] = [Ambiente.__table__, Bloco.__table__,
                                           Departamento.__table__,Centro.__table__,
                                           Campus.__table__]

    # View de criação modificada
    # Escolha tipo de equipamento e redirecionamento para view de criação correspondente
    @expose('/new/', methods=['GET', 'POST'])
    def create_view(self):
        # Formulário para escolha do tipo de ambiente a ser criado
        form = FormCriarEquipamento()

        if form.validate_on_submit():
            # Redirecionar para a view de criação do tipo de equipamento escolhido
            return redirect(url_for(form.tipo_equipamento.data + '.create_view',
                            url=url_for('equipamento.index_view')))
            
        return self.render('administracao/criar_equipamento.html', form=form,
                           return_url=url_for('equipamento.index_view'))

    # View de edição modificada
    # Redirecionamento para view de edição correspondente a partir do id do equipamento
    @expose('/edit/')
    def edit_view(self):
        # Obter id do equipamento a partir da query string
        id_equipamento = request.args.get('id')

        # Obter o endpoint para o tipo de equipamento do equipamento representado pelo id
        tipo_equipamento = Equipamento.query.get(id_equipamento).endpoint

        # Redirecionar para a view de edição do equipamento representado pelo id
        return redirect(url_for(tipo_equipamento + '.edit_view',
                                url = url_for('equipamento.index_view'),
                                id=id_equipamento))

    # View de detalhes modificada
    # Redirecionar para view de detalhes correspondente a partir do id do equipamento
    @expose('/details/')
    def details_view(self):
        # Obter id do equipamento a partir da query string
        id_equipamento = request.args.get('id')

        # Obter o endpoint para o tipo de equipamento do equipamento representado pelo id
        tipo_equipamento = Equipamento.query.get(id_equipamento).endpoint

        # Redirecionar para a view de edição do equipamento representado pelo id
        return redirect(url_for(tipo_equipamento + '.details_view',
                                url = url_for('equipamento.index_view'),
                                id=id_equipamento))


# Extintores
class ModelViewExtintor(ModelViewCadastrador):
    # Colunas exibidas na view de listagem (em ordem)
    # Caso a coluna seja uma referência a outro modelo, indicar que
    # coluna do modelo referenciado deve ser exibida usando notação de ponto
    column_list = ['tombamento', 'classificacao', 'carga_nominal', 'fabricante',
                   'ambiente.nome', 'ambiente.bloco.nome',
                   'ambiente.bloco.departamento.nome',
                   'ambiente.bloco.departamento.centro.nome',
                   'ambiente.bloco.departamento.centro.campus.nome',
                   'proxima_manutencao', 'em_uso', 'em_manutencao']

    # Coluna padrão usada para ordenar itens
    column_default_sort = 'tombamento'

    # Colunas que podem ser utilizadas para ordenar os itens
    column_sortable_list = ['tombamento', 'classificacao', 'carga_nominal', 'fabricante',
                            'ambiente.nome', 'ambiente.bloco.nome',
                            'ambiente.bloco.departamento.nome',
                            'ambiente.bloco.departamento.centro.nome',
                            'ambiente.bloco.departamento.centro.campus.nome',
                            'proxima_manutencao']

    # Colunas em que pode ser feita busca
    column_searchable_list = ['tombamento', 'classificacao', 'ambiente.nome',
                              'fabricante', 'ambiente.bloco.nome',
                              'ambiente.bloco.departamento.nome',
                              'ambiente.bloco.departamento.centro.nome',
                              'ambiente.bloco.departamento.centro.campus.nome']

    # Colunas exibidas na view de detalhes (em ordem)
    column_details_list = ['tombamento', 'tipo_equipamento', 'categoria_equipamento',
                           'classificacao', 'carga_nominal', 'fabricante',
                           'ambiente.nome', 'ambiente.bloco.nome',
                           'ambiente.bloco.departamento.nome',
                           'ambiente.bloco.departamento.centro.nome',
                           'ambiente.bloco.departamento.centro.campus.nome',
                           'info_adicional', 'intervalo_manutencao', 
                           'proxima_manutencao', 'manutencoes', 'em_uso',
                           'em_manutencao', 'inicio_manutencao']

    # Exibição dos nomes das colunas (necessário adicionar os acentos)
    # Colunas referenciadas de outros modelos devem ter seus nomes corrigidos
    column_labels = {'tipo_equipamento': 'Tipo',
                     'categoria_equipamento': 'Categoria',
                     'classificacao': 'Classificação',
                     'ambiente.nome': 'Ambiente',
                     'ambiente.bloco.nome': 'Bloco',
                     'ambiente.bloco.departamento.nome': 'Departamento',
                     'ambiente.bloco.departamento.centro.nome': 'Centro',
                     'ambiente.bloco.departamento.centro.campus.nome': 'Campus',
                     'intervalo_manutencao': 'Intervalo de Manutenção',
                     'manutencoes': 'Manutenções',
                     'proxima_manutencao': 'Próxima Manutenção',
                     'info_adicional': 'Informações Adicionais',
                     'em_manutencao': 'Em Manutenção',
                     'inicio_manutencao': 'Início da Manutenção'}

    # Colunas que possuem um formato modificado (arquivo 'typefmt.py')
    column_formatters = dict(manutencoes=typefmt.formato_relacao_manutencoes)

    # Lista de filtros que podem ser aplicados em cada coluna
    # Deve-se indicar a coluna e o nome de exibição do filtro
    # Note também que alguns tipos de dados possuem mais de um filtro ('filters.py')
    column_filters = FiltrosStrings(Extintor.classificacao, 'Classificação')
    column_filters.extend(FiltrosFloats(Extintor.carga_nominal, 'Carga Nominal'))
    column_filters.extend(FiltrosStrings(Extintor.fabricante, 'Fabricante'))
    column_filters.extend(FiltrosStrings(Ambiente.nome, 'Ambiente'))
    column_filters.extend(FiltrosStrings(Bloco.nome, 'Bloco'))
    column_filters.extend(FiltrosStrings(Departamento.nome, 'Departamento'))
    column_filters.extend(FiltrosStrings(Centro.nome, 'Centro'))
    column_filters.extend(FiltrosStrings(Campus.nome, 'Campus'))
    column_filters.extend(FiltrosDatas(Extintor.proxima_manutencao, 'Próxima Manutenção'))
    column_filters.append(BooleanEqualFilter(Equipamento.em_uso, 'Em Uso'))
    column_filters.append(BooleanEqualFilter(Equipamento.em_manutencao, 'Em Manutenção'))

    # Definição dos formulários utilizados
    create_form = FormCriarExtintor
    edit_form = FormEditarExtintor


    # Inicialização
    def __init__(self, *args, **kwargs):
        super(ModelViewExtintor, self).__init__(*args, **kwargs)

        # Consertar geração automática de joins para as queries dos filtros

        self._filter_joins[Bloco.nome] = [Ambiente.__table__, Bloco.__table__]

        self._filter_joins[Departamento.nome] = [Ambiente.__table__, Bloco.__table__,
                                                 Departamento.__table__]

        self._filter_joins[Centro.nome] = [Ambiente.__table__, Bloco.__table__,
                                           Departamento.__table__, Centro.__table__]

        self._filter_joins[Campus.nome] = [Ambiente.__table__, Bloco.__table__,
                                           Departamento.__table__,Centro.__table__,
                                           Campus.__table__]


    # Procedimentos adicionais após criação/edição
    def after_model_change(self, form, model, is_created):
        # Obtendo id do equipamento
        id_equipamento = model.id

        # Quando um equipamento é criado, é necessário que seja cadastrada também
        # uma manutenção inicial para que seja possível agendar suas manutenções
        # preventivas
        if is_created:
            # Por padrão, é criada uma manutenção inicial com a data do dia
            # da criação do equipamento, mas também é dada a opção de cadastro
            # de uma manutenção inicial já existente

            # Criação da manutenção inicial padrão
            manutencao = Manutencao()
            manutencao.num_ordem_servico = 0
            manutencao.data_abertura = date.today()
            manutencao.data_conclusao = date.today()
            manutencao.tipo_manutencao = 'Inicial'
            manutencao.id_equipamento = id_equipamento
            manutencao.descricao_servico = 'Manutenção inicial padrão criada automaticamente.'
            manutencao.status = 'Concluída'

            # Salvando no banco de dados
            db.session.add(manutencao)
            db.session.commit()

        # Havendo uma manutenção inicial ou eventual edição no intervalo de
        # manutenção, a data da próxima manutenção preventiva é calculada

        # Lista de manutenções concluídas (ordenadas por data de conclusão)
        manutencoes = Manutencao.query.filter_by(id_equipamento=id_equipamento)\
                                      .filter_by(status='Concluída')\
                                      .order_by('data_conclusao').all()        

        # Última manutenção concluída do equipamento
        ultima_manutencao = manutencoes[-1]

        # Cálculo da data da próxima manutenção a ser realizada
        delta = timedelta(days = 30 * model.intervalo_manutencao)
        model.proxima_manutencao = ultima_manutencao.data_conclusao + delta

        # Salvando no banco de dados
        db.session.add(model)
        db.session.commit()


    # Após criação de um novo equipamento, redirecionar para uma página em que
    # pode-se escolher se será utilizada uma manutenção inicial padrão ou se
    # uma manutenção inicial já existente será cadastrada
    def get_save_return_url(self, model, is_created):
        if is_created:
            return url_for('manutencao.manutencao_inicial', id=model.id,
                           url=request.args.get('url'))
        
        # Caso haja apenas edição, redirecionar para view de listagem
        return self.get_url('.index_view')


# Condicionadores de Ar
class ModelViewCondicionadorAr(ModelViewCadastrador):
    # Colunas exibidas na view de listagem (em ordem)
    # Caso a coluna seja uma referência a outro modelo, indicar que
    # coluna do modelo referenciado deve ser exibida usando notação de ponto
    column_list = ['tombamento', 'classificacao', 'cap_refrigeracao', 'pot_nominal',
                   'tensao_alimentacao', 'eficiencia', 'fabricante', 
                   'ambiente.nome', 'ambiente.bloco.nome',
                   'ambiente.bloco.departamento.nome',
                   'ambiente.bloco.departamento.centro.nome',
                   'ambiente.bloco.departamento.centro.campus.nome',
                   'proxima_manutencao', 'em_uso', 'em_manutencao']

    # Coluna padrão usada para ordenar itens
    column_default_sort = 'tombamento'

    # Colunas que podem ser utilizadas para ordenar os itens
    column_sortable_list = ['tombamento', 'classificacao', 'cap_refrigeracao',
                            'pot_nominal', 'tensao_alimentacao', 'eficiencia', 'fabricante',
                            'ambiente.nome', 'ambiente.bloco.nome',
                            'ambiente.bloco.departamento.nome', 
                            'ambiente.bloco.departamento.centro.nome', 
                            'ambiente.bloco.departamento.centro.campus.nome',
                            'proxima_manutencao']

    # Colunas em que pode ser feita busca
    column_searchable_list = ['tombamento', 'classificacao', 'ambiente.nome',
                              'fabricante', 'ambiente.bloco.nome',
                              'ambiente.bloco.departamento.nome',
                              'ambiente.bloco.departamento.centro.nome',
                              'ambiente.bloco.departamento.centro.campus.nome']

    # Colunas exibidas na view de detalhes (em ordem)
    column_details_list = ['tombamento', 'tipo_equipamento', 'categoria_equipamento',
                           'classificacao', 'cap_refrigeracao', 'pot_nominal', 'tensao_alimentacao',
                           'eficiencia', 'fabricante', 'ambiente.nome',
                           'ambiente.bloco.nome',
                           'ambiente.bloco.departamento.nome',
                           'ambiente.bloco.departamento.centro.nome',
                           'ambiente.bloco.departamento.centro.campus.nome',
                           'info_adicional', 'intervalo_manutencao',
                           'proxima_manutencao', 'manutencoes', 'em_uso',
                           'em_manutencao', 'inicio_manutencao']

    # Exibição dos nomes das colunas (necessário adicionar os acentos)
    # Colunas referenciadas de outros modelos devem ter seus nomes corrigidos
    column_labels = {'tipo_equipamento': 'Tipo',
                     'categoria_equipamento': 'Categoria',
                     'classificacao': 'Classificação',
                     'cap_refrigeracao': 'Cap. de Refrigeração',
                     'pot_nominal': 'Pot. Nominal',
                     'tensao_alimentacao': 'Tensão de Alimentação',
                     'eficiencia': 'Eficiência',
                     'ambiente.nome': 'Ambiente',
                     'ambiente.bloco.nome': 'Bloco',
                     'ambiente.bloco.departamento.nome': 'Departamento',
                     'ambiente.bloco.departamento.centro.nome': 'Centro',
                     'ambiente.bloco.departamento.centro.campus.nome': 'Campus',
                     'intervalo_manutencao': 'Intervalo de Manutenção',
                     'manutencoes': 'Manutenções',
                     'proxima_manutencao': 'Próxima Manutenção',
                     'info_adicional': 'Informações Adicionais',
                     'em_manutencao': 'Em Manutenção',
                     'inicio_manutencao': 'Início da Manutenção'}

    # Colunas que possuem um formato modificado (arquivo 'typefmt.py')
    column_formatters = dict(manutencoes=typefmt.formato_relacao_manutencoes)

    # Lista de filtros que podem ser aplicados em cada coluna
    # Deve-se indicar a coluna e o nome de exibição do filtro
    # Note também que alguns tipos de dados possuem mais de um filtro ('filters.py')
    column_filters = FiltrosStrings(CondicionadorAr.classificacao, 'Classificação')
    column_filters.extend(FiltrosInteiros(CondicionadorAr.cap_refrigeracao, 'Cap. Refrigeração'))
    column_filters.extend(FiltrosInteiros(CondicionadorAr.pot_nominal, 'Pot. Nominal'))
    column_filters.extend(FiltrosInteiros(CondicionadorAr.tensao_alimentacao, 'Tensão de Alimentação'))
    column_filters.extend(FiltrosStrings(CondicionadorAr.eficiencia, 'Eficiência'))
    column_filters.extend(FiltrosStrings(CondicionadorAr.fabricante, 'Fabricante'))
    column_filters.extend(FiltrosStrings(Ambiente.nome, 'Ambiente'))
    column_filters.extend(FiltrosStrings(Bloco.nome, 'Bloco'))
    column_filters.extend(FiltrosStrings(Departamento.nome, 'Departamento'))
    column_filters.extend(FiltrosStrings(Centro.nome, 'Centro'))
    column_filters.extend(FiltrosStrings(Campus.nome, 'Campus'))
    column_filters.extend(FiltrosDatas(CondicionadorAr.proxima_manutencao, 'Próxima Manutenção'))
    column_filters.append(BooleanEqualFilter(Equipamento.em_uso, 'Em Uso'))
    column_filters.append(BooleanEqualFilter(Equipamento.em_manutencao, 'Em Manutenção'))

    # Definição dos formulários utilizados
    create_form = FormCriarCondicionadorAr
    edit_form = FormEditarCondicionadorAr


    # Inicialização
    def __init__(self, *args, **kwargs):
        super(ModelViewCondicionadorAr, self).__init__(*args, **kwargs)

        # Consertar geração automática de joins para as queries dos filtros

        self._filter_joins[Bloco.nome] = [Ambiente.__table__, Bloco.__table__]

        self._filter_joins[Departamento.nome] = [Ambiente.__table__, Bloco.__table__,
                                                 Departamento.__table__]

        self._filter_joins[Centro.nome] = [Ambiente.__table__, Bloco.__table__,
                                           Departamento.__table__, Centro.__table__]

        self._filter_joins[Campus.nome] = [Ambiente.__table__, Bloco.__table__,
                                           Departamento.__table__,Centro.__table__,
                                           Campus.__table__]

    # Procedimentos adicionais após criação/edição
    def after_model_change(self, form, model, is_created):
        # Obtendo id do equipamento
        id_equipamento = model.id

        # Quando um equipamento é criado, é necessário que seja cadastrada também
        # uma manutenção inicial para que seja possível agendar suas manutenções
        # preventivas
        if is_created:
            # Por padrão, é criada uma manutenção inicial com a data do dia
            # da criação do equipamento, mas também é dada a opção de cadastro
            # de uma manutenção inicial já existente

            # Criação da manutenção inicial padrão
            manutencao = Manutencao()
            manutencao.num_ordem_servico = 0
            manutencao.data_abertura = date.today()
            manutencao.data_conclusao = date.today()
            manutencao.tipo_manutencao = 'Inicial'
            manutencao.id_equipamento = id_equipamento
            manutencao.descricao_servico = 'Manutenção inicial padrão criada automaticamente.'
            manutencao.status = 'Concluída'

            # Salvando no banco de dados
            db.session.add(manutencao)
            db.session.commit()

        # Havendo uma manutenção inicial ou eventual edição no intervalo de
        # manutenção, a data da próxima manutenção preventiva é calculada

        # Lista de manutenções concluídas (ordenadas por data de conclusão)
        manutencoes = Manutencao.query.filter_by(id_equipamento=id_equipamento)\
                                      .filter_by(status='Concluída')\
                                      .order_by('data_conclusao').all()        

        # Última manutenção concluída do equipamento
        ultima_manutencao = manutencoes[-1]

        # Cálculo da data da próxima manutenção a ser realizada
        delta = timedelta(days = 30 * model.intervalo_manutencao)
        model.proxima_manutencao = ultima_manutencao.data_conclusao + delta

        # Salvando no banco de dados
        db.session.add(model)
        db.session.commit()

    # Após criação de um novo equipamento, redirecionar para uma página em que
    # pode-se escolher se será utilizada uma manutenção inicial padrão ou se
    # uma manutenção inicial já existente será cadastrada
    def get_save_return_url(self, model, is_created):
        if is_created:
            return url_for('manutencao.manutencao_inicial', id=model.id,
                           url=request.args.get('url'))
        
        # Caso haja apenas edição, redirecionar para view de listagem
        return self.get_url('.index_view')


##### Manutenções #####


# Manutenções
class ModelViewManutencao(ModelViewCadastrador):
    # Colunas exibidas na view de listagem (em ordem)
    # Caso a coluna seja uma referência a outro modelo, indicar que
    # coluna do modelo referenciado deve ser exibida usando notação de ponto
    column_list = ['num_ordem_servico', 'data_abertura', 'data_conclusao',
                   'tipo_manutencao', 'equipamento.tipo_equipamento',
                   'equipamento.tombamento', 'equipamento.ambiente.nome',
                   'equipamento.ambiente.bloco.nome',
                   'equipamento.ambiente.bloco.departamento.nome',
                   'equipamento.ambiente.bloco.departamento.centro.nome',
                   'equipamento.ambiente.bloco.departamento.centro.campus.nome',
                   'status']

    # Coluna padrão usada para ordenar itens (True -> ordem descrescente)
    column_default_sort = ('data_abertura', True)

    # Colunas que podem ser utilizadas para ordenar os itens
    column_sortable_list = ['num_ordem_servico', 'data_abertura', 'data_conclusao',
                            'tipo_manutencao', 'equipamento.tipo_equipamento',
                            'equipamento.tombamento', 'equipamento.ambiente.nome',
                            'equipamento.ambiente.bloco.nome',
                            'equipamento.ambiente.bloco.departamento.nome',
                            'equipamento.ambiente.bloco.departamento.centro.nome',
                            'equipamento.ambiente.bloco.departamento.centro.campus.nome',
                            'status']

    # Colunas em que pode ser feita busca    
    column_searchable_list = ['num_ordem_servico', 'tipo_manutencao',
                              'equipamento.tipo_equipamento', 'equipamento.tombamento',
                              'equipamento.ambiente.nome', 'equipamento.ambiente.bloco.nome',
                              'equipamento.ambiente.bloco.departamento.nome',
                              'equipamento.ambiente.bloco.departamento.centro.nome',
                              'equipamento.ambiente.bloco.departamento.centro.campus.nome',
                              'status']
    
    # Colunas exibidas na view de detalhes (em ordem)
    column_details_list = ['num_ordem_servico', 'data_abertura', 'data_conclusao',
                           'tipo_manutencao', 'equipamento.tipo_equipamento',
                           'equipamento.tombamento', 'equipamento.ambiente.nome',
                           'equipamento.ambiente.bloco.nome',
                           'equipamento.ambiente.bloco.departamento.nome',
                           'equipamento.ambiente.bloco.departamento.centro.nome',
                           'equipamento.ambiente.bloco.departamento.centro.campus.nome',
                           'descricao_servico', 'status']

    # Exibição dos nomes das colunas (necessário adicionar os acentos)
    # Colunas referenciadas de outros modelos devem ter seus nomes corrigidos
    column_labels = {'num_ordem_servico': 'Ordem de Serviço',
                     'data_abertura': 'Data de Abertura',
                     'data_conclusao': 'Data de Conclusão',
                     'tipo_manutencao': 'Tipo de Manutenção',
                     'equipamento.tipo_equipamento': 'Tipo de Equipamento',
                     'equipamento.tombamento': 'Tombamento',
                     'equipamento.ambiente.nome': 'Ambiente',
                     'equipamento.ambiente.bloco.nome': 'Bloco',
                     'equipamento.ambiente.bloco.departamento.nome': 'Departamento',
                     'equipamento.ambiente.bloco.departamento.centro.nome': 'Centro',
                     'equipamento.ambiente.bloco.departamento.centro.campus.nome': 'Campus',
                     'descricao_servico': 'Descrição do Serviço'}

    # Lista de filtros que podem ser aplicados em cada coluna
    # Deve-se indicar a coluna e o nome de exibição do filtro
    # Note também que alguns tipos de dados possuem mais de um filtro ('filters.py')
    column_filters = FiltrosDatas(Manutencao.data_abertura, 'Data de Abertura')
    column_filters.extend(FiltrosDatas(Manutencao.data_conclusao, 'Data de Conclusão'))
    column_filters.extend(FiltrosStrings(Manutencao.tipo_manutencao, 'Tipo de Manutenção'))
    column_filters.extend(FiltrosStrings(Equipamento.tipo_equipamento, 'Tipo de Equipamento'))
    column_filters.extend(FiltrosInteiros(Equipamento.tombamento, 'Tombamento'))
    column_filters.extend(FiltrosStrings(Ambiente.nome, 'Ambiente'))
    column_filters.extend(FiltrosStrings(Bloco.nome, 'Bloco'))
    column_filters.extend(FiltrosStrings(Departamento.nome, 'Departamento'))
    column_filters.extend(FiltrosStrings(Centro.nome, 'Centro'))
    column_filters.extend(FiltrosStrings(Campus.nome, 'Campus'))
    column_filters.extend(FiltrosStrings(Manutencao.status, 'Status'))

    # Definição dos formulários utilizados
    create_form = FormCriarManutencao
    edit_form = FormEditarManutencao


    # Inicialização
    def __init__(self, *args, **kwargs):
        super(ModelViewManutencao, self).__init__(*args, **kwargs)

        # Consertar geração automática de joins para as queries dos filtros

        self._filter_joins[Ambiente.nome] = [Equipamento.__table__, Ambiente.__table__]

        self._filter_joins[Bloco.nome] = [Equipamento.__table__, Ambiente.__table__,
                                          Bloco.__table__]

        self._filter_joins[Departamento.nome] = [Equipamento.__table__, Ambiente.__table__,
                                                 Bloco.__table__, Departamento.__table__]

        self._filter_joins[Centro.nome] = [Equipamento.__table__, Ambiente.__table__,
                                           Bloco.__table__, Departamento.__table__,
                                           Centro.__table__]

        self._filter_joins[Campus.nome] = [Equipamento.__table__, Ambiente.__table__,
                                           Bloco.__table__, Departamento.__table__,
                                           Centro.__table__, Campus.__table__]


    # Procedimentos adicionais após criação/edição
    def after_model_change(self, form, model, is_created):
        # Equipamento alvo da manutenção
        equipamento = model.equipamento

        # Manutenções concluídas
        if model.status == 'Concluída':
            # Mudar o status "em manutenção" do equipamento
            equipamento.em_manutencao = False

            # Limpar o campo de data de abertura de manutenção do equipamento
            equipamento.inicio_manutencao = None

            # Para o caso de manutenção inicial, deve-se excluir a manutenção inicial
            # padrão que foi criada juntamente com o equipamento e manter apenas a
            # manutenção inicial cadastrada pelo usuário
            if model.tipo_manutencao == 'Inicial':
                for manutencao in equipamento.manutencoes:
                    # Testar se a manutenção é inicial e diferente da manutenção inicial
                    # recém criada
                    if manutencao.tipo_manutencao == 'Inicial' and manutencao != model:
                        # Excluir a manutenção inicial padrão
                        db.session.delete(manutencao)
                        db.session.commit()

            # Para o caso de troca, o equipamento antigo é colocado fora de uso
            if model.tipo_manutencao == 'Troca':
                equipamento.em_uso = False

                # Salvar no banco de dados
                db.session.add(equipamento)
                db.session.commit()

            # Recalcular a data da próxima manutenção preventiva para este equipamento.
            # A nova data sempre é calculada com base na data de conclusão da manutenção
            # concluída mais recentemente. Desta forma, caso uma manutenção antiga tenha 
            # sido cadastrada, sua data de conclusão não será usada como base para cálculo 
            # da próxima manutenção, que não será alterada.

            # Lista de manutenções concluídas (ordenadas por data de conclusão)
            manutencoes = Manutencao.query.filter_by(id_equipamento=equipamento.id)\
                                          .filter_by(status='Concluída')\
                                          .order_by('data_conclusao').all() 

            # Última manutenção concluída do equipamento
            ultima_manutencao = manutencoes[-1]

            # Cálculo da data da próxima manutenção a ser realizada
            # A data base para o cálculo é a data de conclusão da manutenção concluída
            # mais recentemente.
            delta = timedelta(days = 30 * equipamento.intervalo_manutencao)
            equipamento.proxima_manutencao = ultima_manutencao.data_conclusao + delta

            # Salvar no banco de dados
            db.session.add(equipamento)
            db.session.commit()

        # Manutenções abertas
        else:
            # Atualizar o status "em manutenção" do equipamento
            equipamento.em_manutencao = True

            # Atualizar o campo de data de abertura de manutenção do equipamento
            equipamento.inicio_manutencao = model.data_abertura


    # Quando uma manutenção tipo troca é concluída, redirecionar para criação de um
    # novo equipamento, que substituirá o antigo
    def get_save_return_url(self, model, is_created):
        if model.status == 'Concluída' and model.tipo_manutencao == 'Troca':
            # Obter equipamento que será trocado
            equipamento = model.equipamento

            # Obter o endpoint para o tipo de equipamento do equipamento a ser
            # trocado
            tipo_equipamento = equipamento.endpoint

            # Redirecionar para criação de um novo equipamento do mesmo tipo
            return url_for(tipo_equipamento + '.create_view',
                           url=request.args.get('url'))

        # Para outros casos, redirecionar para view de listagem
        return request.args.get('url') or self.get_url('.index_view')


    # Não permitir exclusão de manutenções iniciais para evitar comprometimento
    # do banco de dados (cada equipamento deve ter pelo menos uma manutenção)
    def on_model_delete(self, model):
        if model.tipo_manutencao == 'Inicial':
            raise Exception('Não é possível excluir manutenções iniciais.')

    # Quando uma manutenção é excluída, é possível que esta seja a última que foi
    # realizada no equipamento, logo, a data da próxima manutenção deste equipamento
    # ficará incorreta, por isso, será recalculada com base na manutenção concluída
    # mais recentemente, além da que foi excluída.
    def after_model_delete(self, model):
        # Obter id do equipamento alvo da manutenção excluída
        id_equipamento = model.id_equipamento

        # Obter o objeto equipamento a partir do seu id
        equipamento = Equipamento.query.get(id_equipamento)

        # Lista de manutenções concluídas do equipamento (ordenadas por data de conclusão)
        manutencoes = Manutencao.query.filter_by(id_equipamento=id_equipamento)\
                                      .filter_by(status='Concluída')\
                                      .order_by('data_conclusao').all() 

        # Última manutenção concluída do equipamento
        ultima_manutencao = manutencoes[-1]

        # Cálculo da data da próxima manutenção a ser realizada
        # A data base para o cálculo é a data de conclusão da manutenção concluída
        # mais recentemente.
        delta = timedelta(days = 30 * equipamento.intervalo_manutencao)
        equipamento.proxima_manutencao = ultima_manutencao.data_conclusao + delta

        # Salvar no banco de dados
        db.session.add(equipamento)
        db.session.commit()


    # Página de cadastro de manutenção inicial
    # São dadas como opções uma manutenção inicial padrão ou cadastro de uma
    # manutenção inicial já existente
    @expose('/manutencao-inicial')
    def manutencao_inicial(self):
        return self.render('administracao/manutencao_inicial.html',
                           id=request.args.get('id'),
                           url=request.args.get('url'))


##### Consumo #####


# Unidades Responsáveis
class ModelViewUnidadeResponsavel(ModelViewCadastrador):
    # Colunas exibidas na view de listagem (em ordem)
    # Caso a coluna seja uma referência a outro modelo, indicar que
    # coluna do modelo referenciado deve ser exibida usando notação de ponto
    column_list = ['nome']

    # Coluna padrão usada para ordenar itens
    column_default_sort = 'nome'

    # Colunas que podem ser utilizadas para ordenar os itens
    column_sortable_list = ['nome']

    # Colunas em que pode ser feita busca    
    column_searchable_list = ['nome']
    
    # Colunas exibidas na view de detalhes (em ordem)
    column_details_list = ['nome', 'responsaveis', 'unidades_consumidoras']

    # Exibição dos nomes das colunas (necessário adicionar os acentos)
    # Colunas referenciadas de outros modelos devem ter seus nomes corrigidos
    column_labels = {'responsaveis': 'Responsáveis'}

    # Colunas que possuem um formato modificado (arquivo 'typefmt.py')
    column_formatters = {'responsaveis': typefmt.formato_relacao_responsaveis,
                         'unidades_consumidoras': typefmt.formato_relacao_unidades_consumidoras}

    # Definição dos formulários utilizados
    create_form = FormCriarUnidadeResponsavel
    edit_form = FormEditarUnidadeResponsavel


# Unidades Consumidoras
class ModelViewUnidadeConsumidora(ModelViewCadastrador):
    # Colunas exibidas na view de listagem (em ordem)
    # Caso a coluna seja uma referência a outro modelo, indicar que
    # coluna do modelo referenciado deve ser exibida usando notação de ponto
    column_list = ['num_cliente', 'nome', 'unidade_responsavel.nome', 'localizacao']

    # Coluna padrão usada para ordenar itens
    column_default_sort = 'nome'

    # Colunas que podem ser utilizadas para ordenar os itens
    column_sortable_list = ['nome', 'unidade_responsavel.nome']

    # Colunas em que pode ser feita busca    
    column_searchable_list = ['num_cliente', 'nome', 'unidade_responsavel.nome']
    
    # Colunas exibidas na view de detalhes (em ordem)
    column_details_list = ['num_cliente', 'nome', 'unidade_responsavel.nome',
                           'endereco', 'localizacao', 'mod_tarifaria',
                           'num_medidores', 'hist_contas']

    # Exibição dos nomes das colunas (necessário adicionar os acentos)
    # Colunas referenciadas de outros modelos devem ter seus nomes corrigidos
    column_labels = {'num_cliente': 'Número do Cliente',
                     'unidade_responsavel.nome': 'Unidade Responsável',
                     'localizacao': 'Localização',
                     'endereco': 'Endereço',
                     'mod_tarifaria': 'Modalidade Tarifária',
                     'num_medidores': 'Número dos Medidores',
                     'hist_contas': 'Histórico de Contas'}

    # Colunas que possuem um formato modificado (arquivo 'typefmt.py')
    column_formatters = dict(hist_contas=typefmt.formato_relacao_contas)

    # Lista de filtros que podem ser aplicados em cada coluna
    # Deve-se indicar a coluna e o nome de exibição do filtro
    # Note também que alguns tipos de dados possuem mais de um filtro ('filters.py')

    column_filters = FiltrosStrings(UnidadeConsumidora.nome, 'Nome')
    column_filters.extend(FiltrosStrings(UnidadeResponsavel.nome, 'Unidade Responsável'))

    # Definição dos formulários utilizados
    create_form = FormCriarUnidadeConsumidora
    edit_form = FormEditarUnidadeConsumidora


# Contas de Energia
class ModelViewConta(ModelViewCadastrador):
    # Colunas exibidas na view de listagem (em ordem)
    # Caso a coluna seja uma referência a outro modelo, indicar que
    # coluna do modelo referenciado deve ser exibida usando notação de ponto
    column_list = ['unidade_consumidora.num_cliente', 'unidade_consumidora.nome',
                   'data_leitura', 'cons_fora_ponta', 'cons_hora_ponta', 
                   'valor_fora_ponta', 'valor_hora_ponta', 'valor_total']

    # Coluna padrão usada para ordenar itens
    column_default_sort = 'unidade_consumidora.nome'

    # Colunas que podem ser utilizadas para ordenar os itens
    column_sortable_list = ['unidade_consumidora.nome', 'data_leitura',
                            'cons_fora_ponta', 'cons_hora_ponta', 'valor_fora_ponta', 
                            'valor_hora_ponta', 'valor_total']

    # Colunas em que pode ser feita busca    
    column_searchable_list = ['unidade_consumidora.num_cliente', 'unidade_consumidora.nome']
    
    # Colunas exibidas na view de detalhes (em ordem)
    column_details_list = ['unidade_consumidora.num_cliente', 'unidade_consumidora.nome',
                           'data_leitura', 'cons_fora_ponta', 'cons_hora_ponta', 
                           'valor_fora_ponta', 'valor_hora_ponta', 'valor_total']


    # Exibição dos nomes das colunas (necessário adicionar os acentos)
    # Colunas referenciadas de outros modelos devem ter seus nomes corrigidos
    column_labels = {'unidade_consumidora.num_cliente': 'Número do Cliente',
                     'unidade_consumidora.nome': 'Unidade Consumidora',
                     'data_leitura': 'Data da Leitura',
                     'cons_fora_ponta': 'Consumo Fora de Ponta (kWh)',
                     'cons_hora_ponta': 'Consumo Hora Ponta (kWh)',
                     'valor_fora_ponta': 'Valor Fora de Ponta (R$)',
                     'valor_hora_ponta': 'Valor Hora Ponta (R$)',
                     'valor_total': 'Valor Total (R$)'}

    # Lista de filtros que podem ser aplicados em cada coluna
    # Deve-se indicar a coluna e o nome de exibição do filtro
    # Note também que alguns tipos de dados possuem mais de um filtro ('filters.py')

    column_filters = FiltrosStrings(UnidadeConsumidora.nome, 'Nome')
    column_filters.extend(FiltrosDatas(Conta.data_leitura, 'Data da Leitura'))
    column_filters.extend(FiltrosFloats(Conta.cons_fora_ponta, 'Consumo Fora de Ponta'))
    column_filters.extend(FiltrosFloats(Conta.cons_hora_ponta, 'Consumo Hora Ponta'))
    column_filters.extend(FiltrosFloats(Conta.valor_fora_ponta, 'Valor Fora de Ponta'))
    column_filters.extend(FiltrosFloats(Conta.valor_hora_ponta, 'Valor Hora Ponta'))
    column_filters.extend(FiltrosFloats(Conta.valor_total, 'Valor Total'))

    # Definição dos formulários utilizados
    create_form = FormCriarConta
    edit_form = FormEditarConta


########## Registro das Views ##########

# Para cada view, define-se o modelo, a sessão atual de interface com
# o banco de dados, o nome exibido na barra de navegação, uma categoria,
# caso se deseje agrupar modelos, e o endpoint da view (importante para
# que alguns redirecionamentos funcionem corretamente)

##### Acesso ao Sistema #####

admin.add_view(ModelViewCargo(Cargo, db.session,
                              name=Cargo.nome_formatado_plural,
                              endpoint=Cargo.endpoint))

admin.add_view(ModelViewUsuario(Usuario, db.session,
                                name=Usuario.nome_formatado_plural, 
                                endpoint=Usuario.endpoint))

##### Locais #####

admin.add_view(ModelViewInstituicao(Instituicao, db.session, 
                                    name=Instituicao.nome_formatado_plural,
                                    category='Locais',
                                    endpoint=Instituicao.endpoint))

admin.add_view(ModelViewCampus(Campus, db.session,
                               name=Campus.nome_formatado_plural,
                               category='Locais',
                               endpoint=Campus.endpoint))

admin.add_view(ModelViewCentro(Centro, db.session,
                               name=Centro.nome_formatado_plural,
                               category='Locais',
                               endpoint=Centro.endpoint))

admin.add_view(ModelViewDepartamento(Departamento, db.session,
                                     name=Departamento.nome_formatado_plural,
                                     category='Locais',
                                     endpoint=Departamento.endpoint))

admin.add_view(ModelViewBloco(Bloco, db.session,
                              name=Bloco.nome_formatado_plural,
                              category='Locais',
                              endpoint=Bloco.endpoint))

##### Ambientes #####

admin.add_view(ModelViewAmbiente(Ambiente, db.session,
                                 name=Ambiente.nome_formatado_plural,
                                 category='Ambientes',
                                 endpoint=Ambiente.endpoint))

admin.add_view(ModelViewAmbienteInterno(AmbienteInterno, db.session,
                                name=AmbienteInterno.nome_formatado_plural,
                                category='Ambientes',
                                endpoint=AmbienteInterno.endpoint))

admin.add_view(ModelViewAmbienteExterno(AmbienteExterno, db.session,
                                name=AmbienteExterno.nome_formatado_plural,
                                category='Ambientes',
                                endpoint=AmbienteExterno.endpoint))


admin.add_view(ModelViewSubestacaoAbrigada(SubestacaoAbrigada, db.session,
                                name=SubestacaoAbrigada.nome_formatado_plural,
                                category='Ambientes',
                                endpoint=SubestacaoAbrigada.endpoint))

admin.add_view(ModelViewSubestacaoAerea(SubestacaoAerea, db.session,
                                name=SubestacaoAerea.nome_formatado_plural,
                                category='Ambientes',
                                endpoint=SubestacaoAerea.endpoint))

##### Equipamentos #####

admin.add_view(ModelViewEquipamento(Equipamento, db.session,
                                 name=Equipamento.nome_formatado_plural,
                                 category='Equipamentos',
                                 endpoint=Equipamento.endpoint))

admin.add_view(ModelViewExtintor(Extintor, db.session,
                                 name=Extintor.nome_formatado_plural,
                                 category='Equipamentos',
                                 endpoint=Extintor.endpoint))

admin.add_view(ModelViewCondicionadorAr(CondicionadorAr, db.session,
                                 name=CondicionadorAr.nome_formatado_plural,
                                 category='Equipamentos',
                                 endpoint=CondicionadorAr.endpoint))

##### Manutenções #####

admin.add_view(ModelViewManutencao(Manutencao, db.session,
                                   name=Manutencao.nome_formatado_plural,
                                   endpoint=Manutencao.endpoint))

##### Consumo #####

admin.add_view(ModelViewUnidadeResponsavel(UnidadeResponsavel, db.session,
                                    name=UnidadeResponsavel.nome_formatado_plural,
                                    category='Consumo',
                                    endpoint=UnidadeResponsavel.endpoint))

admin.add_view(ModelViewUnidadeConsumidora(UnidadeConsumidora, db.session,
                                    name=UnidadeConsumidora.nome_formatado_plural,
                                    category='Consumo',
                                    endpoint=UnidadeConsumidora.endpoint))

admin.add_view(ModelViewConta(Conta, db.session,
                              name=Conta.nome_formatado_plural,
                              category='Consumo',
                              endpoint=Conta.endpoint))

