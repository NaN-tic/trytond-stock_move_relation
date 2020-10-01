# This file is part stock_move_relation module for Tryton.
# The COPYRIGHT file at the top level of this repository contains
# the full copyright notices and license terms.
import unittest


from trytond.tests.test_tryton import ModuleTestCase
from trytond.tests.test_tryton import suite as test_suite


class StockMoveRelationTestCase(ModuleTestCase):
    'Test Stock Move Relation module'
    module = 'stock_move_relation'


def suite():
    suite = test_suite()
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(
            StockMoveRelationTestCase))
    return suite
