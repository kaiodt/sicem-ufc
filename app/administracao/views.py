# coding: utf-8

################################################################################
## SICEM - UFC
################################################################################
## Views do Painel de Administração
################################################################################


from datetime import date, timedelta
from flask import url_for, redirect, request, current_app
from flask_login import current_user
from flask_admin import BaseView, expose
from flask_admin.contrib.geoa import ModelView

from . import admin, typefmt
from .. import db
from .forms import *
from .filters import *
from ..models import *
from ..util import email, tools


########## View Base ##########


class ModelViewBase(ModelView):
    # Formatos de tipos de dados
    column_type_formatters = typefmt.FORMATOS_PADRAO

    # Templates personalizados
    list_template = 'administracao/listar.html'
    details_template = 'administracao/detalhes.html'
    edit_template = 'administracao/editar.html'
    create_template = 'administracao/criar.html'
    
    # Itens por página
    page_size = 10

    # Outras permissões
    can_export = True
    can_view_details = True


########## Views Restritas ##########


# Somente Administradores
class ModelViewAdministrador(ModelViewBase):
    def is_accessible(self):
        return current_user.administrador()


# Administradores e Cadastradores
class ModelViewCadastrador(ModelViewBase):
    def is_accessible(self):
        return current_user.cadastrador()


########## Views dos Modelos do Sistema ##########


# Cargos
class ModelViewCargo(ModelViewAdministrador):
    can_create = False
    can_delete = False

    column_list = ['nome', 'permissoes', 'padrao']

    column_default_sort = 'nome'

    column_sortable_list = ['nome', 'permissoes']

    column_searchable_list = ['nome']

    column_details_list = ['nome', 'permissoes', 'padrao', 'usuarios']

    column_labels = {'permissoes': 'Permissões', 'padrao': 'Padrão',
                     'usuarios': 'Usuários'}

    column_formatters = dict(usuarios=typefmt.formato_relacao)
    
    edit_form = FormEditarCargo


# Usuários
class ModelViewUsuario(ModelViewAdministrador):
    column_list = ['nome', 'email', 'cargo', 'verificado', 'confirmado']

    column_default_sort = 'nome'

    column_sortable_list = ['nome', ('cargo', 'cargo.nome')]

    column_searchable_list = ['nome', 'cargo.nome']

    column_details_list = ['nome', 'email', 'cargo', 'verificado', 'confirmado']

    column_filters = FiltrosStrings(Cargo.nome, 'Cargo')
    column_filters.append(BooleanEqualFilter(Usuario.verificado, 'Verificado'))
    column_filters.append(BooleanEqualFilter(Usuario.confirmado, 'Confirmado'))

    create_form = FormCriarUsuario
    edit_form = FormEditarUsuario


##### Locais #####


# Instituições
class ModelViewInstituicao(ModelViewCadastrador):
    column_list = ['nome']

    column_default_sort = 'nome'

    column_sortable_list = ['nome']

    column_searchable_list = ['nome']

    column_details_list = ['nome', 'campi']

    column_formatters = dict(campi=typefmt.formato_relacao)
    
    create_form = FormCriarInstituicao
    edit_form = FormEditarInstituicao


# Campi
class ModelViewCampus(ModelViewCadastrador):
    column_list = ['nome', 'instituicao', 'mapeamento']

    column_default_sort = 'nome'

    column_sortable_list = ['nome', ('instituicao', 'instituicao.nome')]

    column_searchable_list = ['nome', 'instituicao.nome']

    column_details_list = ['nome', 'instituicao', 'mapeamento', 'centros']

    column_labels = {'instituicao': 'Instituição'}

    column_formatters = dict(centros=typefmt.formato_relacao)

    create_form = FormCriarCampus
    edit_form = FormEditarCampus


    # Após ciração do Campus, criar Centro, Departamento e Bloco para
    # alocar suas subestações
    def after_model_change(self, form, model, is_created):
        if is_created:
            # Criação do Centro
            centro = Centro()
            centro.nome = 'Subestações ' + model.nome
            centro.campus = model

            db.session.add(centro)
            db.session.commit()

            # Criação do Departamento
            departamento = Departamento()
            departamento.nome = 'Subestações ' + model.nome
            departamento.centro = centro

            db.session.add(departamento)
            db.session.commit()   

            # Criação do Bloco
            bloco = Bloco()
            bloco.nome = 'Subestações ' + model.nome
            bloco.departamento = departamento

            db.session.add(bloco)
            db.session.commit() 


# Centros
class ModelViewCentro(ModelViewCadastrador):
    column_list = ['nome', 'campus', 'mapeamento']

    column_default_sort = 'nome'

    column_sortable_list = ['nome', ('campus', 'campus.nome')]

    column_searchable_list = ['nome', 'campus.nome']

    column_details_list = ['nome', 'campus', 'mapeamento', 'departamentos']   

    column_formatters = dict(departamentos=typefmt.formato_relacao)
    
    column_filters = FiltrosStrings(Campus.nome, 'Campus')

    create_form = FormCriarCentro
    edit_form = FormEditarCentro


