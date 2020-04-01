# Copyright 2019  Micronaet SRL (<https://micronaet.com>).
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

import logging
from odoo import fields, api, models
from odoo import tools
from odoo.tools.translate import _

_logger = logging.getLogger(__name__)


class ReportSaleOrderBlock(models.AbstractModel):
    """ Block report parser
    """
    _name = 'report.sale_order_block.report_sale_block_lang'

    @api.model
    def get_report_values(self, docids, data=None):
        """ Render report invoice parser:
        """
        return {
            'doc_ids': docids,
            'doc_model': 'sale.order',
            'docs': self.env['sale.order'].search([('id', 'in', docids)]),
            }
