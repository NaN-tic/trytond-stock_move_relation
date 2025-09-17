# The COPYRIGHT file at the top level of this repository contains the full
# copyright notices and license terms.
from sql.functions import Substring, Position
from sql.conditionals import Coalesce
from sql import Cast, Literal

from trytond.model import fields
from trytond.pool import Pool, PoolMeta
from trytond.pyson import Eval

__all__ = ['Move']


class Move(metaclass=PoolMeta):
    __name__ = 'stock.move'
    document_origin = fields.Function(fields.Reference('Document Origin',
                        selection='get_document_origin'), 'get_relation')
    document = fields.Function(fields.Reference('Document',
                    selection='get_document'), 'get_relation')
    document_origin_date = fields.Function(fields.Date(
        'Document Origin Date'), 'get_relation',)
    document_origin_planned_date = fields.Function(fields.Date(
        'Document Origin Planned Date'), 'get_relation',
        searcher='search_document_origin_planned_date')
    from_warehouse = fields.Function(fields.Many2One('stock.location',
        'From Warehouse', domain=[('type', '=', 'warehouse')]),
        'get_relation', searcher='search_from_warehouse')
    to_warehouse = fields.Function(fields.Many2One('stock.location',
        'To Warehouse', domain=[('type', '=', 'warehouse')]),
        'get_relation', searcher='search_to_warehouse')
    document_origin_party = fields.Function(
        fields.Many2One('party.party', 'Party', context={
            'company': Eval('company', -1),
            },
        depends=['company']), 'get_relation',
        searcher='search_document_origin_party')

    @classmethod
    def _get_document_origin(cls):
        'Return list of Model names for origin Reference'
        return [
            'purchase.purchase',
            'sale.sale',
            ]
    @classmethod
    def get_document_origin(cls):
        Model = Pool().get('ir.model')
        models = cls._get_document_origin()
        models = Model.search([
            ('name', 'in', models),
            ])
        return [(None, '')] + [(m.name, m.string) for m in models]

    @classmethod
    def _get_document(cls):
        'Return list of Model names for origin Reference'
        return [
            'stock.shipment.in',
            'stock.shipment.out',
            'stock.shipment.out.return',
            'stock.shipment.in.return',
            'stock.shipment.internal',
            'production',
            ]

    @classmethod
    def get_document(cls):
        Model = Pool().get('ir.model')
        models = cls._get_document()
        models = Model.search([
            ('name', 'in', models),
            ])
        return [(None, '')] + [(m.name, m.string) for m in models]

    @classmethod
    def get_relation(cls, moves, names):
        Sale = Pool().get('sale.sale')

        res = {n: {m.id: None for m in moves} for n in names}
        for move in moves:
            document_origin = None
            if move.origin and not isinstance(move.origin, str):
                if (move.origin.__name__ == 'sale.line'
                        and move.origin.sale):
                    document_origin = move.origin.sale
                if (move.origin.__name__ == 'purchase.line'
                        and move.origin.purchase):
                    document_origin = move.origin.purchase
                if (getattr(move, 'production_input', None)
                        and move.production_input.origin
                        and isinstance(move.production_input.origin, Sale)):
                    document_origin = move.production_input.origin.sale
                if (getattr(move, 'production_output', None)
                        and move.production_output.origin
                        and isinstance(move.production_output.origin, Sale)):
                    document_origin = move.production_output.origin.sale

            if 'document_origin' in names and document_origin:
                res['document_origin'][move.id] = str(document_origin)

            if 'document' in names:
                if move.shipment:
                    res['document'][move.id] = str(move.shipment)
                if getattr(move, 'production_input', None):
                    res['document'][move.id] = str(move.production_input)
                if getattr(move, 'production_output', None):
                    res['document'][move.id] = str(move.production_output)

            if ('document_origin_date' in names and document_origin
                    and not isinstance(document_origin, str)):
                res['document_origin_date'][move.id] = (
                    document_origin.sale_date
                    if document_origin.__name__ == 'sale.sale'
                    else document_origin.purchase_date)

            if ('document_origin_planned_date' in names and move.origin
                    and not isinstance(move.origin, str)):
                if move.origin.__name__ == 'sale.line':
                    delivery_date = getattr(move.origin,
                        'manual_delivery_date', None)
                    if not delivery_date:
                        delivery_date = getattr(move.origin,
                            'shipping_date', None)
                    res['document_origin_planned_date'][move.id] = delivery_date
                elif move.origin.__name__ == 'purchase.line':
                    planned_date = None
                    if move.origin.delivery_date_store:
                        planned_date = move.origin.delivery_date_store
                    elif (move.origin.purchase
                            and move.origin.purchase.delivery_date):
                        planned_date = move.origin.purchase.delivery_date
                    else:
                        planned_date = move.planned_date
                    res['document_origin_planned_date'][move.id] = planned_date

            if 'from_warehouse' in names and move.from_location.warehouse:
                res['from_warehouse'][move.id] = move.from_location.warehouse.id
            if 'to_warehouse' in names and move.to_location.warehouse:
                res['to_warehouse'][move.id] = move.to_location.warehouse.id
            if ('document_origin_party' in names
                    and document_origin
                    and document_origin.party):
                res['document_origin_party'][move.id] = document_origin.party.id
        return res

    @classmethod
    def search_to_warehouse(cls, name, clause):
        return [('to_location.warehouse',) + tuple(clause[1:])]
    @classmethod
    def search_from_warehouse(cls, name, clause):
        return [('from_location.warehouse',) + tuple(clause[1:])]

    @classmethod
    def search_document_origin_party(cls, name, clause):

        return ['OR',
            ('shipment.customer' + clause[0].lstrip(name),)
                + tuple(clause[1:3]) + ('stock.shipment.out.return',)
                + tuple(clause[3:]),
            ('shipment.customer' + clause[0].lstrip(name),)
                + tuple(clause[1:3]) + ('stock.shipment.out',)
                + tuple(clause[3:]),
            ('sale.party',) + tuple(clause[1:]),
            ('shipment.supplier' + clause[0].lstrip(name),)
                + tuple(clause[1:3]) + ('stock.shipment.in.return',)
                + tuple(clause[3:]),
            ('shipment.supplier' + clause[0].lstrip(name),)
                + tuple(clause[1:3]) + ('stock.shipment.in',)
                + tuple(clause[3:]),
            ('purchase.party',) + tuple(clause[1:]),
            ]

    @classmethod
    def search_document_origin_planned_date(cls, name, clause):
        Line = Pool().get('sale.line')

        domain = ['OR',
                    [('origin', '!=', None),
                        ('planned_date',) + tuple(clause[1:])],
                    ('purchase.delivery_date',) + tuple(clause[1:]),
                    ('origin.delivery_date_store',) + tuple(clause[1:3])
                        + ('purchase.line',) + tuple(clause[3:])
                ]

        if hasattr(Line, 'manual_delivery_date'):
            domain.append(('origin.manual_delivery_date',) + tuple(clause[1:3])
                    + ('sale.line',) + tuple(clause[3:]),)
        return domain

    @classmethod
    def _document_origin_planned_date_query(cls):
        pool = Pool()
        Move = pool.get('stock.move')
        PurchaseLine = pool.get('purchase.line')
        Purchase = pool.get('purchase.purchase')
        SaleLine = pool.get('sale.line')
        Sale = pool.get('sale.sale')

        move = Move.__table__()
        purchase_line = PurchaseLine.__table__()
        purchase = Purchase.__table__()
        sale_line = SaleLine.__table__()
        sale = Sale.__table__()

        return move.join(purchase_line, 'LEFT', condition=(
            (Cast(Substring(move.origin,
                Position(',', move.origin) + Literal(1)),
                cls.id.sql_type().base) == purchase_line.id)
                & move.origin.ilike('purchase.line,%'))).join(
                purchase, 'LEFT', condition=(
                    purchase_line.purchase == purchase.id)
            ).join(sale_line, 'LEFT', condition=(
                (Cast(Substring(
                    move.origin, Position(',', move.origin) + Literal(1)),
                cls.id.sql_type().base) == sale_line.id)
                & move.origin.ilike('sale.line,%'))).join(
                    sale, 'LEFT', condition=(sale_line.sale == sale.id)
                ).select(move.id.as_('move'),
                    purchase_line.delivery_date_store.as_(
                        'delivery_date_store'),
                    purchase.delivery_date.as_('delivery_date'),
                    sale.shipping_date.as_('shipping_date'),
                    move.planned_date.as_('planned_date'),
                    where=(move.origin != None))

    @classmethod
    def order_document_origin_planned_date(cls, tables):
        table, _ = tables[None]

        key = 'document_origin_planned_date'
        if key not in tables:
            query = cls._document_origin_planned_date_query()
            join = table.join(
                query, type_='LEFT',
                condition=(query.move == table.id)
            )
            tables[key] = {
                None: (join.right, join.condition),
                }
        else:
            query, _ = tables[key][None]

        return [Coalesce(query.delivery_date_store, query.delivery_date,
            query.shipping_date, query.planned_date)]