# Departamentos
class ModelViewDepartamento(ModelViewCadastrador):
    column_list = ['nome', 'centro', 'centro.campus']

    column_default_sort = 'nome'

    column_sortable_list = ['nome', ('centro', 'centro.nome'),
                            ('centro.campus', 'centro.campus.nome')]

    column_searchable_list = ['nome', 'centro.nome', 'centro.campus.nome']

    column_details_list = ['nome', 'centro', 'centro.campus', 'blocos'] 

    column_labels = {'centro.campus': 'Campus'}

    column_formatters = dict(blocos=typefmt.formato_relacao)

    column_filters = FiltrosStrings(Centro.nome, 'Centro')
    column_filters.extend(FiltrosStrings(Campus.nome, 'Campus'))

    create_form = FormCriarDepartamento
    edit_form = FormEditarDepartamento


    def __init__(self, *args, **kwargs):
        super(ModelViewDepartamento, self).__init__(*args, **kwargs)

        # Consertar geração automática de joins

        self._filter_joins[Campus.nome] = [Centro.__table__, Campus.__table__]


# Blocos
class ModelViewBloco(ModelViewCadastrador):
    column_list = ['nome', 'departamento', 'departamento.centro',
                   'departamento.centro.campus', 'localizacao']

    column_default_sort = 'nome'

    column_sortable_list = ['nome', ('departamento', 'departamento.nome'),
                            ('departamento.centro', 'departamento.centro.nome'),
                            ('departamento.centro.campus', 
                             'departamento.centro.campus.nome')]

    column_searchable_list = ['nome', 'departamento.nome', 'departamento.centro.nome', 
                              'departamento.centro.campus.nome']

    column_details_list = ['nome', 'departamento', 'departamento.centro',
                           'departamento.centro.campus', 'localizacao',
                           'ambientes']

    column_labels = {'departamento.centro': 'Centro',
                     'departamento.centro.campus': 'Campus',
                     'localizacao': 'Localização'}

    column_formatters = dict(ambientes=typefmt.formato_relacao_ambientes)

    column_filters = FiltrosStrings(Departamento.nome, 'Departamento')
    column_filters.extend(FiltrosStrings(Centro.nome, 'Centro'))
    column_filters.extend(FiltrosStrings(Campus.nome, 'Campus'))

    create_form = FormCriarBloco
    edit_form = FormEditarBloco


    def __init__(self, *args, **kwargs):
        super(ModelViewBloco, self).__init__(*args, **kwargs)

        # Consertar geração automática de joins

        self._filter_joins[Centro.nome] = [Departamento.__table__, Centro.__table__]

        self._filter_joins[Campus.nome] = [Departamento.__table__, Centro.__table__,
                                           Campus.__table__]


##### Ambientes #####


# Ambientes
class ModelViewAmbiente(ModelViewCadastrador):
    column_list = ['nome', 'tipo', 'bloco', 'bloco.departamento',
                   'bloco.departamento.centro', 'bloco.departamento.centro.campus']

    column_default_sort = 'nome'

    column_sortable_list = ['nome', 'tipo', ('bloco', 'bloco.nome'),
                            ('bloco.departamento', 'bloco.departamento.nome'),
                            ('bloco.departamento.centro', 
                             'bloco.departamento.centro.nome'),
                            ('bloco.departamento.centro.campus', 
                             'bloco.departamento.centro.campus.nome')]

    column_searchable_list = ['nome', 'tipo', 'bloco.nome', 'bloco.departamento.nome',
                              'bloco.departamento.centro.nome',
                              'bloco.departamento.centro.campus.nome']

    column_labels = {'bloco.departamento': 'Departamento',
                     'bloco.departamento.centro': 'Centro',
                     'bloco.departamento.centro.campus': 'Campus'}

    column_filters = FiltrosStrings(Ambiente.tipo, 'Tipo')
    column_filters.extend(FiltrosStrings(Bloco.nome, 'Bloco'))
    column_filters.extend(FiltrosStrings(Departamento.nome, 'Departamento'))
    column_filters.extend(FiltrosStrings(Centro.nome, 'Centro'))
    column_filters.extend(FiltrosStrings(Campus.nome, 'Campus'))


    def __init__(self, *args, **kwargs):
        super(ModelViewAmbiente, self).__init__(*args, **kwargs)

        # Consertar geração automática de joins

        self._filter_joins[Departamento.nome] = [Bloco.__table__, Departamento.__table__]

        self._filter_joins[Centro.nome] = [Bloco.__table__, Departamento.__table__,
                                           Centro.__table__]

        self._filter_joins[Campus.nome] = [Bloco.__table__, Departamento.__table__,
                                           Centro.__table__, Campus.__table__]


    # Escolher tipo de ambiente e redirecionar para view de criação correspondente
    @expose('/new/', methods=['GET', 'POST'])
    def create_view(self):
        form = FormCriarAmbiente()

        if form.validate_on_submit():
            return redirect(url_for(form.tipo_ambiente.data + '.create_view',
                            url=url_for('ambiente.index_view')))
            
        return self.render('administracao/criar_ambiente.html', form=form,
                           return_url=url_for('ambiente.index_view'))


    #  Redirecionar para view de edição correspondente a partir do id do ambiente
    @expose('/edit/')
    def edit_view(self):
        id_ambiente = request.args.get('id')
        tipo_ambiente = Ambiente.query.get(id_ambiente).tipo.lower().replace(' ', '')
        tipo_ambiente = tools.retirar_acentos(tipo_ambiente, 'minusculo')

        return redirect(url_for(tipo_ambiente + '.edit_view',
                                url=url_for('ambiente.index_view'),
                                id=id_ambiente))


    #  Redirecionar para view de detalhes correspondente a partir do id do ambiente
    @expose('/details/')
    def details_view(self):
        id_ambiente = request.args.get('id')
        tipo_ambiente = Ambiente.query.get(id_ambiente).tipo.lower().replace(' ', '')
        tipo_ambiente = tools.retirar_acentos(tipo_ambiente, 'minusculo')

        return redirect(url_for(tipo_ambiente + '.details_view',
                                url=url_for('ambiente.index_view'),
                                id=id_ambiente))


