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


# Gera as opções disponíveis para uma coluna a partir de uma busca no
# banco de dados
def gerar_opcoes(query, coluna):
    # Obtenção dos possíveis valores (set = conjunto sem repetições)
    valores = set([valor[0] for valor in query.values(coluna)])

    # Retorno de uma lista de tuples no formato (valor, texto)
    return [(opcao, opcao) for opcao in valores]


# Gera lista de filtros para campos em que são dadas opções para os valores
def FiltrosOpcoes(query, coluna, nome):
    # Geração das opções
    opcoes = gerar_opcoes(query, coluna)

    return [FilterEqual(column=coluna, name=nome, options=opcoes),      # Igual
            FilterInList(column=coluna, name=nome, options=opcoes)]     # Na lista


# Gera lista de filtros para campos do tipo data
def FiltrosDatas(coluna, nome):
    return [DateEqualFilterMod(column=coluna, name=nome),       # Igual
            DateGreaterFilterMod(column=coluna, name=nome),     # Depois de
            DateSmallerFilterMod(column=coluna, name=nome),     # Antes de
            DateBetweenFilterMod(column=coluna, name=nome)]     # Entre


# Organização dos filtros
# Agrupamento de filtros de uma mesma coluna
# Indexação dos filtros
# [Adaptado do Flask-Admin]
def agrupar_filtros(filtros):
    # Dicionário ordenado em que as chaves são o nome da coluna e os valores
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
        # Nome da coluna a qual o filtro é aplicado
        key = filtro.name

        # Caso a coluna ainda não esteja no dicionário "grupos_filtros"
        if key not in grupos_filtros:
            # Criar chave para a coluna e iniciar sua estrutura tipo FilterGroup
            grupos_filtros[key] = FilterGroup(filtro.name)
        
        # Adicionar o filtro na estrutura FilterGroup da coluna em questão
        grupos_filtros[key].append({
            'index': i,
            'arg': str(i),
            'operation': filtro.operation(),
            'options': filtro.options or None,
            'type': filtro.data_type
        })

        # Incluir filtro no dicionário de indexação de filtros
        indice_filtros[str(i)] = (i, filtro)

    return grupos_filtros, indice_filtros


# Conversão dos grupos de filtros para um formato de exibição no template
# [Adaptado do Flask-Admin]
def grupos_filtros_template(grupos_filtros):
    # Dicionário ordenado em que as chaves são os nomes das colunas e os valores
    # são listas de dicionários, um para cada filtro que pode ser aplicado na
    # coluna em questão, contendo as chaves 'operation' e 'options' referentes ao
    # filtro 
    grupos_template = OrderedDict()

    # Preenchimento do dicionário "grupos_template"
    for grupo in grupos_filtros.itervalues():
        # Obter uma coluna (identificada por 'label') e seus filtros (lista de dicionários)
        label, filtros = grupo.non_lazy()

        # Adicionar coluna ao dicionário
        grupos_template[label] = filtros

    return grupos_template


# Obtenção dos filtros selecionados pelo usuário  e seus valores
# a partir da query string gerada no request da página
# [Adaptado do Flask-Admin]
def filtros_selecionados(request, indice_filtros):
    # Lista de filtros selecionados e valores correspondentes
    filtros = []

    # Busca dos filtros nos argumentos da query string do request
    for n in request.args:
        # Os filtros são identificados por flt[pos]_[key], e essas
        # identificações são geradas pelo arquivo 'static/externo/filters.js'

        if not n.startswith('flt'):
            continue

        if '_' not in n:
            continue

        # Obtendo a identificação de um filtro
        pos, key = n[3:].split('_', 1)

        # Testar se o identificador do filtro é válido
        # (se existe no dicionário indexador de filtros)
        if key in indice_filtros:
            # Obter o objeto filtro e seu índice
            idx, flt = indice_filtros[key]

            # Obter o valor a ser usado no filtro
            valor = request.args[n]

            # Testar se o valor é válido para este filtro
            if flt.validate(valor):
                # Adicionar filtro na lista de filtros selecionados
                filtros.append((pos, (idx, flt.name, valor)))
            else:
                flash('Valor inválido: %s' % valor, 'danger')

    # Retornar lista de filtros selecionados ordenada por número identificador
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

# Os filtros utilizados são fornecidos pelo Flask-Admin, mas alguns
# precisam de pequenas correções, como segue:

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

