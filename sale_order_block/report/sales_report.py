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

    # -------------------------------------------------------------------------
    # Parser function:
    # -------------------------------------------------------------------------
    @api.model
    def show_the_block(self, block, data=None):
        """ Check if the block need to be showed
        """
        if data is None:
            data = {}
        only_this_block = data.get('only_this_block')
        if only_this_block:
            return only_this_block == block.id
        return not block.hide_block

    @api.model
    def clean_name(self, line):
        """ Clean line product name depend on block setup
        """
        name = line.name
        if line.block_id.show_code:
            return name

        name = name.split('] ')[-1]
        return name

    @api.model
    def get_report_values(self, docids, data=None):
        """ Render report invoice parser:
        """
        print(data)
        import pdb; pdb.set_trace()
        return {
            'doc_ids': docids,
            'doc_model': 'sale.order',
            'docs': self.env['sale.order'].search([('id', 'in', docids)]),
            'data': data,

            # Parser function:
            'clean_name': self.clean_name,
            'show_the_block': self.show_the_block,
        }
