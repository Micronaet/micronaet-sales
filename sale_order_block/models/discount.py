# Copyright 2019  Micronaet SRL (<http://www.micronaet.it>).
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

import logging
from odoo import models, fields, api

_logger = logging.getLogger(__name__)


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    # Columns:
    discount_multi_rate = fields.Char('Default multi rates', size=50)


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    # Onchange method:
    @api.onchange('discount_multi_rate')
    def onchange_discount_multi_rate(self):
        """ Calc correct discount and clean text insert
        """
        discount_block = self.discount_multi_rate.replace(
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
        self.discount_multi_rate = '% + '.join(discount_block) + '%'
        self.discount = 100.0 - base_discount

    # Columns:
    discount_multi_rate = fields.Char('Discount multi rates', size=50)
    # Override:
    discount = fields.Float(
        string='Discount (%)',
        digits=(20, 10),  # dp.get_precision('Discount'),
        default=0.0)
