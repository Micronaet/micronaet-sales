# Copyright 2019  Micronaet SRL (<http://www.micronaet.it>).
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

import logging
from odoo import models, fields, api

_logger = logging.getLogger(__name__)


class SaleOrderText(models.Model):
    """ Model name: Sale Order Text
    """

    _name = 'sale.order.text'
    _description = 'Sale order text'
    _order = 'name'

    name = fields.Char(
        string='Name',
        required=True)
    text = fields.Text(
        string='Text',
        required=True,
    )


class SaleOrderTextRel(models.Model):
    """ Model name: Sale Order Text Rel
    """

    _name = 'sale.order.text.rel'
    _description = 'Sale order text rel'
    _order = 'text_id'

    sequence = fields.Integer(string='Sequence')
    pagebreak_before = fields.Boolean(string='Pagebreak before')
    text_id = fields.Many2one(
        comodel_name='sale.order.text',
        string='Text',
        required=True,
        ondelete='cascade',
    )
    order_id = fields.Many2one(
        comodel_name='sale.order',
        string='Sale order',
        ondelete='cascade',
    )


class SaleOrderBlockGroup(models.Model):
    """ Model name: SaleOrderBlockGroup
    """

    _name = 'sale.order.block.group'
    _description = 'Sale order block'
    _order = 'name'

    @api.one
    def has_discount(self):
        """ Check if there's one line with discount
        """
        return any([line.discount_multi_rate for line in self.line_ids])

    # Button events:
    @api.multi
    def duplicate_block_items(self):
        """ Duplicate this block
        """
        # Duplicate block:
        new_block = self.copy(default={'title': '%s bis' % self.title})

        # Duplicate sale.order.line
        line_pool = self.env['sale.order.line']
        lines = line_pool.search([('block_id', '=', self.id)])
        for line in lines:
            line.copy(default={
                'block_id': new_block.id,
                'order_id': self.order_id.id,
            })
        return True

    @api.multi
    def print_only_this(self):
        """ Print sale order only with this block
        """
        order = self.order_id
        self.env.context = dict(self.env.context)
        self.env.context.update({
            'only_this_block': self.id,
        })
        return order.print_quotation()

    @api.multi
    def _function_get_total_block(self):
        """ Fields function for calculate
            # for sol in block.order_id.order_line:
            #     if sol.block_id.id == block.id:
        """
        for block in self:
            total = 0.0
            for sol in block.line_ids:
                total += sol.price_subtotal
            block.current_total = total

            if block.block_margin:
                total *= 100.0 + block.block_margin
                total /= 100.0
            block.real_total = total

    # Columns:
    name = fields.Integer(
        'Code', required=True)
    title = fields.Char(
        'Title', size=64, required=True)
    block_margin = fields.Float(
        'Extra recharge %', digits=(16, 3),
        help='Add extra recharge to calculate real total')

    pre_text = fields.Text('Pre text')
    post_text = fields.Text('Post text')

    total = fields.Float(
        'Forced total', digits=(16, 2),
        help='Total written in offer block')
    current_total = fields.Float(
        string='Current total',
        store=False,
        multi=True,
        compute='_function_get_total_block',
        help='Total sum of sale line in this block')
    real_total = fields.Float(
        string='Real total',
        store=False,
        multi=True,
        compute='_function_get_total_block',
        help='Total sum of sale line in this block (with margin)')
    order_id = fields.Many2one(
        'sale.order',
        'Order',
        ondelete='cascade',
    )

    # Parameter for line:
    hide_block = fields.Boolean(
        'Hide block', help='Hide in report for simulation')
    not_confirmed = fields.Boolean(
        'Not confirmed', help='Removed from order')

    show_header = fields.Boolean(
        'Show header', default=True)
    show_detail = fields.Boolean(
        'Show details', default=True)
    show_code = fields.Boolean(
        'Show code', default=True,
        help='Show code in line details')
    show_price = fields.Boolean(
        'Show price', default=True,
        help='Show unit price and subtotal')
    # 'show_subtotal = fields.Boolean('Show Subtotal', default=True)
    show_total = fields.Boolean('Show total', default=True)


class AccountPaymentTerm(models.Model):
    """ Model name: Account payment term
    """
    _inherit = 'account.payment.term'

    account_ref = fields.Char('Rif. contabile', size=9)


class ResUsers(models.Model):
    """ Model name: Res users
    """
    _inherit = 'res.users'

    account_ref = fields.Char('Rif. contabile', size=9)


class ProductUom(models.Model):
    """ Model name: Product uom
    """
    _inherit = 'product.uom'

    account_ref = fields.Char('Rif. contabile', size=9)


