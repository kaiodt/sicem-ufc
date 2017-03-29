# coding: utf-8

################################################################################
## SICEM - UFC
################################################################################
## Views do Blueprint Principal
################################################################################

from datetime import date
from flask import render_template, redirect, url_for, request, current_app
from flask_login import login_required
from shapely import wkb     # para converter na view function 'equipamentos'

from . import principal
from .filters import *
from .forms import FormEmailContato
from ..models import *
from ..util.email import enviar_email


########## Rotas ##########


# Página Inicial
@principal.route('/')
def home():
    return render_template('principal/home.html')


# Página do Mapa
@principal.route('/mapa')
def mapa():
    # Pegando do banco de dados todos os elementos que serão inseridos no mapa
    blocos = Bloco.query.all()
    subestacoes_abrigadas = SubestacaoAbrigada.query.all()
    subestacoes_aereas = SubestacaoAerea.query.all()
    centros = Centro.query.all()
    campi = Campus.query.all()
    
    # Listas que conterão dicionários com o par objeto e localização (convertida para números de lat. e long. que podem ser processados pela extensão Leaflet)
    lista_blocos = []
    lista_subestacoes_abrigadas = []
    lista_subestacoes_aereas = []    
    lista_centros = []
    lista_campi = []

    # Processos iterativos que geram essas listas de dicionários
    for bloco in blocos:
        if bloco.localizacao is not None:    # se o bloco tiver uma localização registrada ele será adicionado à lista que será levada ao mapa
            point_temp = wkb.loads(bytes(bloco.localizacao.data))
            localizacao_temp = [point_temp.y, point_temp.x]
            lista_blocos.append({"objeto_bloco": bloco,
                                 "localizacao":  localizacao_temp
                })

    for subestacao_abrigada in subestacoes_abrigadas:
        if subestacao_abrigada.localizacao is not None:
            point_temp = wkb.loads(bytes(subestacao_abrigada.localizacao.data))
            localizacao_temp = [point_temp.y, point_temp.x]
            lista_subestacoes_abrigadas.append({"objeto_subestacao_abrigada":    subestacao_abrigada,
                                                "localizacao":                   localizacao_temp,
                })

    for subestacao_aerea in subestacoes_aereas:
        if subestacao_aerea.localizacao is not None:
            point_temp = wkb.loads(bytes(subestacao_aerea.localizacao.data))
            localizacao_temp = [point_temp.y, point_temp.x]
            lista_subestacoes_aereas.append({"objeto_subestacao_aerea":    subestacao_aerea,
                                             "localizacao":                localizacao_temp
                })

    for centro in centros:
        if centro.mapeamento is not None:
            map_temp = wkb.loads(bytes(centro.mapeamento.data)) # convertendo de um WKBElement para formato da biblioteca shapely
            mapeamento = []
            for area in list(map_temp):    # list(map_temp) retorna uma lista com os vários polygonos (ou áreas) do centro
                                           # formato: lista de tuples contendo dois elementos cada (latitude e longitude) 
                                           # Ex: [(1, 0),(1, 1),(0, 1)]
                # trocar (x,y) => (y,x)
                coordenadas_temp = []
                for ponto in list(area.exterior.coords):
                    coordenadas_temp.append([ponto[1], ponto[0]])
                mapeamento.append(coordenadas_temp)    # mapeamento é uma lista de áreas
            lista_centros.append({"objeto_centro":          centro,
                                  "mapeamento":             mapeamento,
                                  "lista_departamentos":    centro.departamentos.all()
                })

    for campus in campi:
        if campus.mapeamento is not None:
            map_temp = wkb.loads(bytes(campus.mapeamento.data))
            mapeamento = []
            for area in list(map_temp):
                coordenadas_temp = []
                for ponto in list(area.exterior.coords):
                    coordenadas_temp.append([ponto[1], ponto[0]])
                mapeamento.append(coordenadas_temp)
            lista_campi.append({"objeto_campus":        campus,
                                "mapeamento":           mapeamento
                })


    return render_template('principal/mapa.html', 
                            lista_blocos = lista_blocos,
                            lista_subestacoes_abrigadas = lista_subestacoes_abrigadas,
                            lista_subestacoes_aereas = lista_subestacoes_aereas,
                            lista_centros = lista_centros,
                            lista_campi = lista_campi)


# Página de Equipamentos de um Bloco (Restrita a Usuários)
@principal.route('/equipamentos/bloco')
@login_required
def equipamentos_bloco():
    id_bloco = request.args.get('id')
    bloco = Bloco.query.get(id_bloco)
    ambientes = bloco.ambientes
    local_equipamentos = []

    for ambiente in ambientes:
        local_equipamentos.extend(ambiente.equipamentos)

    dict_local_equipamentos = {}    # dicionário com a key como o tipo do equipamento e seu valor a lista de equipamentos

    for equipamento in local_equipamentos:
        if equipamento.em_uso:  # considerando apenas equipamentos em uso
            if equipamento.tipo_equipamento in dict_local_equipamentos:    # se o tipo de equipamento já possui uma key no dicionário
                dict_local_equipamentos[equipamento.tipo_equipamento].append(equipamento) # o equipamento é adicionado à lista referente à key
            else:
                dict_local_equipamentos[equipamento.tipo_equipamento] = [equipamento] # se não crio uma lista começando com o equipamento em questão

    ordem_alfa_dict = sorted(dict_local_equipamentos.iteritems())   # lista de tuples no formato (key, lista_equipamentos)
                                                                    # com keys em ordem alfabética
    return render_template('principal/equipamentos_bloco.html', 
                        bloco = bloco, ordem_alfa_dict = ordem_alfa_dict)