# Ambientes Internos
class ModelViewAmbienteInterno(ModelViewCadastrador):
    column_list = ['nome', 'andar', 'bloco', 'bloco.departamento',
                   'bloco.departamento.centro', 'bloco.departamento.centro.campus']

    column_default_sort = 'nome'

    column_sortable_list = ['nome', 'andar', ('bloco', 'bloco.nome'),
                            ('bloco.departamento', 'bloco.departamento.nome'),
                            ('bloco.departamento.centro', 
                             'bloco.departamento.centro.nome'),
                            ('bloco.departamento.centro.campus', 
                             'bloco.departamento.centro.campus.nome')]

    column_searchable_list = ['nome', 'andar', 'bloco.nome', 'bloco.departamento.nome', 
                              'bloco.departamento.centro.nome',
                              'bloco.departamento.centro.campus.nome']

    column_details_list = ['nome', 'tipo', 'andar', 'bloco', 'bloco.departamento',
                           'bloco.departamento.centro', 'bloco.departamento.centro.campus',
                           'detalhe_localizacao', 'area', 'populacao', 'equipamentos']

    column_labels = {'bloco.departamento': 'Departamento',
                     'bloco.departamento.centro': 'Centro',
                     'bloco.departamento.centro.campus': 'Campus',
                     'detalhe_localizacao': 'Detalhe de Localização',
                     'area': 'Área (m²)',
                     'populacao': 'População'}

    column_formatters = dict(equipamentos=typefmt.formato_relacao_equipamentos)

    column_filters = FiltrosStrings(Bloco.nome, 'Bloco')
    column_filters.extend(FiltrosStrings(AmbienteInterno.andar, 'Andar'))
    column_filters.extend(FiltrosStrings(Departamento.nome, 'Departamento'))
    column_filters.extend(FiltrosStrings(Centro.nome, 'Centro'))
    column_filters.extend(FiltrosStrings(Campus.nome, 'Campus'))

    create_form = FormCriarAmbienteInterno
    edit_form = FormEditarAmbienteInterno


    def __init__(self, *args, **kwargs):
        super(ModelViewAmbienteInterno, self).__init__(*args, **kwargs)

        # Consertar geração automática de joins

        self._filter_joins[Departamento.nome] = [Bloco.__table__, Departamento.__table__]

        self._filter_joins[Centro.nome] = [Bloco.__table__, Departamento.__table__,
                                           Centro.__table__]

        self._filter_joins[Campus.nome] = [Bloco.__table__, Departamento.__table__,
                                           Centro.__table__, Campus.__table__]


# Ambientes Externos
class ModelViewAmbienteExterno(ModelViewCadastrador):
    column_list = ['nome', 'bloco', 'bloco.departamento', 'bloco.departamento.centro',
                   'bloco.departamento.centro.campus']

    column_default_sort = 'nome'

    column_sortable_list = ['nome', ('bloco', 'bloco.nome'),
                            ('bloco.departamento', 'bloco.departamento.nome'),
                            ('bloco.departamento.centro', 
                             'bloco.departamento.centro.nome'),
                            ('bloco.departamento.centro.campus', 
                             'bloco.departamento.centro.campus.nome')]

    column_searchable_list = ['nome', 'bloco.nome', 'bloco.departamento.nome', 
                              'bloco.departamento.centro.nome',
                              'bloco.departamento.centro.campus.nome']

    column_details_list = ['nome', 'tipo', 'bloco', 'bloco.departamento',
                           'bloco.departamento.centro', 'bloco.departamento.centro.campus',
                           'detalhe_localizacao', 'equipamentos']

    column_labels = {'bloco.departamento': 'Departamento',
                     'bloco.departamento.centro': 'Centro',
                     'bloco.departamento.centro.campus': 'Campus',
                     'detalhe_localizacao': 'Detalhe de Localização'}

    column_formatters = dict(equipamentos=typefmt.formato_relacao_equipamentos)

    column_filters = FiltrosStrings(Bloco.nome, 'Bloco')
    column_filters.extend(FiltrosStrings(Departamento.nome, 'Departamento'))
    column_filters.extend(FiltrosStrings(Centro.nome, 'Centro'))
    column_filters.extend(FiltrosStrings(Campus.nome, 'Campus'))

    create_form = FormCriarAmbienteExterno
    edit_form = FormEditarAmbienteExterno


    def __init__(self, *args, **kwargs):
        super(ModelViewAmbienteExterno, self).__init__(*args, **kwargs)

        # Consertar geração automática de joins

        self._filter_joins[Departamento.nome] = [Bloco.__table__, Departamento.__table__]

        self._filter_joins[Centro.nome] = [Bloco.__table__, Departamento.__table__,
                                           Centro.__table__]

        self._filter_joins[Campus.nome] = [Bloco.__table__, Departamento.__table__,
                                           Centro.__table__, Campus.__table__]