class AccountTax(models.Model):
    """ Model name: Account tax
    """
    _inherit = 'account.tax'

    account_ref = fields.Char('Rif. contabile', size=9)


class ProductTemplateExtraFields(models.Model):
    """ Model name: Product template
    """
    _inherit = 'product.template'

    # Onchange method:
    @api.onchange('default_code')
    def onchange_default_code_upper(self):
        """ Always upper
        """
        self.default_code = (self.default_code or '').upper()

    product_link = fields.Char('Product link', size=120)

class ProductProductExtraFields(models.Model):
    """ Model name: Product product
    """
    _inherit = 'product.product'

    # Onchange method:
    @api.onchange('default_code')
    def onchange_default_code_upper(self):
        """ Always upper
        """
        self.default_code = (self.default_code or '').upper()


class SaleOrder(models.Model):
    """ Model name: SaleOrder
    """
    _inherit = 'sale.order'

    """
    @api.multi
    def _get_printed_report_name(self):
        import pdb; pdb.set_trace()
        self.ensure_one()
        return '%s.%s' % (
            (object.name or 'draft').replace('/', '_'),
            object.printed
            )
    """

    # -------------------------------------------------------------------------
    # Button events:
    # -------------------------------------------------------------------------
    @api.multi
    def action_confirm(self):
        """ Confirm block marked and move extra line in unused list
        """
        order_id = self.id
        for line in self.order_line:
            if line.block_id.not_confirmed:
                # Move unused block line in unused list
                line.write({
                    'order_id': False,
                    'unused_order_id': order_id
                })
            else:
                # TODO Export for accounting
                pass
        return self.write({
            'account_state': 'confirmed',
        })

    @api.multi
    def action_cancel(self):
        """ Confirm overrided
        """
        return self.write({
            'account_state': 'cancel',
        })

    @api.multi
    def account_cancel_accounting(self):
        """ Confirm case import in accounting
        """
        return self.write({
            'account_state': 'cancel',
        })

    @api.multi
    def account_restart(self):
        """ Confirm case import in accounting
        """
        return self.write({
            'account_state': 'draft',
        })

    @api.multi
    def dummy_action(self):
        """ Dummy button to refresh data
        """
        return True

    # Override function:
    @api.one
    @api.returns('self', lambda value: value.id)
    def copy(self, default=None):
        """ Duplicate also block information
        """
        # Pool used:
        block_pool = self.env['sale.order.block.group']
        sol_pool = self.env['sale.order.line']
        text_rel_pool = self.env['sale.order.text.rel']

        new_order = super(SaleOrder, self).copy(default)
        new_id = new_order.id
        old_id = self.id

        if not self.block_ids:
            return new_order

        blocks = block_pool.search([
            ('order_id', '=', old_id),
        ])
        convert_db = []

        # TODO When adding new parameter put here!
        # ---------------------------------------------------------------------
        # Duplicate block list:
        # ---------------------------------------------------------------------
        _logger.warning('Duplicate extra block in sale: %s' % len(blocks))
        for block in blocks:
            data = {
                'name': block.name,
                'title': block.title,

                'pre_text': block.pre_text,
                'post_text': block.post_text,

                'total': block.total,
                # 'real_total':
                'order_id': new_id,

                # Parameter for line:
                'show_header': block.show_header,
                'show_detail': block.show_detail,
                'show_code': block.show_code,
                'show_price': block.show_detail,
                # 'show_subtotal': fields.boolean('Show Subtotal'),
                'show_total': block.show_total,

                'hide_block': False,  # Forced!
                'not_confirmed': False,  # Forced!
            }
            convert_db.append((block.id, block_pool.create(data).id))

        # ---------------------------------------------------------------------
        # Fixed block:
        # ---------------------------------------------------------------------
        for block in self.report_text_ids:
            text_rel_pool.create({
                'sequence': block.sequence,
                'order_id': new_id,
                'text_id': block.text_id.id,
                'pagebreak_before': block.pagebreak_before,
            })

        # ---------------------------------------------------------------------
        # Restore unused lines:
        # ---------------------------------------------------------------------
        self.unused_order_line_ids.write({
            'order_id': new_id,
            'unused_order_id': False,
        })

        # ---------------------------------------------------------------------
        # Change reference for block in detail list:
        # ---------------------------------------------------------------------
        _logger.warning('Update reference in details: %s' % len(convert_db))
        for old, new in convert_db:
            lines = sol_pool.search([
                ('order_id', '=', new_id),
                ('block_id', '=', old),
            ])
            if not lines:
                continue
            lines.write({
                'block_id': new,
            })

        # ---------------------------------------------------------------------
        # Extra fields in order:
        # ---------------------------------------------------------------------
        new_order.write({
            'client_order_ref': self.client_order_ref,
            'account_state': 'draft',
        })
        return new_order

    @api.multi
    def print_quotation(self):
        """ This function prints the sales order and mark it as sent
            so that we can see more easily the next step of the workflow
        """
        self.ensure_one()

        self.printed = self.printed + 1
        if self.account_state in ('draft', ):
            self.write({
                'account_state': 'sent',  # Mark as sent or printed
            })
        datas = {
            'model': 'sale.order',
            'ids': self,
        }
        only_this_block = self.env.context.get('only_this_block')
        if only_this_block:
            datas['only_this_block'] = only_this_block

        return self.env.ref(
            'sale_order_block.action_report_sale_block_lang').report_action(
                [self.id], data=datas)

    # Fields function:
    @api.multi
    def _function_get_total_block(self):
        """ Fields function for calculate
        """
        for order in self:
            total = 0.0
            for block in order.block_ids:
                total += block.total or block.real_total  # price_subtotal
            order.real_total = total

    # Onchange method:
    @api.onchange('this_map_code')
    def onchange_this_map_code(self):
        """ Always upper
        """
        self.this_map_code = (self.this_map_code or '').upper()

    # Columns:
    hide_link = fields.Boolean(
        string='Hide link',
        help='Hide product link in report'
    )
    this_block_id = fields.Many2one(
        comodel_name='sale.order.block.group',
        string='This block',
        help='Used as default for lines',
        domain="[('order_id', '=', active_id)]",
    )
    this_map_code = fields.Char(
        string='This map code',
        help='Used as default for line',
    )

    client_order_ref = fields.Char(
        string='Client order ref')
    printed = fields.Integer(
        string='Printed', default=1, help='Printed version')
    show_master_total = fields.Boolean(
        'Show master total', default=True)
    block_ids = fields.One2many(
        'sale.order.block.group', 'order_id', 'Block')

    real_total = fields.Float(
        'Real total',
        store=False,
        compute='_function_get_total_block',
        help='Total sum of sale line in this block')
    report_text_ids = fields.One2many(
        comodel_name='sale.order.text.rel',
        inverse_name='order_id',
        string='Report text',
        help='Extra document add after report text',
    )


