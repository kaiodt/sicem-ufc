# coding: utf-8

################################################################################
## SICEM - UFC
################################################################################
## Views do Blueprint Principal
################################################################################

from datetime import date
from flask import render_template, redirect, url_for, request, current_app
from flask_login import login_required
from shapely import wkb
from sqlalchemy import extract

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
    # Pegando do banco de dados todos os elementos que serão inseridos no mapa,
    # ou seja, todos elementos com 'localizacao' definida
    unidades_consumidoras = UnidadeConsumidora.query.filter(UnidadeConsumidora.localizacao != None).all()
    blocos = Bloco.query.filter(Bloco.localizacao != None).all()
    subestacoes_abrigadas = SubestacaoAbrigada.query.filter(SubestacaoAbrigada.localizacao != None).all()
    subestacoes_aereas = SubestacaoAerea.query.filter(SubestacaoAerea.localizacao != None).all()
    centros = Centro.query.filter(Centro.mapeamento != None).all()
    campi = Campus.query.filter(Campus.mapeamento != None).all()
    
    # Listas que conterão dicionários com o par objeto e localização (convertida para números de lat. e long. 
    # que podem ser processados pela extensão Leaflet)
    lista_blocos = []
    lista_subestacoes_abrigadas = []
    lista_subestacoes_aereas = []    
    lista_centros = []
    lista_campi = []
    lista_unidades_consumidoras = []

    # Função para converter a localização salva em WKB para uma lista [latitude, longitude]
    def wkb_to_latLong(localizacao):
        temp = wkb.loads(bytes(localizacao.data))
        return [temp.y, temp.x]


    # Processos iterativos que geram essas listas de dicionários
    for unidade_consumidora in unidades_consumidoras:
        lista_unidades_consumidoras.append({
             "nome":               unidade_consumidora.nome
            ,"localizacao":        wkb_to_latLong(unidade_consumidora.localizacao)
            ,"unidadeResponsavel": unidade_consumidora.unidade_responsavel.nome
            ,"mod_tarifaria":      unidade_consumidora.mod_tarifaria
            ,"linkConsumo":        url_for('principal.consumo', id=unidade_consumidora.id)
            })

    for bloco in blocos:
        lista_blocos.append({
             "nome":             bloco.nome
            ,"localizacao":      wkb_to_latLong(bloco.localizacao)
            ,"departamento":     bloco.departamento.nome
            ,"centro":           bloco.departamento.centro.nome
            ,"campus":           bloco.departamento.centro.campus.nome
            ,"linkEquipamentos": url_for('principal.equipamentos_bloco', id=bloco.id)
            })

    for subestacao_abrigada in subestacoes_abrigadas:
        lista_subestacoes_abrigadas.append({
             "nome":        subestacao_abrigada.nome
            ,"localizacao": wkb_to_latLong(subestacao_abrigada.localizacao)
            })

    for subestacao_aerea in subestacoes_aereas:
        lista_subestacoes_aereas.append({
             "nome":        subestacao_aerea.nome
            ,"localizacao": wkb_to_latLong(subestacao_aerea.localizacao)
            })

    # Como Centros e Campus possuem um mapeamento de multi-polígonos o processo iterativo é mais complexo
    for centro in centros:
        centroMapData = wkb.loads(bytes(centro.mapeamento.data)) # convertendo de um WKBElement para formato da biblioteca shapely
        mapeamento = []
        for area in list(centroMapData): # list(centroMapData) retorna uma lista com os vários polygonos (ou áreas) do centro
                                         # formato de um polígono: lista de tuples contendo dois elementos cada (latitude 
                                         # e longitude). Ex: Um triângulo é [(0, 0),(0, 1),(1, 0)]
            # trocar (x,y) => (y,x)
            coordenadas_temp = []
            for ponto in list(area.exterior.coords):
                coordenadas_temp.append([ponto[1], ponto[0]])
            mapeamento.append(coordenadas_temp)    # mapeamento é uma lista de áreas
            
            lista_departamentos = [departamento.nome for departamento in centro.departamentos.all()]
            lista_centros.append({
                 "nome":                centro.nome
                ,"mapeamento":          mapeamento
                ,"campus":              centro.campus.nome
                ,"lista_departamentos": lista_departamentos
                })

    for campus in campi:
        map_temp = wkb.loads(bytes(campus.mapeamento.data))
        mapeamento = []
        for area in list(map_temp):
            coordenadas_temp = []
            for ponto in list(area.exterior.coords):
                coordenadas_temp.append([ponto[1], ponto[0]])
            mapeamento.append(coordenadas_temp)
            lista_campi.append({
                 "nome":        campus.nome
                ,"mapeamento":  mapeamento
                ,"instituicao": campus.instituicao.nome
            })


    return render_template('principal/mapa.html', 
                            lista_blocos = lista_blocos,
                            lista_subestacoes_abrigadas = lista_subestacoes_abrigadas,
                            lista_subestacoes_aereas = lista_subestacoes_aereas,
                            lista_centros = lista_centros,
                            lista_campi = lista_campi,
                            lista_unidades_consumidoras = lista_unidades_consumidoras)


