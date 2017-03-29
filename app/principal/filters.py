# coding: utf-8

################################################################################
## SICEM - UFC
################################################################################
## Filtros para Páginas de Listagem de Manutenções
################################################################################


import datetime
from collections import OrderedDict
from flask import flash
from flask_admin.contrib.sqla.filters import *
from flask_admin.model.base import FilterGroup


########## Funções Auxiliares ##########


# Gera as possíveis opções disponíveis para uma coluna a partir de uma query ao
# banco de dados
def gerar_opcoes(query, coluna):
    # Obtenção dos possíveis valores (set = conjunto sem repetições)
    valores = set([valor[0] for valor in query.values(coluna)])

    # Retorno de uma lista de tuples (valor, texto)
    return [(opcao, opcao) for opcao in valores]


# Gera lista de filtros para campos em são dadas opções dos valores
def FiltrosOpcoes(query, coluna, nome):
    # Geração das opções
    opcoes = gerar_opcoes(query, coluna)
    
    return [FilterEqual(column=coluna, name=nome, options=opcoes),
            FilterInList(column=coluna, name=nome, options=opcoes)]


# Gera lista de filtros para campos do tipo data
def FiltrosDatas(coluna, nome):
    return [DateEqualFilterMod(column=coluna, name=nome),
            DateGreaterFilterMod(column=coluna, name=nome),
            DateSmallerFilterMod(column=coluna, name=nome),
            DateBetweenFilterMod(column=coluna, name=nome)]


# Organização dos filtros
# Agrupamento de filtros de uma mesma coluna
# Indexação dos filtros
# [Adaptado do Flask-Admin]
def agrupar_filtros(filtros):
    # Dicionário em que as chaves são o nome da coluna e os valores
    # são uma estrutura tipo FilterGroup (identificada por uma label, 
    # que é o nome da coluna, e guarda uma lista de dicionários com
    # cada filtro pertencente a esta coluna, contendo atributos
    # específicos de cada filtro)
    grupos_filtros = OrderedDict()

    # Dicionário em que as chaves são o número identificador do filtro
    # (string) e os valores são tuples no formato:
    # (identificador do filtro, objeto filtro)
    indice_filtros = {}

    # Preenchimento dos dicionários
    for i, filtro in enumerate(filtros):
        key = filtro.name

        if key not in grupos_filtros:
            grupos_filtros[key] = FilterGroup(filtro.name)
        
        grupos_filtros[key].append({
            'index': i,
            'arg': str(i),
            'operation': filtro.operation(),
            'options': filtro.options or None,
            'type': filtro.data_type
        })

        indice_filtros[str(i)] = (i, filtro)

    return grupos_filtros, indice_filtros


# Conversão dos grupos de filtros para um formato de exibição no template
# [Adaptado do Flask-Admin]
def grupos_filtros_template(grupos_filtros):
    grupos_template = OrderedDict()

    for grupo in grupos_filtros.itervalues():
        label, filtros = grupo.non_lazy()
        grupos_template[label] = filtros

    return grupos_template


# Obtendo os filtros selecionados pelo usuário  e seus valores 
# a partir da query string gerada no request da página
# [Adaptado do Flask-Admin]
def filtros_selecionados(request, indice_filtros):
    # Lista de filtros selecionados e valores correnspondentes
    filtros = []

    for n in request.args:
        if not n.startswith('flt'):
            continue

        if '_' not in n:
            continue

        pos, key = n[3:].split('_', 1)

        if key in indice_filtros:
            idx, flt = indice_filtros[key]

            valor = request.args[n]

            if flt.validate(valor):
                filtros.append((pos, (idx, flt.name, valor)))
            else:
                flash('Valor inválido: %s' % valor, 'danger')

    # Ordenar filtros por número identificador
    return [v[1] for v in sorted(filtros, key=lambda n: n[0])]


# Aplicação dos filtros selecionados
# [Adaptado do Flask-Admin]
def aplicar_filtros(query, filtros, filtros_ativos):
    # Os filtros são sucessivamentes aplicados à query inicial
    for idx, nome_filtro, valor in filtros_ativos:
        filtro = filtros[idx]

        # Processamento do valor dado ao filtro
        valor_proc = filtro.clean(valor)

        # Aplicação do filtro à query
        query = filtro.apply(query, valor_proc)

    # Retorno da query após aplicação dos filtros
    return query


########## Filtros Modificados ##########


# Filtros para tipo data (Problema no formato)

class DateEqualFilterMod(DateEqualFilter):
    def clean(self, value):
        return datetime.datetime.strptime(value, '%d.%m.%Y').date()


class DateGreaterFilterMod(DateGreaterFilter):
    def clean(self, value):
        return datetime.datetime.strptime(value, '%d.%m.%Y').date()


class DateSmallerFilterMod(DateSmallerFilter):
    def clean(self, value):
        return datetime.datetime.strptime(value, '%d.%m.%Y').date()


class DateBetweenFilterMod(DateBetweenFilter):
    def clean(self, value):
        return [datetime.datetime.strptime(range, '%d.%m.%Y').date()
                for range in value.split(' e ')]

    def validate(self, value):
        try:
            value = [datetime.datetime.strptime(range, '%d.%m.%Y').date()
                     for range in value.split(' e ')]
            # if " to " is missing, fail validation
            # sqlalchemy's .between() will not work if end date is before start date
            if (len(value) == 2) and (value[0] <= value[1]):
                return True
            else:
                return False
        except ValueError:
            return False