# Página de Equipamentos
@principal.route('/equipamentos')
@login_required
def equipamentos():
    # Query de equipamentos (adicionando joins de outras tabelas)

    equip_query = Equipamento.query.join(Ambiente, Bloco, Departamento, Centro, Campus)

    # Query de equipamentos em uso

    equip_em_uso_query = equip_query.filter(Equipamento.em_uso==True)

    # Definição dos filtros que podem ser aplicados

    filtros = FiltrosOpcoes(equip_em_uso_query, Equipamento.tipo_equipamento,
                            u'Tipo')
    filtros.extend(FiltrosOpcoes(equip_em_uso_query, Equipamento.categoria_equipamento,
                                 u'Categoria'))
    filtros.extend(FiltrosOpcoes(equip_em_uso_query, Ambiente.nome,
                                 u'Ambiente'))
    filtros.extend(FiltrosOpcoes(equip_em_uso_query, Bloco.nome,
                                 u'Bloco'))
    filtros.extend(FiltrosOpcoes(equip_em_uso_query, Departamento.nome,
                                 u'Departamento'))
    filtros.extend(FiltrosOpcoes(equip_em_uso_query, Centro.nome,
                                 u'Centro'))
    filtros.extend(FiltrosOpcoes(equip_em_uso_query, Campus.nome,
                                 u'Campus'))

    # Criação dos grupos de filtros e dicionário de indexação dos filtros

    grupos_filtros, indice_filtros = agrupar_filtros(filtros)

    # Processamento dos grupos de filtros para exibição no template

    grupos_template = grupos_filtros_template(grupos_filtros)

    # Filtros selecionados (a partir da query string)

    filtros_ativos = filtros_selecionados(request, indice_filtros)

    # Aplicação dos filtros

    equip_filtrados_query = aplicar_filtros(equip_em_uso_query, 
                                            filtros, filtros_ativos)

    # Paginação dos resultados

    page = request.args.get('page', 1, type=int)

    pagination = equip_filtrados_query.paginate(page, per_page=10, error_out=False)

    # Lista de equipamentos após paginação

    equip_filtrados = pagination.items

    return render_template('principal/equipamentos.html',
                           equipamentos=equip_filtrados,
                           pagination=pagination,
                           filtros=filtros,
                           filter_groups=grupos_template,
                           active_filters=filtros_ativos,
                           url_inicial=url_for('principal.equipamentos'))


# Página de Controle de Manutenções (Restrita a Usuários)
# Aba Manutenções Abertas
@principal.route('/manutencoes-abertas')
@login_required
def manutencoes_abertas():
    # Query de equipamentos (adicionando joins de outras tabelas)

    equip_query = Equipamento.query.join(Ambiente, Bloco, Departamento, Centro, Campus)

    # Query de equipamentos em uso

    equip_em_uso_query = equip_query.filter(Equipamento.em_uso==True)

    # Query de equipamentos em uso com manutenção aberta

    equip_em_manutencao_query = equip_em_uso_query.filter(Equipamento.em_manutencao==True)

    # Definição dos filtros que podem ser aplicados

    filtros = FiltrosOpcoes(equip_em_manutencao_query, Equipamento.tipo_equipamento,
                            u'Tipo de Equipamento')
    filtros.extend(FiltrosOpcoes(equip_em_manutencao_query, Ambiente.nome,
                                 u'Ambiente'))
    filtros.extend(FiltrosOpcoes(equip_em_manutencao_query, Bloco.nome,
                                 u'Bloco'))
    filtros.extend(FiltrosOpcoes(equip_em_manutencao_query, Departamento.nome,
                                 u'Departamento'))
    filtros.extend(FiltrosOpcoes(equip_em_manutencao_query, Centro.nome,
                                 u'Centro'))
    filtros.extend(FiltrosOpcoes(equip_em_manutencao_query, Campus.nome,
                                 u'Campus'))
    filtros.extend(FiltrosDatas(Equipamento.inicio_manutencao, u'Data de Abertura'))

    # Criação dos grupos de filtros e dicionário de indexação dos filtros

    grupos_filtros, indice_filtros = agrupar_filtros(filtros)

    # Processamento dos grupos de filtros para exibição no template

    grupos_template = grupos_filtros_template(grupos_filtros)

    # Filtros selecionados (a partir da query string)

    filtros_ativos = filtros_selecionados(request, indice_filtros)

    # Aplicação dos filtros

    equip_filtrados_query = aplicar_filtros(equip_em_manutencao_query, 
                                            filtros, filtros_ativos)

    # Paginação dos resultados (ordenados por data de abertura)

    page = request.args.get('page', 1, type=int)

    pagination = equip_filtrados_query.order_by(Equipamento.inicio_manutencao).paginate(
        page, per_page=10, error_out=False)

    # Lista de equipamentos após paginação

    equip_filtrados = pagination.items

    return render_template('principal/manutencoes_abertas.html',
                           equip_man_aberta=equip_filtrados,
                           data_hoje=date.today(),
                           pagination=pagination,
                           filtros=filtros,
                           filter_groups=grupos_template,
                           active_filters=filtros_ativos,
                           url_inicial=url_for('principal.manutencoes_abertas'))