# Página de Equipamentos de um Bloco (Restrita a usuários cadastrados)
@principal.route('/equipamentos/bloco')
@login_required
def equipamentos_bloco():
    id_bloco = request.args.get('id')
    bloco = Bloco.query.get(id_bloco)
   
    ambientes = bloco.ambientes
    local_equipamentos = []

    # Adicionando os equipamentos de cada ambiente à lista local_equipamentos
    for ambiente in ambientes:
        local_equipamentos.extend(ambiente.equipamentos)

    dict_local_equipamentos = {}    # dicionário cujas keys são os tipos do equipamentos e os valores 
                                    # são as listas de equipamentos de cada tipo

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


# Página de Equipamentos (Restrita a usuários cadastrados)
@principal.route('/equipamentos')
@login_required
def equipamentos():
    # São listados todos os equipamentos em uso cadastrados no banco de dados.
    # Também é possível filtrar os resultados de acordo com os valores de determinadas
    # colunas.

    # Query de equipamentos (adicionando joins de outras tabelas)
    equip_query = Equipamento.query.join(Ambiente, Bloco, Departamento, Centro, Campus)

    # Query de equipamentos em uso
    equip_em_uso_query = equip_query.filter(Equipamento.em_uso==True)

    # Definição dos filtros que podem ser aplicados (lista de filtros)
    # Deve-se indicar a query de base, a coluna e o nome de exibição do filtro
    # Note também que alguns tipos de dados possuem mais de um filtro ('filters.py')

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

    # Filtros selecionados (a partir da query string do request da página)
    filtros_ativos = filtros_selecionados(request, indice_filtros)

    # Aplicação dos filtros selecionados
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