# Subestações Abrigadas
class ModelViewSubestacaoAbrigada(ModelViewCadastrador):
    column_list = ['nome', 'bloco.departamento.centro.campus', 'localizacao']

    column_default_sort = 'nome'

    column_sortable_list = ['nome',
                            ('bloco.departamento.centro.campus', 
                             'bloco.departamento.centro.campus.nome')]

    column_searchable_list = ['nome', 'bloco.departamento.centro.campus.nome']

    column_details_list = ['nome', 'tipo', 'bloco', 'bloco.departamento',
                           'bloco.departamento.centro', 'bloco.departamento.centro.campus',
                           'localizacao', 'detalhe_localizacao', 'equipamentos']

    column_labels = {'bloco.departamento': 'Departamento',
                     'bloco.departamento.centro': 'Centro',
                     'bloco.departamento.centro.campus': 'Campus',
                     'localizacao': 'Localização',
                     'detalhe_localizacao': 'Detalhe de Localização'}

    column_formatters = dict(equipamentos=typefmt.formato_relacao_equipamentos)

    column_filters = FiltrosStrings(Campus.nome, 'Campus')

    create_form = FormCriarSubestacaoAbrigada
    edit_form = FormEditarSubestacaoAbrigada


    def __init__(self, *args, **kwargs):
        super(ModelViewSubestacaoAbrigada, self).__init__(*args, **kwargs)

        # Consertar geração automática de joins

        self._filter_joins[Campus.nome] = [Bloco.__table__, Departamento.__table__,
                                           Centro.__table__, Campus.__table__]


# Subestações Aéreas
class ModelViewSubestacaoAerea(ModelViewCadastrador):
    column_list = ['nome', 'bloco.departamento.centro.campus', 'localizacao']

    column_default_sort = 'nome'

    column_sortable_list = ['nome',
                            ('bloco.departamento.centro.campus', 
                             'bloco.departamento.centro.campus.nome')]

    column_searchable_list = ['nome', 'bloco.departamento.centro.campus.nome']

    column_details_list = ['nome', 'tipo', 'bloco', 'bloco.departamento',
                           'bloco.departamento.centro', 'bloco.departamento.centro.campus',
                           'localizacao', 'detalhe_localizacao', 'equipamentos']

    column_labels = {'bloco.departamento': 'Departamento',
                     'bloco.departamento.centro': 'Centro',
                     'bloco.departamento.centro.campus': 'Campus',
                     'localizacao': 'Localização',
                     'detalhe_localizacao': 'Detalhe de Localização'}

    column_formatters = dict(equipamentos=typefmt.formato_relacao_equipamentos)

    column_filters = FiltrosStrings(Campus.nome, 'Campus')

    create_form = FormCriarSubestacaoAerea
    edit_form = FormEditarSubestacaoAerea


    def __init__(self, *args, **kwargs):
        super(ModelViewSubestacaoAerea, self).__init__(*args, **kwargs)

        # Consertar geração automática de joins

        self._filter_joins[Campus.nome] = [Bloco.__table__, Departamento.__table__,
                                           Centro.__table__, Campus.__table__]


##### Equipamentos #####


