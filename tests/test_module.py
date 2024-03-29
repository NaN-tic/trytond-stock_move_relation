
# This file is part of Tryton.  The COPYRIGHT file at the top level of
# this repository contains the full copyright notices and license terms.

from trytond.modules.company.tests import CompanyTestMixin
from trytond.tests.test_tryton import ModuleTestCase


class StockMoveRelationTestCase(CompanyTestMixin, ModuleTestCase):
    'Test StockMoveRelation module'
    module = 'stock_move_relation'
    extras = ['production', 'sale_delivery_date', 'stock_lot', 'stock_valued']


del ModuleTestCase
