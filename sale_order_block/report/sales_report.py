# Copyright 2019  Micronaet SRL (<https://micronaet.com>).
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

import logging
from odoo import fields, api, models

_logger = logging.getLogger(__name__)


class ReportSaleOrderBlock(models.AbstractModel):
    """ Block report parser
    """
    _name = 'report.sale_order_block.report_sale_block_lang'

    # -------------------------------------------------------------------------
    # Override
    # -------------------------------------------------------------------------
    @api.model
    def get_report_values(self, docids, data=None):
        """ Render report invoice parser:
            Note: ex render_html(self, docids, data)
        """
        print('DocIDS: %s' % (docids, ))
        print(data)
        import pdb; pdb.set_trace()
        model_name = 'sale.order'
        docs = self.env[model_name].browse(docids)
        return {
            'doc_ids': docids,
            'doc_model': model_name,
            'docs': docs,
            'data': data,

            # Parser function:
            'clean_name': self.clean_name,
            'show_the_block': self.show_the_block,
        }

    # -------------------------------------------------------------------------
    # Parser function:
    # -------------------------------------------------------------------------
    @api.model
    def show_the_block(self, block, data=None):
        """ Check if the block need to be showed
        """
        #import pdb; pdb.set_trace()
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

