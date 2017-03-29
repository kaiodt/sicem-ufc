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

from ..util import tools


########## Formatos de Tipos de Dados ##########


# Tipo Data
def formato_data(view, value):
    return value.strftime('%d.%m.%Y')


# Tipo Mapa
def formato_mapa(view, value):
    # Alterar dimensões do mapa na view de detalhes
    if 'details' in request.path:
        width = 400
        height = 400
        zoom = 17
    else:
        width = 100
        height = 70
        zoom = 15

    params = html_params(**{
        "data-role": "leaflet",
        "data-width": width,
        "data-height": height,
        "data-geometry-type": to_shape(value).geom_type,
        "data-zoom": zoom
    })

    # Desabilitar edição na view de listar
    if 'details' not in request.path:
        params += u' disabled'

    if value.srid is -1:
        value.srid = 4326

    geojson = view.session.query(view.model).with_entities(func.ST_AsGeoJSON(value)).scalar()

    return Markup('<textarea %s>%s</textarea>' % (params, geojson))


########## Formatos de Campos Específicos ##########


# Campos Tipo Relação
def formato_relacao(view, context, model, name):
    html_string = ""

    # Extrair o tipo de relação a partir do nome do campo (plural) para
    # usar nas urls dos links (singular)
    if name[-1] == 's':             # Caso '***s' -> '***'
        tipo = name[:-1]
    elif name[-1] == 'i':           # Caso 'Campi' -> 'Campus'
        tipo = name[:-1] + 'us'

    # Gerar lista de botões com links para cada item da relação
    for item in model.__getattribute__(name).all():
        html_string += \
            '<a class="campo_relacao" href="{url}">\
                <span class="label label-default">{nome}</span>\
             </a>'.format(url=url_for(tipo + '.details_view', id=item.id),
                          nome=item.nome)

    return Markup(html_string)


# Campos Tipo Ambientes
def formato_relacao_ambientes(view, context, model, name):
    html_string = ""

    # Gerar lista de botões com links para cada ambiente
    for ambiente in model.__getattribute__(name).all():
        tipo = ambiente.tipo.lower().replace(' ', '')
        tipo = tools.retirar_acentos(tipo, 'minusculo')

        html_string += \
            '<a class="campo_relacao" href="{url}">\
                <span class="label label-default">{nome}</span>\
             </a>'.format(url=url_for(tipo + '.details_view', id=ambiente.id),
                          nome=ambiente.nome)

    return Markup(html_string)


# Campos Tipo Equipamentos
def formato_relacao_equipamentos(view, context, model, name):
    html_string = ""

    # Gerar lista de botões com links para cada equipamento
    for equip in model.__getattribute__(name).all():
        tipo = equip.tipo_equipamento.lower().replace(' ', '').replace('de', '')
        tipo = tools.retirar_acentos(tipo, 'minusculo')

        html_string += \
            '<a class="campo_relacao" href="{url}">\
                <span class="label label-default">{tipo} [{tomb}]</span>\
             </a>'.format(url=url_for(tipo + '.details_view', id=equip.id),
                          tipo=equip.tipo_equipamento, tomb=equip.tombamento)

    return Markup(html_string)


# Campos Tipo Manutenções
def formato_relacao_manutencoes(view, context, model, name):
    html_string = ""

    # Gerar lista de botões com links para cada manutenção
    for manutencao in model.__getattribute__(name).all():
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


########## Registro dos Formatos de Tipos de Dados ##########


FORMATOS_PADRAO = dict(typefmt.DEFAULT_FORMATTERS)
FORMATOS_PADRAO[date] = formato_data
FORMATOS_PADRAO[WKBElement] = formato_mapa

