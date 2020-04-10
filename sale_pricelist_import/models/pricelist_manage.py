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
    @api.multi
    def return_original_pricelist(self):
        """ Return original file imported
        """
        def slugify(text, separator='-'):
            """ Slug the text
            """
            res = ''
            for c in text:
                if c.isalpha() or c.isspace():
                    res += c
            res = res.lower().replace(' ', separator).replace('.', '')
            return res

        fullname = self.get_pricelist_fullname()
        return_name = slugify(u'%s %s' % (
            self.supplier_id.name,
            self.name or '',
        ))
        return_name = '%s.xlsx' % return_name
        _logger.info('Return %s file as %s' % (
            fullname,
            return_name,
        ))

        return {
            'type': 'ir.actions.act_url',
            'name': 'contract',
            'url': '/web/content/%s/%s/%s/%s?download=true' % (
                self._name,
                self.id,
                'file_stored',
                return_name
            ),
        }

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
    def get_pricelist_fullname(self):
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
        fullname = self.get_pricelist_fullname()
        b64_file = base64.decodebytes(self.file_data)
        f = open(fullname, 'wb')
        f.write(b64_file)
        f.close()

        self.write({
            'state': 'loaded',
            'file_data': False,  # Remove data from database
            'version': version,

            # For reimport process status:
            'check_data': '',
            'first_row': '',
            'import_current': 0,
            'import_total': 0,
        })

    # Loaded to Available
    @api.multi
    def schedule_available_pricelist_form_file(self):
        """ Schedule for load
        """
        return self.write({
            'state': 'scheduled',
        })

    @api.model
    def etl_available_pricelist_form_file(self, pricelist_id, import_block=50):
        """ Scheduled import pricelist and store (single)
            @return True if end import (also error), else False
        """
        product_pool = self.env['product.template']
        pricelist = self.browse(pricelist_id)

        _logger.warning(
            'Start import pricelist (Show all for update if present): %s' % (
                pricelist.name,
            )
        )
        # Show all before update:
        pricelist.show_pricelist_form_file()

        fullname = pricelist.get_pricelist_fullname()
        try:
            wb = xlrd.open_workbook(fullname)
        except:
            pricelist.write({
                'error_comment': _('Cannot read XLS file: %s' % fullname),
                'state': 'loaded',  # Go back in status
            })
            return True  # Done with error!
        first_row = pricelist.check_data or ''
        check_data = pricelist.first_row or ''
        total = 0
        current = pricelist.import_current
        ws = wb.sheet_by_index(0)

        version = pricelist.version
        pricelist_prefix = pricelist.pricelist_prefix or ''
        excel_pricelist_id = pricelist.id
        uom_id = 1

        start = max(pricelist.start - 1, current)
        end = min(ws.nrows, start + import_block)

        _logger.warning('Pricelist %s, block [%s:%s]' % (
            pricelist.name, start, end - 1
        ))
        for row in range(start, end):  # Loop with block
            log_row = row + 1
            _logger.warning('Import line %s' % row)
            real_code = ws.cell(row, 0).value
            name = ws.cell(row, 1).value
            price = ws.cell(row, 2).value or 0.0

            # Check if line is correct:
            if not all((real_code, name, price)):
                check_data += _(
                    '%s. Missed some value %s!<br/>') % (
                        log_row, (real_code, name, price))
                continue
            if type(price) != float:
                check_data += _(
                    '%s. Jump, No float data: %s!<br/>') % (log_row, price)
                continue

            default_code = '%s%s' % (pricelist_prefix, real_code)
            if not first_row:
                first_row = '''
                    <b>Codice:</b> %s | <b>Descrizione:</b> %s | 
                    <b>Prezzo:</b> %s''' % (
                        default_code, name, price)

            # Update product:
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
        if end < ws.nrows:
            pricelist.write({
                'import_current': end,
                'import_total': ws.nrows
            })
            return False  # Done this block

        # Hide previous version:
        _logger.warning('Hide previous version still remained')
        hide_previous = product_pool.search([
            ('pricelist_version', '<', pricelist.version),
        ])
        hide_previous.write({
            'active': False,
        })

        check_data += _('Totale righe <b>%s</b>, importate: <b>%s</b>') % (
            ws.nrows, total)
        pricelist.write({
            'first_row': first_row,
            'check_data': check_data,
            'state': 'available',
        })
        return True

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

    # Fields function:
    @api.one
    def _get_stored_pricelist(self):
        """ File saved as binary
        """
        fullname = self.get_pricelist_fullname()
        self.file_stored = base64.b64encode(
            open(fullname, 'rb').read())

    @api.depends('import_current', 'import_total')
    @api.multi
    def update_import_rate(self):
        for pricelist in self:
            if pricelist.import_total:
                pricelist.import_rate = \
                    100.0 * pricelist.import_current / pricelist.import_total
            else:
                if pricelist.state in ('draft', 'loaded'):
                    pricelist.import_total = 0.0
                else:
                    pricelist.import_total = 100.0

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
    # Import status:
    import_current = fields.Integer(
        string='Current imported',
    )
    import_total = fields.Integer(
        string='Total to import',
    )
    import_rate = fields.Float(
        string='Import rate',
        compute='update_import_rate',
    )

    version = fields.Integer(
        string='Version',
        readonly=True,
        track_visibility=True,
    )
    file_data = fields.Binary(
        string='Excel file',
    )
    file_stored = fields.Binary(
        'Stored', compute='_get_stored_pricelist')
    check_data = fields.Text(
        string='Check data',
        help='Check error in data file',
        widget='html',
    )
    error_comment = fields.Text(
        string='Error comment',
        help='Raise error during importation',
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
            ('scheduled', 'Scheduled'),
            ('available', 'Available'),
            ('hide', 'Hide'),
            ('removed', 'Removed'),  # Return to draft?
            # ('error', 'Error'),
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