# Página de Controle de Manutenções (Restrita a usuários cadastrados)
# Aba Manutenções Abertas
@principal.route('/manutencoes-abertas')
@login_required
def manutencoes_abertas():
    # São listadas todas as manutenções abertas cadastradas no banco de dados.
    # Também é possível filtrar os resultados de acordo com os valores de determinadas
    # colunas.

    # Query de manutenções (adicionando joins de outras tabelas)
    manut_query = Manutencao.query.join(Equipamento, Ambiente, Bloco, Departamento,
                                        Centro, Campus)

    # Query de manutenções abertas
    manut_abertas_query = manut_query.filter(Manutencao.status=='Aberta')

    # Definição dos filtros que podem ser aplicados (lista de filtros)
    # Deve-se indicar a query de base, a coluna e o nome de exibição do filtro
    # Note também que alguns tipos de dados possuem mais de um filtro ('filters.py')

    filtros = FiltrosOpcoes(manut_abertas_query, Manutencao.tipo_manutencao,
                            u'Tipo de Manutenção')
    filtros.extend(FiltrosOpcoes(manut_abertas_query, Equipamento.tipo_equipamento,
                                 u'Tipo de Equipamento'))
    filtros.extend(FiltrosOpcoes(manut_abertas_query, Ambiente.nome,
                                 u'Ambiente'))
    filtros.extend(FiltrosOpcoes(manut_abertas_query, Bloco.nome,
                                 u'Bloco'))
    filtros.extend(FiltrosOpcoes(manut_abertas_query, Departamento.nome,
                                 u'Departamento'))
    filtros.extend(FiltrosOpcoes(manut_abertas_query, Centro.nome,
                                 u'Centro'))
    filtros.extend(FiltrosOpcoes(manut_abertas_query, Campus.nome,
                                 u'Campus'))
    filtros.extend(FiltrosDatas(Manutencao.data_abertura, u'Data de Abertura'))

    # Criação dos grupos de filtros e dicionário de indexação dos filtros
    grupos_filtros, indice_filtros = agrupar_filtros(filtros)

    # Processamento dos grupos de filtros para exibição no template
    grupos_template = grupos_filtros_template(grupos_filtros)

    # Filtros selecionados (a partir da query string do request da página)
    filtros_ativos = filtros_selecionados(request, indice_filtros)

    # Aplicação dos filtros selecionados
    manut_filtradas_query = aplicar_filtros(manut_abertas_query, 
                                            filtros, filtros_ativos)

    # Paginação dos resultados (ordenados por data de abertura)

    page = request.args.get('page', 1, type=int)

    pagination = manut_filtradas_query.order_by(Manutencao.data_abertura).paginate(
        page, per_page=10, error_out=False)

    # Lista de manutenções abertas após paginação
    manut_filtradas = pagination.items

    return render_template('principal/manutencoes_abertas.html',
                           man_abertas=manut_filtradas,
                           data_hoje=date.today(),
                           pagination=pagination,
                           filtros=filtros,
                           filter_groups=grupos_template,
                           active_filters=filtros_ativos,
                           url_inicial=url_for('principal.manutencoes_abertas'))


# Página de Controle de Manutenções (Restrita a usuários cadastrados)
# Aba Manutenções Agendadas
@principal.route('/manutencoes-agendadas')
@login_required
def manutencoes_agendadas():
    # São listadas todas as manutenções preventivas agendadas.
    # Também é possível filtrar os resultados de acordo com os valores de determinadas
    # colunas.

    # Query de equipamentos (adicionando joins de outras tabelas)
    equip_query = Equipamento.query.join(Ambiente, Bloco, Departamento, Centro, Campus)

    # Query de equipamentos em uso
    equip_em_uso_query = equip_query.filter(Equipamento.em_uso==True)

    # Query de equipamentos em uso com manutenção agendada (fora de manutenção)
    equip_man_agendada_query = equip_em_uso_query.filter(Equipamento.em_manutencao==False)

    # Definição dos filtros que podem ser aplicados (lista de filtros)
    # Deve-se indicar a query de base, a coluna e o nome de exibição do filtro
    # Note também que alguns tipos de dados possuem mais de um filtro ('filters.py')

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

    # Filtros selecionados (a partir da query string do request da página)
    filtros_ativos = filtros_selecionados(request, indice_filtros)

    # Aplicação dos filtros selecionados
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


# Página de Solicitações (Em Desenvolvimento)
@principal.route('/solicitacoes')
def solicitacoes():
    return render_template('principal/solicitacoes.html')