class SaleOrderLine(models.Model):
    """ Model name: Sale Order Line
    """
    _inherit = 'sale.order.line'
    _order = 'block_id, map_code, id'  # sequence,

    # Onchange method:
    @api.onchange('map_code')
    def onchange_line_this_map_code(self):
        """ Always upper
        """
        self.map_code = (self.map_code or '').upper()

    @api.onchange('prefilter')
    def onchange_domain_filter_default_code(self):
        """ Prefilter search
        """
        if self.prefilter:
            domain = [
                ('default_code', '=ilike', '%s%%' % self.prefilter)]
            product_ids = self.env['product.product'].search(domain)
            if len(product_ids) == 1:
                self.product_id = product_ids[0].id
                return True
        else:
            domain = []
        return {'domain': {'product_id': domain}}

    # -------------------------------------------------------------------------
    # Columns:
    # -------------------------------------------------------------------------
    map_code = fields.Char('Map code', size=15)
    prefilter = fields.Char(string='Prefiltro', size=25)

    # Override:
    order_id = fields.Many2one(
        comodel_name='sale.order',
        string='Sale order',
        required=False,  # Not mandatory (for moved lines)
        ondelete='cascade',
    )
    unused_order_id = fields.Many2one(
        comodel_name='sale.order',
        string='Unused order',
        ondelete='cascade',
    )
    block_id = fields.Many2one(
        'sale.order.block.group',
        'Block',
        ondelete='set null',
        required=True,
    )

    # Parameter for line:
    hide_block = fields.Boolean(
        'Hide block',
        related='block_id.hide_block',
        help='Hide in report for simulation')
    not_confirmed = fields.Boolean(
        'Not confirmed',
        related='block_id.not_confirmed',
        help='Removed from order')


class SaleOrderBlockGroupRelation(models.Model):
    """ Model name: Sale Order Block Group
    """

    _inherit = 'sale.order.block.group'

    # Columns:
    line_ids = fields.One2many(
        'sale.order.line', 'block_id', 'Sale order line')


class SaleOrderRelation(models.Model):
    """ Model name: Sale Order
    """
    _inherit = 'sale.order'

    unused_order_line_ids = fields.One2many(
        comodel_name='sale.order.line',
        inverse_name='unused_order_id',
        string='Unused order line')

    account_state = fields.Selection(
        string='Account state',
        track_visibility=True,
        selection=[
            ('draft', 'Quotation'),
            ('sent', 'Sent (or printed)'),
            ('confirmed', 'Confirmed'),
            ('imported', 'Imported'),
            ('cancel', 'Cancel'),
            ], required=True, default='draft')
