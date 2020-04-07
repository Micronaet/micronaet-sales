# Copyright 2019  Micronaet SRL (<https://micronaet.com>).
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

import os
import base64
import logging
from odoo import fields, api, models

_logger = logging.getLogger(__name__)


class ExcelPricelistItem(models.Model):
    _name = 'excel.pricelist.item'
    _description = 'Excel pricelist item'
    _rec_name = 'supplier_id'
    _order = 'supplier_id'
    _root_filestore = r'~/.local/share/Odoo/filestore'

    # -------------------------------------------------------------------------
    # Wkf Button operation:
    # -------------------------------------------------------------------------
    @api.multi
    def import_pricelist_form_file(self):
        """ Import pricelist and store
        """
        return True

    # Draft to Loaded
    @api.multi
    def upload_pricelist_file(self):
        """ Import selected file
        """
        root_pricelist = os.path.join(
            os.path.expanduser(self._root_filestore),
            self._cr.dbname,
        )
        # Create if not present
        os.system('mkdir -p %s' % root_pricelist)

        # Save binary data to file:
        fullname = os.path.join(root_pricelist, 'pricelist_%s.xlsx' % self.id)
        b64_file = base64.decodebytes(self.file_data)
        f = open(fullname, 'wb')
        f.write(b64_file)
        f.close()

    timestamp_update = fields.Datetime(
        string='Timestamp_update',
        required=True,
        default=fields.Datetime.now,
    )
    supplier_id = fields.Many2one(
        comodel_name='res.partner',
        string='Supplier',
        required=True,
        domain="[('supplier', '=', True)]")
    start = fields.Integer(
        string='Start row',
        required=True,
        default=1,
    )
    file_data = fields.Binary(
        string="Excel file",
        required=True,
    )
    state = fields.Selection(
        string='State',
        selection=[
            ('draft', 'Draft'),
            ('loaded', 'Loaded'),
            ('available', 'Available'),
            ('hide', 'Hide'),
            ('removed', 'Removed'),  # Return to draft?
        ],
        required=True,
        default='draft',
    )
