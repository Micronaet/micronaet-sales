# Copyright 2019  Micronaet SRL (<http://www.micronaet.it>).
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

import logging
from odoo import models, fields, api

_logger = logging.getLogger(__name__)


class SaleOrderBlockGroup(models.Model):
    """ Model name: SaleOrderBlockGroup
    """

    _name = 'sale.order.block.group'
    _description = 'Sale order block'
    _order = 'name'

    # Button events:
    @api.multi
    def print_only_this(self):
        """ Print sale order only with this block
        """
        order = self.order_id
        self.env.context = dict(self.env.context)
        self.env.context.update({
            'only_this_block': self.id,
        })
        return order.print_quotation()

    @api.multi
    def _function_get_total_block(self):
        """ Fields function for calculate
        """
        for block in self:
            total = 0.0
            for sol in block.order_id.order_line:
                if sol.block_id.id == block.id:
                    total += sol.price_subtotal
            if block.block_margin:
                total *= 100.0 + block.block_margin
                total /= 100.0
            block.real_total = total

    # Columns:
    name = fields.Integer(
        'Code', required=True)
    title = fields.Char(
        'Title', size=64, required=True)
    block_margin = fields.Float(
        'Extra recharge %', digits=(16, 3),
        help='Add extra recharge to calculate real total')

    pre_text = fields.Text('Pre text')
    post_text = fields.Text('Post text')

    total = fields.Float(
        'Forced total', digits=(16, 2),
        help='Total written in offer block')
    real_total = fields.Float(
        string='Real total', store=False,
        compute='_function_get_total_block',
        help='Total sum of sale line in this block')
    order_id = fields.Many2one(
        'sale.order', 'Order', ondelete='cascade')

    # Parameter for line:
    hide_block = fields.Boolean(
        'Hide block', help='Hide in report for simulation')
    not_confirmed = fields.Boolean(
        'Not confirmed', help='Removed from order')

    show_header = fields.Boolean(
        'Show header', default=True)
    show_detail = fields.Boolean(
        'Show details', default=True)
    show_code = fields.Boolean(
        'Show code', default=True,
        help='Show code in line details')
    show_price = fields.Boolean(
        'Show price', default=True,
        help='Show unit price and subtotal')
    # 'show_subtotal = fields.Boolean('Show Subtotal', default=True)
    show_total = fields.Boolean('Show total', default=True)


class SaleOrder(models.Model):
    """ Model name: SaleOrder
    """
    _inherit = 'sale.order'

    # -------------------------------------------------------------------------
    # Button events:
    # -------------------------------------------------------------------------
    @api.multi
    def dummy_action(self):
        """ Dummy button to refresh data
        """
        return True

    # Override function:
    @api.one
    @api.returns('self', lambda value: value.id)
    def copy(self, default=None):
        """ Duplicate also block information
        """
        # Pool used:
        block_pool = self.env['sale.order.block.group']
        sol_pool = self.env['sale.order.line']

        new_order = super(SaleOrder, self).copy(default)
        new_id = new_order.id
        old_id = self.id

        if not self.block_ids:
            return new_order

        blocks = block_pool.search([
            ('order_id', '=', old_id),
        ])
        convert_db = []

        # TODO When adding new parameter put here!
        # ---------------------------------------------------------------------
        # Duplicate block list:
        # ---------------------------------------------------------------------
        _logger.warning('Duplicate extra block in sale: %s' % len(blocks))
        for block in blocks:
            data = {
                'name': block.name,
                'title': block.title,

                'pre_text': block.pre_text,
                'post_text': block.post_text,

                'total': block.total,
                # 'real_total':
                'order_id': new_id,

                # Parameter for line:
                'show_header': block.show_header,
                'show_detail': block.show_detail,
                'show_code': block.show_code,
                'show_price': block.show_detail,
                # 'show_subtotal': fields.boolean('Show Subtotal'),
                'show_total': block.show_total,

                'hide_block': block.hide_block,
                'not_confirmed': False,
            }
            convert_db.append((block.id, block_pool.create(data).id))

        # ---------------------------------------------------------------------
        # Change reference for block in detail list:
        # ---------------------------------------------------------------------
        _logger.warning('Update reference in details: %s' % len(convert_db))
        for old, new in convert_db:
            lines = sol_pool.search([
                ('order_id', '=', new_id),
                ('block_id', '=', old),
            ])
            if not lines:
                continue
            lines.write({
                'block_id': new,
            })
        return new_order

    @api.multi
    def print_quotation(self):
        """ This function prints the sales order and mark it as sent
            so that we can see more easily the next step of the workflow
        """
        self.ensure_one()

        self.printed = self.printed + 1
        datas = {
            'model': 'sale.order',
            'ids': [item.id for item in self],
            # TODO 'form': self.read(cr, uid, ids[0], context=context),
        }
        only_this_block = self.env.context.get('only_this_block')
        if only_this_block:
            datas['only_this_block'] = only_this_block

        # self.env.context = dict(self.env.context)
        # self.env.context['nicola'] = True
        return self.env.ref(
            'sale_order_block.report_sale_block_lang').report_action(
                self, data=datas)
        return {
            'type': 'ir.actions.report',
            'report_name': 'sale_order_block.report_sale_block_lang',
            'model': 'sale.order',
            'report_type': 'qweb-pdf',
            'datas': datas,
        }

    # Fields function:
    @api.multi
    def _function_get_total_block(self):
        """ Fields function for calculate
        """
        for order in self:
            total = 0.0
            for block in order.block_ids:
                total += block.total or block.real_total  # price_subtotal
            order.real_total = total

    # Columns:
    client_order_ref = fields.Char(
        string='Client order ref')
    printed = fields.Integer(
        string='Printed', default=1, help='Printed version')
    show_master_total = fields.Boolean(
        'Show master total', default=True)
    block_ids = fields.One2many(
        'sale.order.block.group', 'order_id', 'Block')

    real_total = fields.Float(
        'Real total', store=False,
        compute='_function_get_total_block',
        help='Total sum of sale line in this block')


class SaleOrderLine(models.Model):
    """ Model name: Sale Order Lie
    """
    _inherit = 'sale.order.line'
    _order = 'block_id, sequence, id'

    # Columns:
    block_id = fields.Many2one(
        'sale.order.block.group', 'Block', ondelete='set null', required=True)

    # Parameter for line:
    hide_block = fields.Boolean(
        'Hide block',
        related='block_id.hide_block',
        help='Hide in report for simulation')
    not_confirmed = fields.Boolean(
        'Not confirmed',
        related='block_id.not_confirmed',
        help='Removed from order')


class SaleOrderBlockGroupRelation(models.Model):
    """ Model name: Sale Order Block Group
    """

    _inherit = 'sale.order.block.group'

    # Columns:
    line_ids = fields.One2many(
        'sale.order.line', 'block_id', 'Sale order line')