# Equipamentos
class ModelViewEquipamento(ModelViewCadastrador):
    column_list = ['tombamento', 'tipo_equipamento', 'categoria_equipamento',
                   'fabricante', 'ambiente.nome', 'ambiente.bloco',
                   'ambiente.bloco.departamento', 'ambiente.bloco.departamento.centro',
                   'ambiente.bloco.departamento.centro.campus', 'em_uso', 'em_manutencao']

    column_default_sort = 'tombamento'

    column_sortable_list = ['tombamento', 'tipo_equipamento', 'categoria_equipamento', 
                            'fabricante', 'ambiente.nome',
                            ('ambiente.bloco', 'ambiente.bloco.nome'),
                            ('ambiente.bloco.departamento', 
                             'ambiente.bloco.departamento.nome'),
                            ('ambiente.bloco.departamento.centro', 
                             'ambiente.bloco.departamento.centro.nome'),
                            ('ambiente.bloco.departamento.centro.campus', 
                             'ambiente.bloco.departamento.centro.campus.nome')]

    column_searchable_list = ['tombamento', 'tipo_equipamento', 'categoria_equipamento',
                              'fabricante', 'ambiente.nome', 'ambiente.bloco.nome',
                              'ambiente.bloco.departamento.nome',
                              'ambiente.bloco.departamento.centro.nome',
                              'ambiente.bloco.departamento.centro.campus.nome']

    column_labels = {'ambiente.nome': 'Ambiente',
                     'tipo_equipamento': 'Tipo',
                     'categoria_equipamento': 'Categoria',
                     'ambiente.bloco': 'Bloco',
                     'ambiente.bloco.departamento': 'Departamento',
                     'ambiente.bloco.departamento.centro': 'Centro',
                     'ambiente.bloco.departamento.centro.campus': 'Campus',
                     'em_manutencao': 'Em Manutenção'}

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


    def __init__(self, *args, **kwargs):
        super(ModelViewEquipamento, self).__init__(*args, **kwargs)

        # Consertar geração automática de joins

        self._filter_joins[Bloco.nome] = [Ambiente.__table__, Bloco.__table__]

        self._filter_joins[Departamento.nome] = [Ambiente.__table__, Bloco.__table__,
                                                 Departamento.__table__]

        self._filter_joins[Centro.nome] = [Ambiente.__table__, Bloco.__table__,
                                           Departamento.__table__, Centro.__table__]

        self._filter_joins[Campus.nome] = [Ambiente.__table__, Bloco.__table__,
                                           Departamento.__table__,Centro.__table__,
                                           Campus.__table__]


    # Escolher tipo de equipamento e redirecionar para view de criação correspondente
    @expose('/new/', methods=['GET', 'POST'])
    def create_view(self):
        form = FormCriarEquipamento()

        if form.validate_on_submit():
            return redirect(url_for(form.tipo_equipamento.data + '.create_view',
                            url=url_for('equipamento.index_view')))
            
        return self.render('administracao/criar_equipamento.html', form=form,
                           return_url=url_for('equipamento.index_view'))


    #  Redirecionar para view de edição correspondente a partir do id do equipamento
    @expose('/edit/')
    def edit_view(self):
        id_equipamento = request.args.get('id')
        tipo_equipamento = \
            Equipamento.query.get(id_equipamento).tipo_equipamento.lower().replace(' ', '')
        tipo_equipamento = tools.retirar_acentos(tipo_equipamento, 'minusculo')

        return redirect(url_for(tipo_equipamento + '.edit_view',
                                url = url_for('equipamento.index_view'),
                                id=id_equipamento))


    #  Redirecionar para view de detalhes correspondente a partir do id do equipamento
    @expose('/details/')
    def details_view(self):
        id_equipamento = request.args.get('id')
        tipo_equipamento = \
            Equipamento.query.get(id_equipamento).tipo_equipamento.lower().replace(' ', '')
        tipo_equipamento = tools.retirar_acentos(tipo_equipamento, 'minusculo')

        return redirect(url_for(tipo_equipamento + '.details_view',
                                url = url_for('equipamento.index_view'),
                                id=id_equipamento))


