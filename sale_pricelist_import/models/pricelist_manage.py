# Copyright 2019  Micronaet SRL (<https://micronaet.com>).
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

import os
import base64
import logging
import xlrd
from odoo import fields, api, models
from odoo.tools.translate import _
from odoo.exceptions import (
    AccessError, UserError, RedirectWarning, ValidationError, Warning)


_logger = logging.getLogger(__name__)


class ExcelPricelistItem(models.Model):
    _name = 'excel.pricelist.item'
    _description = 'Excel pricelist item'
    _rec_name = 'name'
    _order = 'supplier_id,name'
    _root_filestore = r'~/.local/share/Odoo/filestore'
    _inherit = ['mail.thread']

    # -------------------------------------------------------------------------
    # Utility
    # -------------------------------------------------------------------------
    @api.model
    def log_message(self, subject, body, message_type='notification'):
        """ Write log message
        """
        body = ("""
            <div class="o_mail_notification">
                %s
            </div>
            """) % body

        return self.sudo().message_post(
            body=body,
            message_type=message_type,
            subject=subject,
            )

    # -------------------------------------------------------------------------
    # Wkf Button operation:
    # -------------------------------------------------------------------------
    @api.model
    def _get_pricelist_fullname(self):
        """ Pricelist path
        """
        root_pricelist = os.path.join(
            os.path.expanduser(self._root_filestore),
            self._cr.dbname,
            'Pricelist',
        )
        # Create if not present
        os.system('mkdir -p %s' % root_pricelist)
        return os.path.join(root_pricelist, 'pricelist_%s.xlsx' % self.id)

    # Draft to Loaded
    @api.multi
    def upload_pricelist_from_file(self):
        """ Import selected file
        """
        version = self.version
        version += 1
        # Save binary data to file:
        fullname = self._get_pricelist_fullname()
        b64_file = base64.decodebytes(self.file_data)
        f = open(fullname, 'wb')
        f.write(b64_file)
        f.close()

        self.write({
            'state': 'loaded',
            'file_data': False,  # Remove data from database
            'version': version,
        })

    # Loaded to Available
    @api.multi
    def available_pricelist_form_file(self):
        """ Import pricelist and store
        """
        product_pool = self.env['product.template']

        # Show all before update:
        _logger.warning('Show all for update if present')
        self.show_pricelist_form_file()

        fullname = self._get_pricelist_fullname()
        try:
            wb = xlrd.open_workbook(fullname)
        except:
            raise Warning(_('Cannot read XLS file: %s' % fullname))

        start = self.start - 1
        version = self.version
        pricelist_prefix = self.pricelist_prefix or ''
        excel_pricelist_id = self.id
        uom_id = 1

        first_row = check_data = ''
        total = 0
        ws = wb.sheet_by_index(0)
        for row in range(start, ws.nrows):
            log_row = row + 1
            if not (row % 50):
                _logger.info('%s: Row imported %s / %s' % (
                    fullname,
                    row,
                    ws.nrows
                ))
            real_code = ws.cell(row, 0).value
            if not real_code:
                check_data += _('%s. Product code not found!<br/>') % log_row
                continue
            name = ws.cell(row, 1).value
            price = ws.cell(row, 2).value or 0.0
            default_code = '%s%s' % (pricelist_prefix, real_code)
            if not first_row:
                first_row = '''
                    <b>Codice:</b> %s | <b>Descrizione:</b> %s | 
                    <b>Prezzo:</b> %s''' % (
                        default_code, name, price)

            # Update product:
            # TODO hide previous product if present?
            total += 1
            products = product_pool.search([
                ('real_code', '=', real_code),
                ('excel_pricelist_id', '=', excel_pricelist_id),
            ])
            data = {
                'excel_pricelist_id': excel_pricelist_id,
                'real_code': real_code,
                'name': name,
                'default_code': default_code,
                'lst_price': price,
                'uom_id': uom_id,
                'pricelist_version': version,
            }
            if products:
                products.write(data)
            else:
                product_pool.create(data)

        # Hide previous version:
        _logger.warning('Hide previous version still remained')
        hide_previous = product_pool.search([
            ('pricelist_version', '<', self.version),
        ])
        hide_previous.write({
            'active': False,
        })

        check_data += _('Totale righe <b>%s</b>, importate: <b>%s</b>') % (
            ws.nrows, total)
        return self.write({
            'first_row': first_row,
            'check_data': check_data,
            'state': 'available',
        })

    # All to Draft
    @api.multi
    def new_pricelist_form_file(self):
        """ Hide product items
        """
        # Show all for update operation (if present)
        _logger.warning('Restart from draft')
        return self.write({
            'state': 'draft',
            'first_line': False,
        })

    # Available to Hide
    @api.multi
    def hide_pricelist_form_file(self):
        """ Hide product items
        """
        _logger.warning('Hide all product items present')
        cr = self._cr
        cr.execute("""
            UPDATE product_template 
            SET active = 'f', sale_ok = 'f', purchase_ok = 'f'
           
            WHERE excel_pricelist_id=%s
            """ % self.id)

        return self.write({
            'state': 'hide',
        })

    # Hide to Available
    @api.multi
    def show_pricelist_form_file(self):
        """ Show product items
        """
        _logger.warning('Show all product items present')
        cr = self._cr
        cr.execute("""
            UPDATE product_template 
            SET active = 't', sale_ok = 't', purchase_ok = 't'
            WHERE excel_pricelist_id=%s
            """ % self.id)

        return self.write({
            'state': 'available',
        })

    # Available / Hide to Removed
    @api.multi
    def remove_pricelist_form_file(self):
        """ Hide product items
        """
        _logger.warning('Remove all product items present')
        cr = self._cr

        # Remove product same pricelist, not in sale order
        cr.execute("""
            DELETE FROM product_product 
            WHERE 
                product_tmpl_id IN (
                    SELECT id 
                    FROM product_template 
                    WHERE excel_pricelist_id=%s)
                AND id NOT IN (
                    SELECT product_id 
                    FROM sale_order_line);
            """, (self.id, ))

        # Remove template not in product remained
        cr.execute("""
            DELETE FROM product_template 
            WHERE 
                excel_pricelist_id=%s
                AND id NOT IN (
                    SELECT product_tmpl_id 
                    FROM product_product 
                    WHERE excel_pricelist_id=%s);
            """, (self.id, self.id))

        # Hide remain template product:
        cr.execute("""
            UPDATE product_template 
            SET active = 'f', sale_ok = 'f', purchase_ok = 'f'
            WHERE excel_pricelist_id=%s
            """ % self.id)

        return self.write({
            'state': 'removed',
        })

    name = fields.Char('Name', required=True)
    timestamp_update = fields.Datetime(
        string='Timestamp_update',
        required=True,
        default=fields.Datetime.now,
    )
    supplier_id = fields.Many2one(
        comodel_name='res.partner',
        string='Supplier',
        required=True,
        domain="[('supplier', '=', True)]",
        context="{'default_supplier': True, 'default_customer': False}"
    )
    pricelist_prefix = fields.Char(
        'Pricelist prefix', size=4,
        track_visibility=True,
    )
    start = fields.Integer(
        string='Start row',
        required=True,
        default=1,
    )
    version = fields.Integer(
        string='Version',
        readonly=True,
        track_visibility=True,
    )
    file_data = fields.Binary(
        string='Excel file',
    )
    check_data = fields.Text(
        string='Check data',
        help='Check error in data file',
        widget='html',
    )
    first_row = fields.Char(
        string='First row',
        help='Check first row to be imported on file',
        widget='html',
    )
    state = fields.Selection(
        string='State',
        track_visibility=True,
        selection=[
            ('draft', 'Draft'),
            ('loaded', 'Saved'),
            ('available', 'Available'),
            ('hide', 'Hide'),
            ('removed', 'Removed'),  # Return to draft?
        ],
        required=True,
        default='draft',
    )
    sql_constraints = [
        ('name_supplier_id_uniq', 'UNIQUE (supplier_id,name)',
         'You can not have two pricelist same supplier-name!')
    ]


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    excel_pricelist_id = fields.Many2one(
        comodel_name='excel.pricelist.item',
        string='Excel pricelist',
    )
    pricelist_version = fields.Integer(
        string='Pricelist version',
    )
    real_code = fields.Char(
        string='Real code')


class ExcelPricelistItemRelation(models.Model):
    _inherit = 'excel.pricelist.item'

    product_ids = fields.One2many(
        comodel_name='product.template',
        inverse_name='excel_pricelist_id',
        string='Product linked',
    )

