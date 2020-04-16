# Copyright 2019  Micronaet SRL (<http://www.micronaet.it>).
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

import logging
from odoo import models, fields, api

_logger = logging.getLogger(__name__)


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    # Button:
    @api.multi
    def update_all_multi_discount(self):
        """ Update all price multi discount
        """
        line_pool = self.env['sale.order.line']
        discount_multi_rate, discount = line_pool.get_multirate_data(
            self.discount_multi_rate)

        for line in self.order_line:
            line.write({
                'discount_multi_rate': discount_multi_rate,
                'discount': discount,
            })

    # Columns:
    discount_multi_rate = fields.Char('Default multi rates', size=50)


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    @api.model
    def get_multirate_data(self, discount_multi_rate):
        """ Extract procedure from text multidiscount field
        """
        discount_multi_rate = discount_multi_rate or ''
        discount_block = discount_multi_rate.replace(
            ' ', '').replace(
            ',', '.').replace(
            '%', '').strip('+').split('+')
        base_discount = 100.0
        for rate in discount_block:
            try:
                i = float(rate)
            except:
                _logger.error('Cannot found rate for %s' % rate)
                i = 0.00
            base_discount -= base_discount * i / 100.0
        return (
            ' + '.join(discount_block),
            100.0 - base_discount,
        )

    # Onchange method:
    @api.onchange('discount_multi_rate')
    def onchange_discount_multi_rate(self):
        """ Calc correct discount and clean text insert
        """
        discount_multi_rate, discount = self.get_multirate_data(
            self.discount_multi_rate)
        self.discount_multi_rate = discount_multi_rate
        self.discount = discount

    # Columns:
    discount_multi_rate = fields.Char('Discount multi rates', size=50)
    # Override:
    discount = fields.Float(
        string='Discount (%)',
        digits=(20, 10),  # dp.get_precision('Discount'),
        default=0.0)