# Extintores
class ModelViewExtintor(ModelViewCadastrador):
    column_list = ['tombamento', 'classificacao', 'carga_nominal', 'fabricante',
                   'ambiente.nome', 'ambiente.bloco', 'ambiente.bloco.departamento',
                   'ambiente.bloco.departamento.centro',
                   'ambiente.bloco.departamento.centro.campus',
                   'proxima_manutencao', 'em_uso', 'em_manutencao']

    column_default_sort = 'tombamento'

    column_sortable_list = ['tombamento', 'classificacao', 'carga_nominal', 'fabricante',
                            'ambiente.nome', ('ambiente.bloco', 'ambiente.bloco.nome'),
                            ('ambiente.bloco.departamento', 
                             'ambiente.bloco.departamento.nome'),
                            ('ambiente.bloco.departamento.centro', 
                             'ambiente.bloco.departamento.centro.nome'),
                            ('ambiente.bloco.departamento.centro.campus', 
                             'ambiente.bloco.departamento.centro.campus.nome'),
                            'proxima_manutencao']

    column_searchable_list = ['tombamento', 'classificacao', 'ambiente.nome',
                              'fabricante', 'ambiente.bloco.nome',
                              'ambiente.bloco.departamento.nome',
                              'ambiente.bloco.departamento.centro.nome',
                              'ambiente.bloco.departamento.centro.campus.nome']

    column_details_list = ['tombamento', 'tipo_equipamento', 'categoria_equipamento',
                           'classificacao', 'carga_nominal', 'fabricante',
                           'ambiente.nome', 'ambiente.bloco', 'ambiente.bloco.departamento',
                           'ambiente.bloco.departamento.centro',
                           'ambiente.bloco.departamento.centro.campus',
                           'info_adicional', 'intervalo_manutencao', 
                           'proxima_manutencao', 'manutencoes', 'em_uso', 'em_manutencao',
                           'inicio_manutencao']

    column_labels = {'tipo_equipamento': 'Tipo',
                     'categoria_equipamento': 'Categoria',
                     'classificacao': 'Classificação',
                     'ambiente.nome': 'Ambiente',
                     'ambiente.bloco': 'Bloco',
                     'ambiente.bloco.departamento': 'Departamento',
                     'ambiente.bloco.departamento.centro': 'Centro',
                     'ambiente.bloco.departamento.centro.campus': 'Campus',
                     'intervalo_manutencao': 'Intervalo de Manutenção',
                     'manutencoes': 'Manutenções',
                     'proxima_manutencao': 'Próxima Manutenção',
                     'info_adicional': 'Informações Adicionais',
                     'em_manutencao': 'Em Manutenção',
                     'inicio_manutencao': 'Início da Manutenção'}

    column_formatters = dict(manutencoes=typefmt.formato_relacao_manutencoes)

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

    create_form = FormCriarExtintor
    edit_form = FormEditarExtintor


    def __init__(self, *args, **kwargs):
        super(ModelViewExtintor, self).__init__(*args, **kwargs)

        # Consertar geração automática de joins

        self._filter_joins[Bloco.nome] = [Ambiente.__table__, Bloco.__table__]

        self._filter_joins[Departamento.nome] = [Ambiente.__table__, Bloco.__table__,
                                                 Departamento.__table__]

        self._filter_joins[Centro.nome] = [Ambiente.__table__, Bloco.__table__,
                                           Departamento.__table__, Centro.__table__]

        self._filter_joins[Campus.nome] = [Ambiente.__table__, Bloco.__table__,
                                           Departamento.__table__,Centro.__table__,
                                           Campus.__table__]


    # Após criação de um novo equipamento, redirecionar para criação de sua
    # manutenção inicial
    def get_save_return_url(self, model, is_created):
        if is_created and not model.manutencoes.all():
            return url_for('manutencao.manutencao_inicial', id=model.id)
        
        # Caso haja apenas edição, redirecionar para view de listagem
        return self.get_url('.index_view')


# Condicionadores de Ar
class ModelViewCondicionadorAr(ModelViewCadastrador):
    column_list = ['tombamento', 'classificacao', 'cap_refrigeracao', 'pot_nominal',
                   'tensao_alimentacao', 'eficiencia', 'fabricante', 
                   'ambiente.nome', 'ambiente.bloco', 'ambiente.bloco.departamento',
                   'ambiente.bloco.departamento.centro',
                   'ambiente.bloco.departamento.centro.campus',
                   'proxima_manutencao', 'em_uso', 'em_manutencao']

    column_default_sort = 'tombamento'

    column_sortable_list = ['tombamento', 'classificacao', 'cap_refrigeracao', 'pot_nominal',
                            'tensao_alimentacao', 'eficiencia', 'fabricante',
                            'ambiente.nome', ('ambiente.bloco', 'ambiente.bloco.nome'),
                            ('ambiente.bloco.departamento', 
                             'ambiente.bloco.departamento.nome'),
                            ('ambiente.bloco.departamento.centro', 
                             'ambiente.bloco.departamento.centro.nome'),
                            ('ambiente.bloco.departamento.centro.campus', 
                             'ambiente.bloco.departamento.centro.campus.nome'),
                            'proxima_manutencao']

    column_searchable_list = ['tombamento', 'classificacao', 'ambiente.nome',
                              'fabricante', 'ambiente.bloco.nome',
                              'ambiente.bloco.departamento.nome',
                              'ambiente.bloco.departamento.centro.nome',
                              'ambiente.bloco.departamento.centro.campus.nome']

    column_details_list = ['tombamento', 'tipo_equipamento', 'categoria_equipamento',
                           'classificacao', 'cap_refrigeracao', 'pot_nominal', 'tensao_alimentacao',
                           'eficiencia', 'fabricante', 'ambiente.nome', 'ambiente.bloco',
                           'ambiente.bloco.departamento', 'ambiente.bloco.departamento.centro',
                           'ambiente.bloco.departamento.centro.campus',
                           'info_adicional', 'intervalo_manutencao',
                           'proxima_manutencao', 'manutencoes', 'em_uso', 'em_manutencao',
                           'inicio_manutencao']

    column_labels = {'tipo_equipamento': 'Tipo',
                     'categoria_equipamento': 'Categoria',
                     'classificacao': 'Classificação',
                     'cap_refrigeracao': 'Cap. de Refrigeração',
                     'pot_nominal': 'Pot. Nominal',
                     'tensao_alimentacao': 'Tensão de Alimentação',
                     'eficiencia': 'Eficiência',
                     'ambiente.nome': 'Ambiente',
                     'ambiente.bloco': 'Bloco',
                     'ambiente.bloco.departamento': 'Departamento',
                     'ambiente.bloco.departamento.centro': 'Centro',
                     'ambiente.bloco.departamento.centro.campus': 'Campus',
                     'intervalo_manutencao': 'Intervalo de Manutenção',
                     'manutencoes': 'Manutenções',
                     'proxima_manutencao': 'Próxima Manutenção',
                     'info_adicional': 'Informações Adicionais',
                     'em_manutencao': 'Em Manutenção',
                     'inicio_manutencao': 'Início da Manutenção'}

    column_formatters = dict(manutencoes=typefmt.formato_relacao_manutencoes)

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

    create_form = FormCriarCondicionadorAr
    edit_form = FormEditarCondicionadorAr


    def __init__(self, *args, **kwargs):
        super(ModelViewCondicionadorAr, self).__init__(*args, **kwargs)

        # Consertar geração automática de joins

        self._filter_joins[Bloco.nome] = [Ambiente.__table__, Bloco.__table__]

        self._filter_joins[Departamento.nome] = [Ambiente.__table__, Bloco.__table__,
                                                 Departamento.__table__]

        self._filter_joins[Centro.nome] = [Ambiente.__table__, Bloco.__table__,
                                           Departamento.__table__, Centro.__table__]

        self._filter_joins[Campus.nome] = [Ambiente.__table__, Bloco.__table__,
                                           Departamento.__table__,Centro.__table__,
                                           Campus.__table__]


    # Após criação de um novo equipamento, redirecionar para criação de sua
    # manutenção inicial
    def get_save_return_url(self, model, is_created):
        if is_created and not model.manutencoes.all():
            return url_for('manutencao.manutencao_inicial', id=model.id)
        
        # Caso haja apenas edição, redirecionar para view de listagem
        return self.get_url('.index_view')


