
# This file is part of Tryton.  The COPYRIGHT file at the top level of
# this repository contains the full copyright notices and license terms.

from decimal import Decimal

from trytond.modules.company.tests import CompanyTestMixin
from trytond.modules.company.tests import create_company, set_company
from trytond.pool import Pool
from trytond.tests.test_tryton import ModuleTestCase, with_transaction


class StockMoveRelationTestCase(CompanyTestMixin, ModuleTestCase):
    'Test StockMoveRelation module'
    module = 'stock_move_relation'
    extras = ['production', 'sale_delivery_date', 'stock_lot', 'stock_valued']

    @with_transaction()
    def test_search_from_warehouse(self):
        'Test searcher for from_warehouse_'
        pool = Pool()
        Uom = pool.get('product.uom')
        Template = pool.get('product.template')
        Product = pool.get('product.product')
        Location = pool.get('stock.location')
        Move = pool.get('stock.move')

        kg, = Uom.search([('name', '=', 'Kilogram')])
        template, = Template.create([{
                    'name': 'Test Stock Move Relation Warehouse Search',
                    'type': 'goods',
                    'default_uom': kg.id,
                    }])
        product, = Product.create([{
                    'template': template.id,
                    }])
        supplier, = Location.search([('code', '=', 'SUP')])
        storage, = Location.search([('code', '=', 'STO')])
        company = create_company()

        with set_company(company):
            move, = Move.create([{
                        'product': product.id,
                        'unit': kg.id,
                        'quantity': 1,
                        'from_location': storage.id,
                        'to_location': supplier.id,
                        'company': company.id,
                        'unit_price': Decimal('1'),
                        'currency': company.currency.id,
                        }])
            self.assertIn(move, Move.search([
                        ('from_warehouse_.code', '=', 'WH'),
                        ]))


del ModuleTestCase
