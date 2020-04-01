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
    _rec_name = 'code'
    _order = 'code'

    # Button events:
    @api.multi
    def print_only_this(self):
        """ Print sale order only with this block
        """
        sale_pool = self.env['sale.order']
        return sale_pool.with_context(only_block=[self.id]).print_quotation()

    @api.depends
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
    code = fields.Integer(
        'Code', required=True)
    name = fields.Char(
        'Name', size=64, required=True)
    block_margin = fields.Float(
        'Extra recharge %', digits=(16, 3),
        help='Add extra recharge to calculate real total')

    pre_text = fields.Text('Pre text')
    post_text = fields.Text('Post text')

    total = fields.Float(
        'Block total', digits=(16, 2),
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

    # Button events:
    @api.multi
    def dummy_action(self):
        """ Dummy button to refresh data
        """
        return True

    # Override function:
    # TODO
    '''
    @api.one
    @api.returns('self', lambda value: value.id)
    def copy(self, default=None):
        default = dict(default or {})
        default.update({
            'invoice_date': ''})
        return super(AccountInvoice, self).copy(default)
    
    @api.multi
    def copy(self, cr, uid, old_id, default=None, context=None):
        """ Create a new record in ClassName model from existing one
            @param cr: cursor to database
            @param uid: id of current user
            @param id: list of record ids on which copy method executes
            @param default: dict type contains the values to override copy op.
            @param context: context arguments

            @return: returns a id of newly created record
        """
        new_id = super(SaleOrder, self).copy(
            cr, uid, old_id, default=default, context=context)

        block_pool = self.pool.get('sale.order.block.group')
        block_ids = block_pool.search(cr, uid, [
            ('order_id', '=', old_id),
        ], context=context)
        convert_db = []

        # XXX When adding new parameter put here!
        # ---------------------------------------------------------------------
        # Duplicate block list:
        # ---------------------------------------------------------------------
        _logger.warning('Duplicate extra block in sale: %s' % len(block_ids))
        for block in block_pool.browse(cr, uid, block_ids, context=context):
            data = {
                'code': block.code,
                'name': block.name,

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
            }
            convert_db.append((
                block.id, block_pool.create(cr, uid, data, context=context)))

        # ---------------------------------------------------------------------
        # Change reference for block in detail list:
        # ---------------------------------------------------------------------
        sol_pool = self.pool.get('sale.order.line')
        _logger.warning('Update reference in details: %s' % len(convert_db))
        for old, new in convert_db:
            sol_ids = sol_pool.search(cr, uid, [
                ('order_id', '=', new_id),
                ('block_id', '=', old),
            ], context=context)
            if not sol_ids:
                continue
            sol_pool.write(cr, uid, sol_ids, {
                'block_id': new,
            }, context=context)
        return new_id
    '''
    # TODO
    '''
    @api.multi
    def print_quotation(self):
        """ This function prints the sales order and mark it as sent
            so that we can see more easily the next step of the workflow
        """
        self.ensureone()

        # Mark as sent: TODO use workflow?
        # wf_service = netsvc.LocalService("workflow")
        # wf_service.trg_validate(
        #    uid, 'sale.order', ids[0], 'quotation_sent', cr)

        datas = {
            'model': 'sale.order',
            'ids': ids,
            'form': self.read(cr, uid, ids[0], context=context),
        }
        only_this_block = context.get('only_this_block')
        if only_this_block:
            datas['only_this_block'] = only_this_block

        return {
            'type': 'ir.actions.report.xml',
            'report_name': 'custom_block_sale_order_report',
            'datas': datas,
            'nodestroy': True,
        }
    '''

    # Fields function:
    @api.depends
    def _function_get_total_block(self):
        """ Fields function for calculate
        """
        for order in self:
            total = 0.0
            for block in order.block_ids:
                total += block.total or block.real_total
            order.real_total = total

    # Columns:
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
    _order = 'block_id,sequence'

    # Columns:
    block_id = fields.Many2one(
        'sale.order.block.group', 'Block', ondelete='set null')


class SaleOrderBlockGroupRelation(models.Model):
    """ Model name: SaleOrderBlockGroup
    """

    _inherit = 'sale.order.block.group'

    # Columns:
    line_ids = fields.One2many(
        'sale.order.line', 'block_id', 'Sale order line')