##### Manutenções #####


# Manutenções
class ModelViewManutencao(ModelViewCadastrador):
    column_list = ['num_ordem_servico', 'data_abertura', 'data_conclusao',
                   'tipo_manutencao', 'equipamento.tipo_equipamento',
                   'equipamento.tombamento', 'equipamento.ambiente.nome',
                   'equipamento.ambiente.bloco', 'equipamento.ambiente.bloco.departamento',
                   'equipamento.ambiente.bloco.departamento.centro',
                   'equipamento.ambiente.bloco.departamento.centro.campus',
                   'status']

    column_default_sort = ('data_abertura', True)

    column_sortable_list = ['num_ordem_servico', 'data_abertura', 'data_conclusao',
                            'tipo_manutencao', 'equipamento.tipo_equipamento',
                            'equipamento.tombamento', 'equipamento.ambiente.nome',
                            ('equipamento.ambiente.bloco',
                             'equipamento.ambiente.bloco.nome'),
                            ('equipamento.ambiente.bloco.departamento',
                             'equipamento.ambiente.bloco.departamento.nome'),
                            ('equipamento.ambiente.bloco.departamento.centro',
                             'equipamento.ambiente.bloco.departamento.centro.nome'),
                            ('equipamento.ambiente.bloco.departamento.centro.campus',
                             'equipamento.ambiente.bloco.departamento.centro.campus.nome'),
                            'status']
    
    column_searchable_list = ['num_ordem_servico', 'tipo_manutencao',
                              'equipamento.tipo_equipamento', 'equipamento.tombamento',
                              'equipamento.ambiente.nome', 'equipamento.ambiente.bloco.nome',
                              'equipamento.ambiente.bloco.departamento.nome',
                              'equipamento.ambiente.bloco.departamento.centro.nome',
                              'equipamento.ambiente.bloco.departamento.centro.campus.nome',
                              'status']
    
    column_details_list = ['num_ordem_servico', 'data_abertura', 'data_conclusao',
                           'tipo_manutencao', 'equipamento.tipo_equipamento',
                           'equipamento.tombamento', 'equipamento.ambiente.nome',
                           'equipamento.ambiente.bloco',
                           'equipamento.ambiente.bloco.departamento',
                           'equipamento.ambiente.bloco.departamento.centro',
                           'equipamento.ambiente.bloco.departamento.centro.campus',
                           'descricao_servico', 'status']

    column_labels = {'num_ordem_servico': 'Ordem de Serviço',
                     'data_abertura': 'Data de Abertura',
                     'data_conclusao': 'Data de Conclusão',
                     'tipo_manutencao': 'Tipo de Manutenção',
                     'equipamento.tipo_equipamento': 'Tipo de Equipamento',
                     'equipamento.tombamento': 'Tombamento',
                     'equipamento.ambiente.nome': 'Ambiente',
                     'equipamento.ambiente.bloco': 'Bloco',
                     'equipamento.ambiente.bloco.departamento': 'Departamento',
                     'equipamento.ambiente.bloco.departamento.centro': 'Centro',
                     'equipamento.ambiente.bloco.departamento.centro.campus': 'Campus',
                     'descricao_servico': 'Descrição do Serviço'}

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

    create_form = FormCriarManutencao
    edit_form = FormEditarManutencao


    def __init__(self, *args, **kwargs):
        super(ModelViewManutencao, self).__init__(*args, **kwargs)

        # Consertar geração automática de joins

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


    # Procedimentos adicionais quando uma manutenção é criada ou editada
    def after_model_change(self, form, model, is_created):
        # Equipamento alvo da manutenção
        equipamento = model.equipamento

        # Manutenções concluídas
        if model.status == 'Concluída':
            # Mudar o status "em manutenção" do equipamento
            equipamento.em_manutencao = False

            # Limpar o campo de data de abertura de manutenção do equipamento
            equipamento.inicio_manutencao = None

            # Para o caso de troca, o equipamento antigo é colocado fora de uso
            if model.tipo_manutencao == 'Troca':
                equipamento.em_uso = False

                db.session.add(equipamento)
                db.session.commit()
            
            # Para outros tipos de manutenção, a data da próxima manutenção é calculada
            else:        
                delta = timedelta(days = 30 * equipamento.intervalo_manutencao)
                equipamento.proxima_manutencao = \
                    model.data_conclusao + delta

                db.session.add(equipamento)
                db.session.commit()

        # Manutenções abertas
        else:
            # Atualizar o status "em manutenção" do equipamento
            equipamento.em_manutencao = True

            # Atualizar o campo de data de abertura de manutenção do equipamento
            equipamento.inicio_manutencao = model.data_abertura


    # Quando uma manutenção tipo troca é concluída, redirecionar para criação de um
    # novo equipamento, que substitui o antigo
    def get_save_return_url(self, model, is_created):
        if model.status == 'Concluída' and model.tipo_manutencao == 'Troca':
            equipamento = model.equipamento

            tipo_equipamento = \
                equipamento.tipo_equipamento.lower().replace(' ', '')
            tipo_equipamento = tools.retirar_acentos(tipo_equipamento, 'minusculo')

            return url_for(tipo_equipamento + '.create_view')

        # Para outros casos, redirecionar para view de listagem
        return request.args.get('url') or self.get_url('.index_view')


    # Página de cadastro de manutenção inicial
    # São dadas como opções uma manutenção inicial padrão ou personalizada
    @expose('/manutencao-inicial')
    def manutencao_inicial(self):
        id_equipamento = request.args.get('id')

        return self.render('administracao/manutencao_inicial.html', id=id_equipamento)


    # Criação da manutenção inicial padrão
    @expose('/manutencao-inicial-padrao')
    def manutencao_inicial_padrao(self):
        id_equipamento = request.args.get('id')
        equipamento = Equipamento.query.get(id_equipamento)

        manutencao = Manutencao()
        manutencao.num_ordem_servico = 0
        manutencao.data_abertura = date.today()
        manutencao.data_conclusao = date.today()
        manutencao.tipo_manutencao = 'Inicial'
        manutencao.equipamento = equipamento
        manutencao.descricao_servico = 'Manutenção inicial padrão criada automaticamente.'
        manutencao.status = 'Concluída'

        # Cálculo da próxima manutenção a ser realizada no equipamento
        delta = timedelta(days = 30 * equipamento.intervalo_manutencao)
        equipamento.proxima_manutencao = \
            manutencao.data_conclusao + delta

        db.session.add(manutencao)
        db.session.add(equipamento)
        db.session.commit()

        return redirect(url_for('equipamento.index_view'))