# Página de Consumo
@principal.route('/consumo')
def consumo():
    id_unidade_consumidora = request.args.get('id') # id da Unidade Consumidora caso exista query string
    unidade_consumidora_inicial = ''
    if id_unidade_consumidora is not None:
        unidade_consumidora_inicial = UnidadeConsumidora.query.filter_by(id = id_unidade_consumidora).first()

    unidades_responsaveis = UnidadeResponsavel.query.all()
    '''
    O dicionário abaixo conterá a relação de Unidades Responsáveis com Unidades Consumidoras da seguinte forma:
    cada nome de Unidade Responsável é uma key do dicionário cujo valor é uma lista com cada elemento sendo o nome de uma
    Unidade Consumidora relacionada
    '''
    dicionario = {}    
    dicionario["Todas"] = []
    for unidade_responsavel in unidades_responsaveis:
        # criando uma lista vazia para uma key com o nome da Unidade Responsável
        dicionario[unidade_responsavel.nome] = [] 
        # é feito então um query do db com todas as Unidades Consumidoras da Unidade responsável em questão
        unidades_consumidoras = unidade_responsavel.unidades_consumidoras.all()

        for unidade_consumidora in unidades_consumidoras:
            dicionario[unidade_responsavel.nome].append(unidade_consumidora.nome) # é adicionado ao final da lista o nome da nova Unidade Consumidora
            dicionario["Todas"].append(unidade_consumidora.nome)                  # esse nome é igualmente adicionado à lista contendo todas as Unidades Consumidoras

    # Organizando em ordem alfabética a lista com todas as unidades consumidoras
    dicionario["Todas"] = sorted(dicionario["Todas"])
    
    '''
    No código a seguir o será construído o dicionário 'contas_5anos' contendo todas as Contas de energia de todas as Unidades Consumidoras
    dos últimos 5 anos. Cada key de contas_5anos será o nome de uma Unidade Consumidora e seu valor será um novo dicionário cujas keys serão
    propriedades das Contas de energia (como data, consumo fora de ponta etc) com valores no formato de listas (visando a fácil integração
    com a biblioteca plotly.js do lado do cliente)
    '''
    unidades_consumidoras = UnidadeConsumidora.query.all()
    contas_5anos = {}

    for unidade_consumidora in unidades_consumidoras:
        contas_5anos[unidade_consumidora.nome] = {
             'data': []
            ,'consumoPonta': []
            ,'consumoForaPonta': []
            ,'valorPonta': []
            ,'valorForaPonta': []
        }
        # Query secreto para pegar as contas dos últimos 5 anos, organizados de acordo com a coluna 'data_leitura' da tabela do db
        contas = unidade_consumidora.hist_contas.filter(extract('year', Conta.data_leitura) > date.today().year-5).order_by(Conta.data_leitura).all()

        for conta in contas:
            contas_5anos[unidade_consumidora.nome]['data'].append("%d-%d" %(conta.data_leitura.year, conta.data_leitura.month)) # Formato para a biblioteca plotly.js
            contas_5anos[unidade_consumidora.nome]['consumoPonta'].append(conta.cons_hora_ponta)
            contas_5anos[unidade_consumidora.nome]['consumoForaPonta'].append(conta.cons_fora_ponta)
            contas_5anos[unidade_consumidora.nome]['valorPonta'].append(conta.valor_hora_ponta)
            contas_5anos[unidade_consumidora.nome]['valorForaPonta'].append(conta.valor_fora_ponta)
          
    return render_template('principal/consumo.html', dicionario=dicionario, contas_5anos=contas_5anos,
                                                     unidade_consumidora_inicial=unidade_consumidora_inicial)


# Página de Contato
@principal.route('/contato', methods=['GET', 'POST'])
def contato():
    # Formulário de envio de email de contato
    form_email = FormEmailContato()

    # Caso o usuário tenha clicado no link "Reportar problema",
    # será redirecionado para a página de contato, e alguns campos
    # serão preenchidos automaticamente
    if request.args.get('tipo') == 'problema':
        form_email.enviar_para.data = 'dev'
        form_email.assunto.data = 'Problema Técnico'

    # Após validação do formulário
    if form_email.validate_on_submit():
        # Baseado no campo "enviar_para", os destinatários da
        # mensagem são selecionados

        # Administradores
        if form_email.enviar_para.data == 'adm':
            # Obter lista de administradores cadastrados
            lista_adms = Usuario.listar_administradores()

            # Gerar lista de emails dos administradores
            destinatarios = [usuario.email for usuario in lista_adms]
                
        # Desenvolvedores
        elif form_email.enviar_para.data == 'dev':
            # Obter lista de desenvolvedores cadastrados
            lista_devs = listar_desenvolvedores()

            # Gerar lista de emails dos desenvolvedores
            destinatarios = [usuario.email for usuario in lista_devs]

        # Enviar email(s) para os destinatários
        enviar_email(destinatarios,
                     form_email.assunto.data,
                     'principal/email/mensagem',
                     nome=form_email.nome.data,
                     email=form_email.email.data,
                     mensagem=form_email.mensagem.data)

        flash('Email enviado!', 'success')

        # Redirecionar para página de contato
        return redirect(url_for('principal.contato'))

    return render_template('principal/contato.html',
                           form_email=form_email)

