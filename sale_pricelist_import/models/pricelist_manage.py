# Copyright 2019  Micronaet SRL (<https://micronaet.com>).
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

import os
import sys
import base64
import logging
import xlrd
import pdb
from odoo import fields, api, models, exceptions
from odoo.tools.translate import _


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
    def execute_query(self, query, parameters, log=True):
        """ Execute and log query
        """
        if log:
            query_file = os.path.expanduser('~/log')
            os.system('mkdir -p %s' % query_file)
            query_file = os.path.join(
                query_file, 'query.%s.log' % self._cr.dbname)
            query_f = open(query_file, 'a')
            line = '%s\n' % (query.replace('\n', ' ').replace('    ', ''))
            query_f.write(line % parameters)
            query_f.close()
            _logger.warning(line % parameters)
        self._cr.execute(query, parameters)

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
        pricelist.show_pricelist_form_file_query()

        fullname = pricelist.get_pricelist_fullname()
        try:
            wb = xlrd.open_workbook(fullname)
        except:
            pricelist.write({
                'error_comment': _('Cannot read XLS file: %s' % fullname),
                'state': 'loaded',  # Go back in status
            })
            pricelist.log_message('File error', '%s' % (sys.exc_info(), ))
            return True  # Done with error!
        first_row = pricelist.first_row or ''
        check_data = pricelist.check_data or ''
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

            if type(real_code) == float:
                real_code = str(int(real_code))

            try:
                price = float(price)
            except:
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
                'import_total': ws.nrows,
                'check_data': check_data,
                'first_row': first_row,
            })
            return False  # Done this block

        # Hide previous version:
        _logger.warning('Hide previous version still remained')
        hide_previous = product_pool.search([
            ('excel_pricelist_id', '=', excel_pricelist_id),
            ('pricelist_version', '<', pricelist.version),
        ])
        hide_previous.write({
            'active': False,
        })

        check_data += _('Totale righe su file <b>%s</b>') % ws.nrows
        pricelist.write({
            'first_row': first_row,
            'check_data': check_data,
            'state': 'available',
            # For 100.0% rate:
            'import_current': ws.nrows,
            'import_total': ws.nrows,
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
        query = """
            UPDATE product_template 
            SET active = 'f', sale_ok = 'f', purchase_ok = 'f'
            WHERE excel_pricelist_id=%s
            """
        parameters = (self.id, )
        self.execute_query(query, parameters)

        query = """
            UPDATE product_product 
            SET active = 'f'
            WHERE product_tmpl_id in (
                SELECT id 
                FROM product_template 
                WHERE excel_pricelist_id=%s);
            """
        parameters = (self.id, )
        self.execute_query(query, parameters)

        return self.write({
            'state': 'hide',
        })

    # Hide to Available
    @api.multi
    def show_pricelist_form_file_query(self):
        _logger.warning('Show all product items present')
        query = """
            UPDATE product_template 
            SET active = 't', sale_ok = 't', purchase_ok = 't'
            WHERE excel_pricelist_id=%s
            """
        parameters = (self.id, )
        self.execute_query(query, parameters)

        query = """
            UPDATE product_product 
            SET active = 't'
            WHERE product_tmpl_id in (
                SELECT id 
                FROM product_template 
                WHERE excel_pricelist_id=%s);
            """
        parameters = (self.id, )
        self.execute_query(query, parameters)

    @api.multi
    def show_pricelist_form_file(self):
        """ Show product items
        """
        self.show_pricelist_form_file_query()
        return self.write({
            'state': 'available',
        })

    # Available / Hide to Removed
    @api.multi
    def remove_pricelist_form_file(self):
        """ Hide product items
        """
        _logger.warning('Remove all product items present')
        # 1. Remove product same pricelist, not in sale order
        query = """
            DELETE FROM product_product 
            WHERE 
                product_tmpl_id IN (
                    SELECT id 
                    FROM product_template 
                    WHERE excel_pricelist_id=%s)
                AND id NOT IN (
                    SELECT product_id 
                    FROM sale_order_line);
            """
        parameters = (self.id, )
        self.execute_query(query, parameters)

        # 2. Remove template not in product remained
        query = """
            DELETE FROM product_template 
            WHERE 
                excel_pricelist_id=%s
                AND id NOT IN (
                    SELECT product_tmpl_id 
                    FROM product_product 
                    WHERE excel_pricelist_id=%s);
            """
        parameters = (self.id, self.id)
        self.execute_query(query, parameters)

        # 3. Hide remain template product:
        if not self.env.context.get('remain_not_hidden'):
            # This part is executed only for original method removed, not for
            # Dump mode:
            query = """
                UPDATE product_template 
                SET active = 'f', sale_ok = 'f', purchase_ok = 'f'
                WHERE excel_pricelist_id=%s
                """
            parameters = (self.id, )
            self.execute_query(query, parameters)

            return self.write({
                'state': 'removed',
            })
        return True

    # Restore:
    @api.multi
    def restore_pricelist_odoo_table(self):
        """ Restore dumped database in available state
        """
        pricelist_id = self.id
        # 1. Restore as product (template/product):
        dump_pool = self.env['product.product.dump']
        product_pool = self.env['product.product']
        for dump in dump_pool.search([
                ('excel_pricelist_id', '=', pricelist_id)]):
            product_pool.create({
                'name': dump.name,
                'product_link': dump.product_link,
                'active': dump.active,
                'sale_ok': dump.sale_ok,
                'purchase_ok': dump.purchase_ok,
                'excel_pricelist_id': pricelist_id,
                'pricelist_version': dump.pricelist_version,
                'real_code': dump.real_code,
                'default_code': dump.default_code,
                'uom_id:': dump.uom_id.id,
                'uom_po_id': dump.uom_po_id.id,
                'list_price': dump.list_price,

                # Auto fields:
                'create_uid': dump.create_uid.id,
                'create_date': dump.create_date,
                'write_uid': dump.write_uid.id,
                'write_date': dump.write_date,

                # Mandatory fields:
                'type': dump.type,
                'categ_id': dump.categ_id.id,
                'responsible_id': dump.responsible_id.id or 1,
                'tracking': dump.tracking,
                'sale_line_warn': dump.sale_line_warn,

            })

        # 3. Clean dump table:
        query = """
            DELETE FROM product_product_dump
            WHERE id IN (
                SELECT id
                FROM product_product_dump
                WHERE excel_pricelist_id=%s);
            """
        parameters = (self.id, )
        self.execute_query(query, parameters)

        # 4. Update status:
        return self.write({
                'state': 'available',
            })

    # Dump pricelist:
    @api.multi
    def dump_pricelist_odoo_table(self):
        """ Dump all unused product in product dump table
        """
        _logger.warning(
            'Dump all unused product and remove from original object')

        # 1. Create dump of unused in sold product:
        query = """
            INSERT INTO product_product_dump(
                name, product_link, active, sale_ok, purchase_ok,
                excel_pricelist_id, pricelist_version, real_code,
                default_code, uom_id, list_price, categ_id, type,
                uom_po_id, responsible_id,
                create_uid, create_date, write_uid, write_date
            )
            SELECT
                name, product_link, active, sale_ok, purchase_ok,
                excel_pricelist_id, pricelist_version, real_code,
                default_code, uom_id, list_price, categ_id, type,
                uom_po_id, responsible_id,
                create_uid, create_date, write_uid, write_date
            FROM product_template
            WHERE
                id IN (
                    SELECT id
                    FROM product_template
                    WHERE excel_pricelist_id=%s)
                AND id NOT IN (
                    SELECT product_tmpl_id
                    FROM product_product
                    WHERE id IN
                        (SELECT product_id FROM sale_order_line)
                    );
            """
        parameters = (self.id, )
        self.execute_query(query, parameters)

        # 2. Call original method for remove all pricelist (no hide remain):
        self.with_context({
            'remain_not_hidden': True,
        }).remove_pricelist_form_file()

        # 3. Update new state:
        return self.write({
            'state': 'dumped',
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
            ('dumped', 'Dumped'),  # Dump in another table
            # ('error', 'Error'),
        ],
        required=True,
        default='draft',
    )
    sql_constraints = [
        ('name_supplier_id_uniq', 'UNIQUE (supplier_id,name)',
         'You can not have two pricelist same supplier-name!')
    ]


class ProductProduct(models.Model):
    _inherit = 'product.product'

    @api.multi
    def hide_product_pricelist(self):
        """ Hide product
        """
        return self.env['dialog.box.wizard'].open_dialog(
            message=_('The product will be hided, <b>you cannot use again</b> '
                      'but remain in sale order where yet present, <br/>'
                      'confirm?'),
            action='self.env["product.product"].browse(%s).write('
                   '{"active": False})' % self.id,
            title=_('Confirm request:'),
            mode='cancel_confirm',
        )


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

    @api.model
    def get_total_product_pricelist(self):
        """ Total product found
        """
        for pricelist in self:
            pricelist.product_total = len(pricelist.product_ids)

    product_ids = fields.One2many(
        comodel_name='product.template',
        inverse_name='excel_pricelist_id',
        string='Product linked',
    )
    product_total = fields.Integer(
        string='Total product', compute='get_total_product_pricelist')


class ProductProductDump(models.Model):
    """ Dump data for product.product - template as history external database
    """
    _name = 'product.product.dump'
    _description = 'Product Dump'
    _order = 'default_code'

    # product.template
    name = fields.Char('Name', size=80)
    product_link = fields.Char('Name', size=80)
    active = fields.Boolean('Active')
    sale_ok = fields.Boolean('Sale OK')
    purchase_ok = fields.Boolean('Purchase OK')
    excel_pricelist_id = fields.Many2one(
        comodel_name='excel.pricelist.item',
        string='Excel pricelist',
    )
    pricelist_version = fields.Integer(
        string='Pricelist version',
    )
    real_code = fields.Char(
        string='Real code')
    default_code = fields.Char(
        string='Default code')
    uom_id = fields.Many2one(
        comodel_name='product.uom',
        string='UOM',
    )
    uom_po_id = fields.Many2one(
        comodel_name='product.uom',
        string='UOM Po',
    )
    list_price = fields.Float(
        string='List price',
    )
    type = fields.Char('Type')
    categ_id = fields.Many2one('product.category', 'Category')
    responsible_id = fields.Many2one('res.users', 'Responsibile')
    tracking = fields.Char('Tracking')
    sale_line_warn = fields.Char('Sale line warn.')

    create_uid = fields.Many2one('res.users', 'Create by')
    write_uid = fields.Many2one('res.users', 'Write by')
    create_date = fields.Datetime('Create')
    write_date = fields.Datetime('Write')

    # service_type 'manual'
    # type 'service', 'consu', 'manual'
    # invoice_policy 'order'
    # rental f
    # barcode
    # active
    # default_code
    # volume
    # weight
