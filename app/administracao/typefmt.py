# coding: utf-8

################################################################################
## SICEM - UFC
################################################################################
## Formatos de Alguns Campos das Views do Painel de Administração
################################################################################


from flask import request, url_for
from datetime import date
from jinja2 import Markup
from flask_admin.contrib.geoa import typefmt
from wtforms.widgets import html_params
from geoalchemy2.shape import to_shape
from geoalchemy2.elements import WKBElement
from sqlalchemy import func


########## Formatos de Tipos de Dados ##########

# Alteração da forma como alguns tipos de dados são exibidos nas views
# de listagem e de detalhes

# Tipo float
def formato_float(view, value):
    # Exibir duas casas decimais e mostrar separadores de milhares
    float_str = '{:,.2f}'.format(value)

    # Substituir '.' por ',' e ',' por '.' e retornar o valor formatado
    # Note que isso deve ser feito simultaneamente, por isso o uso 
    # de uma variável temporária.
    return float_str.replace(',', '%temp%').replace('.', ',').replace('%temp%', '.')
    

# Tipo Data
def formato_data(view, value):
    # Exibição no formato dd.mm.aaa
    return value.strftime('%d.%m.%Y')


# Tipo Mapa
def formato_mapa(view, value):
    # Mostrar mapa maior na view de detalhes
    if 'details' in request.path:
        width = 400
        height = 400
        zoom = 17
    # Mostrar mapa menor na view de listagem
    else:
        width = 100
        height = 70
        zoom = 15

    # Passando parâmetros para renderização do widget do mapa
    params = html_params(**{
        "data-role": "leaflet",
        "data-width": width,
        "data-height": height,
        "data-geometry-type": to_shape(value).geom_type,
        "data-zoom": zoom
    })

    # Desabilitar edição do mapa na view de listagem
    # Deixar zoom habilitado na view de detalhes
    if 'details' not in request.path:
        params += u' disabled'

    if value.srid is -1:
        value.srid = 4326

    geojson = view.session.query(view.model).with_entities(func.ST_AsGeoJSON(value)).scalar()

    return Markup('<textarea %s>%s</textarea>' % (params, geojson))


########## Formatos de Campos Específicos ##########

# Alteração da forma como alguns campos específicos dos modelos são 
# exibidos nas views de listagem e de detalhes

# Campos Tipo Relação Geral (Relações one-to-many)
def formato_relacao(view, context, model, name):
    html_string = ""

    # Extrair o tipo de relação a partir do nome do campo (que estará no plural)
    # para usar nas urls dos links de redirecionamento (que deve ser no singular)

    if name[-1] == 's':             # Caso '***s' -> '***'
        tipo = name[:-1]
    elif name[-1] == 'i':           # Caso 'Campi' -> 'Campus'
        tipo = name[:-1] + 'us'

    # Gerar lista de botões com links de redirecionamento para cada item da relação

    for item in model.__getattribute__(name).order_by('nome').all():
        html_string += \
            '<a class="campo_relacao" href="{url}">\
                <span class="label label-default">{nome}</span>\
             </a>'.format(url=url_for(tipo + '.details_view', id=item.id),
                          nome=item.nome)

    return Markup(html_string)


# Campo Tipo Relação de Ambientes
def formato_relacao_ambientes(view, context, model, name):
    html_string = ""

    # Gerar lista de botões com links de redirecionamento para cada ambiente

    for ambiente in model.__getattribute__(name).order_by('nome').all():
        # Obter o endpoint do tipo do ambiente para gerar o link de redirecionamento
        endpoint = ambiente.endpoint

        html_string += \
            '<a class="campo_relacao" href="{url}">\
                <span class="label label-default">{nome}</span>\
             </a>'.format(url=url_for(endpoint + '.details_view', id=ambiente.id),
                          nome=ambiente.nome)

    return Markup(html_string)


# Campo Tipo Relação de Equipamentos
def formato_relacao_equipamentos(view, context, model, name):
    html_string = ""

    # Gerar lista de botões com links de redirecionamento para cada equipamento
    
    for equip in model.__getattribute__(name).order_by('tipo_equipamento').all():
        # Obter o endpoint do tipo do equipamento para gerar o link de redirecionamento
        endpoint = equip.endpoint

        html_string += \
            '<a class="campo_relacao" href="{url}">\
                <span class="label label-default">{tipo} [{tomb}]</span>\
             </a>'.format(url=url_for(endpoint + '.details_view', id=equip.id),
                          tipo=equip.tipo_equipamento, tomb=equip.tombamento)

    return Markup(html_string)


# Campo Tipo Relação de Manutenções
def formato_relacao_manutencoes(view, context, model, name):
    html_string = ""

    # Gerar lista de botões com links de redirecionamento para cada manutenção
    for manutencao in model.__getattribute__(name).order_by('data_abertura').all():
        # Mostrar a data de conclusão (caso haja) ou a de abertura
        if manutencao.data_conclusao:
            data = manutencao.data_conclusao
        else:
            data = manutencao.data_abertura

        html_string += \
            '<a class="campo_relacao" href="{url}">\
                <span class="label label-default">{num_os} [{data}]</span>\
             </a>'.format(url=url_for('manutencao.details_view', id=manutencao.id),
                          num_os=manutencao.num_ordem_servico,
                          data=data.strftime("%d.%m.%Y"))

    return Markup(html_string)


# Campo Tipo Relação de Usuários Responsáveis por uma Unidade Responsável
def formato_relacao_responsaveis(view, context, model, name):
    html_string = ""

    # Gerar lista de botões com links de redirecionamento para cada responsável
    for responsavel in model.__getattribute__(name).order_by('nome').all():
        html_string += \
            '<a class="campo_relacao" href="{url}">\
                <span class="label label-default">{nome} [{email}]</span>\
             </a>'.format(url=url_for('usuario.details_view', id=responsavel.id),
                          nome=responsavel.nome,
                          email=responsavel.email)

    return Markup(html_string)


# Campo Tipo Relação de Unidades Consumidoras
def formato_relacao_unidades_consumidoras(view, context, model, name):
    html_string = ""

    # Gerar lista de botões com links de redirecionamento para cada unidade consumidora
    for unidade in model.__getattribute__(name).order_by('nome').all():
        html_string += \
            '<a class="campo_relacao" href="{url}">\
                <span class="label label-default">{nome}</span>\
             </a>'.format(url=url_for('unidadeconsumidora.details_view', 
                          id=unidade.id),
                          nome=unidade.nome)

    return Markup(html_string)


# Campo Tipo Relação de Contas de Luz
def formato_relacao_contas(view, context, model, name):
    html_string = ""

    # Gerar lista de botões com links de redirecionamento para cada conta de luz
    for conta in model.__getattribute__(name).order_by('data_leitura').all():
        html_string += \
            '<a class="campo_relacao" href="{url}">\
                <span class="label label-default">{data}</span>\
             </a>'.format(url=url_for('conta.details_view', id=conta.id),
                          data=conta.data_leitura.strftime("%d.%m.%Y"))

    return Markup(html_string)




########## Registro dos Formatos de Tipos de Dados ##########

# Alteração do dicionário que define os formatos dos tipos de dados padrão
# para que sejam substituídos pelos formatos modificados

FORMATOS_PADRAO = dict(typefmt.DEFAULT_FORMATTERS)
FORMATOS_PADRAO[float] = formato_float
FORMATOS_PADRAO[date] = formato_data
FORMATOS_PADRAO[WKBElement] = formato_mapa


