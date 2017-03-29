# coding: utf-8

################################################################################
## SICEM - UFC
################################################################################
## Filtros da View de Listagem do Painel de Administração
################################################################################


import datetime
from flask_admin.contrib.sqla.filters import *


########## Funções Auxiliares ##########


# Gera série de filtros para campos do tipo string
def FiltrosStrings(coluna, nome):
    return [FilterLike(column=coluna, name=nome),
            FilterNotLike(column=coluna, name=nome),
            FilterEqual(column=coluna, name=nome),
            FilterNotEqual(column=coluna, name=nome),
            FilterInList(column=coluna, name=nome),
            FilterNotInListMod(column=coluna, name=nome),
            FilterEmpty(column=coluna, name=nome)]


# Gera série de filtros para campos do tipo inteiro
def FiltrosInteiros(coluna, nome):
    return [IntEqualFilter(column=coluna, name=nome),
            IntNotEqualFilter(column=coluna, name=nome),
            IntGreaterFilter(column=coluna, name=nome),
            IntSmallerFilter(column=coluna, name=nome),
            IntInListFilter(column=coluna, name=nome),
            IntNotInListFilterMod(column=coluna, name=nome),
            FilterEmpty(column=coluna, name=nome)]


# Gera série de filtros para campos do tipo float
def FiltrosFloats(coluna, nome):
    return [FloatEqualFilter(column=coluna, name=nome),
            FloatNotEqualFilter(column=coluna, name=nome),
            FloatGreaterFilter(column=coluna, name=nome),
            FloatSmallerFilter(column=coluna, name=nome),
            FloatInListFilter(column=coluna, name=nome),
            FloatNotInListFilterMod(column=coluna, name=nome),
            FilterEmpty(column=coluna, name=nome)]


# Gera série de filtros para campos do tipo data
def FiltrosDatas(coluna, nome):
    return [DateEqualFilterMod(column=coluna, name=nome),
            DateNotEqualFilterMod(column=coluna, name=nome),
            DateGreaterFilterMod(column=coluna, name=nome),
            DateSmallerFilterMod(column=coluna, name=nome),
            DateBetweenFilterMod(column=coluna, name=nome),
            DateNotBetweenFilterMod(column=coluna, name=nome),
            FilterEmpty(column=coluna, name=nome)]


########## Filtros Modificados ##########


# Filtros tipo fora da lista (Problema na tradução)

class FilterNotInListMod(FilterNotInList):
    def operation(self):
        return 'fora da lista'


class IntNotInListFilterMod(IntNotInListFilter):
    def operation(self):
        return 'fora da lista'


class FloatNotInListFilterMod(FloatNotInListFilter):
    def operation(self):
        return 'fora da lista'


# Filtros para tipo data (Problema no formato)

class DateEqualFilterMod(DateEqualFilter):
    def clean(self, value):
        return datetime.datetime.strptime(value, '%d.%m.%Y').date()


class DateNotEqualFilterMod(DateNotEqualFilter):
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


class DateNotBetweenFilterMod(DateNotBetweenFilter):
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