# Página de Controle de Manutenções (Restrita a Usuários)
# Aba Manutenções Agendadas
@principal.route('/manutencoes-agendadas')
@login_required
def manutencoes_agendadas():
    # Query de equipamentos (adicionando joins de outras tabelas)

    equip_query = Equipamento.query.join(Ambiente, Bloco, Departamento, Centro, Campus)

    # Query de equipamentos em uso

    equip_em_uso_query = equip_query.filter(Equipamento.em_uso==True)

    # Query de equipamentos em uso com manutenção agendada (fora de manutenção)

    equip_man_agendada_query = equip_em_uso_query.filter(Equipamento.em_manutencao==False)

    # Definição dos filtros que podem ser aplicados

    filtros = FiltrosOpcoes(equip_man_agendada_query, Equipamento.tipo_equipamento,
                            u'Tipo de Equipamento')
    filtros.extend(FiltrosOpcoes(equip_man_agendada_query, Ambiente.nome,
                                 u'Ambiente'))
    filtros.extend(FiltrosOpcoes(equip_man_agendada_query, Bloco.nome,
                                 u'Bloco'))
    filtros.extend(FiltrosOpcoes(equip_man_agendada_query, Departamento.nome,
                                 u'Departamento'))
    filtros.extend(FiltrosOpcoes(equip_man_agendada_query, Centro.nome,
                                 u'Centro'))
    filtros.extend(FiltrosOpcoes(equip_man_agendada_query, Campus.nome,
                                 u'Campus'))
    filtros.extend(FiltrosDatas(Equipamento.proxima_manutencao, u'Próxima Manutenção'))

    # Criação dos grupos de filtros e dicionário de indexação dos filtros

    grupos_filtros, indice_filtros = agrupar_filtros(filtros)

    # Processamento dos grupos de filtros para exibição no template

    grupos_template = grupos_filtros_template(grupos_filtros)

    # Filtros selecionados (a partir da query string)

    filtros_ativos = filtros_selecionados(request, indice_filtros)

    # Aplicação dos filtros

    equip_filtrados_query = aplicar_filtros(equip_man_agendada_query, 
                                            filtros, filtros_ativos)

    # Paginação dos resultados (ordenados por data da próxima manutenção)

    page = request.args.get('page', 1, type=int)

    pagination = equip_filtrados_query.order_by(Equipamento.proxima_manutencao).paginate(
        page, per_page=10, error_out=False)

    # Lista de equipamentos após paginação

    equip_filtrados = pagination.items

    return render_template('principal/manutencoes_agendadas.html',
                           equip_man_agendada=equip_filtrados,
                           data_hoje=date.today(),
                           pagination=pagination,
                           filtros=filtros,
                           filter_groups=grupos_template,
                           active_filters=filtros_ativos,
                           url_inicial=url_for('principal.manutencoes_agendadas'))


# Página de Solicitações
@principal.route('/solicitacoes')
def solicitacoes():
    return render_template('principal/solicitacoes.html')


# Página de Consumo
@principal.route('/consumo')
def consumo():
    return render_template('principal/consumo.html')


# Página de Contato
@principal.route('/contato', methods=['GET', 'POST'])
def contato():
    form_email = FormEmailContato()

    # Caso o usuário tenha clicado no link "Reportar problema",
    # será redirecionado para a página de contato, e alguns campos
    # serão preenchidos automaticamente
    if request.args.get('tipo') == 'problema':
        form_email.enviar_para.data = 'dev'
        form_email.assunto.data = 'Problema Técnico'

    if form_email.validate_on_submit():
        # Baseado no campo "enviar_para", os destinatários da
        # mensagem são selecionados
        if form_email.enviar_para.data == 'adm':
            lista_adms = Usuario.listar_administradores()
            destinatarios = [usuario.email for usuario in lista_adms]
                
        elif form_email.enviar_para.data == 'dev':
            lista_devs = listar_desenvolvedores()
            destinatarios = [usuario.email for usuario in lista_devs]

        enviar_email(destinatarios,
                     form_email.assunto.data,
                     'principal/email/mensagem',
                     nome=form_email.nome.data,
                     email=form_email.email.data,
                     mensagem=form_email.mensagem.data)

        flash('Email enviado!', 'success')

        return redirect(url_for('principal.contato'))

    return render_template('principal/contato.html',
                           form_email=form_email)