########## Registro das Views ##########


# Acesso ao Sistema

admin.add_view(ModelViewCargo(Cargo, db.session, name='Cargos'))

admin.add_view(ModelViewUsuario(Usuario, db.session, name='Usuários'))

# Locais

admin.add_view(ModelViewInstituicao(Instituicao, db.session, 
                                    name='Instituições', category='Locais'))

admin.add_view(ModelViewCampus(Campus, db.session,
                               name='Campi', category='Locais'))

admin.add_view(ModelViewCentro(Centro, db.session,
                               name='Centros', category='Locais'))

admin.add_view(ModelViewDepartamento(Departamento, db.session,
                                     name='Departamentos', category='Locais'))

admin.add_view(ModelViewBloco(Bloco, db.session,
                              name='Blocos', category='Locais'))

# Ambientes

admin.add_view(ModelViewAmbiente(Ambiente, db.session,
                                 name='Ambientes', category='Ambientes'))

admin.add_view(ModelViewAmbienteInterno(AmbienteInterno, db.session,
                                name='Ambientes Internos', category='Ambientes'))

admin.add_view(ModelViewAmbienteExterno(AmbienteExterno, db.session,
                                name='Ambientes Externos', category='Ambientes'))


admin.add_view(ModelViewSubestacaoAbrigada(SubestacaoAbrigada, db.session,
                                name='Subestações Abrigadas', category='Ambientes'))

admin.add_view(ModelViewSubestacaoAerea(SubestacaoAerea, db.session,
                                name='Subestações Aéreas', category='Ambientes'))

# Equipamentos

admin.add_view(ModelViewEquipamento(Equipamento, db.session,
                                 name='Equipamentos', category='Equipamentos'))

admin.add_view(ModelViewExtintor(Extintor, db.session,
                                 name='Extintores', category='Equipamentos'))

admin.add_view(ModelViewCondicionadorAr(CondicionadorAr, db.session,
                                 name='Condicionadores de Ar', category='Equipamentos'))

# Manutenções

admin.add_view(ModelViewManutencao(Manutencao, db.session, name='Manutenções'))

