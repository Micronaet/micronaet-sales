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
        ''' Print sale order only with this block
        '''
        sale_pool = self.env['sale.order']
        return sale_pool.with_context(only_block=[self.id]).print_quotation()

    @api.depends
    def _function_get_total_block(self):
        ''' Fields function for calculate 
        '''
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
    code = fields.Integer('Code', required=True)
    name = fields.Char('Name', size=64, required=True)
    block_margin = fields.Float(
        'Extra recharge %', digits=(16, 3) 
        help='Add extra recharge to calculate real total')
    
    pre_text = fields.Text('Pre text')
    post_text = fields.Text('Post text')
    
    total = fields.Float(
        'Block total', digits=(16, 2) 
        help='Total written in offer block')
    real_total = fields.Float(
        string='Real total', store=False, 
        compute='_function_get_total_block',
        help='Total sum of sale line in this block')
    order_id = fields.Many2one('sale.order', 'Order', ondelete='cascade')
    
    # Parameter for line:
    hide_block = fields.Boolean(
        'Hide block', help='Hide in report for simulation')
    not_confirmed = fields.Boolean(
        'Not confirmed', help='Removed from order')

    show_header = fields.Boolean('Show header', default=True)
    show_detail = fields.Boolean('Show details', default=True)
    show_code = fields.Boolean(
        'Show code', default=True, 
        help='Show code in line details')
    show_price = fields.Boolean(
        'Show price', default=True, 
        help='Show unit price and subtotal')
    #'show_subtotal = fields.Boolean('Show Subtotal', default=True)
    show_total = fields.Boolean('Show total', default=True)        

