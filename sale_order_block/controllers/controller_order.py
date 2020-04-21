import json

from odoo import http
from odoo.http import request


class SaleOrderController(http.Controller):
    """ Return list of open orders
    """

    @http.route('/edi/get_html_orders', type='http', auth='none')
    def return_html_orders(self):
        """ Return order list confirmed
        """
        records = request.env['sale.order'].sudo().search([
            # ('account_state', '=', 'confirmed')
            ])
        result = '''
            <!DOCTYPE html>
            <html>
                <head>
                    <title>Order pending importation</title>
                </head>
                <body>
                    <table>
                        <tr><td>
                        '''
        result += '</td></tr><td><tr>'.join(records.mapped('name'))
        result += '</td></tr></table></body></html>'
        return result

    @http.route('/edi/get_json_orders', type='json', auth='none')
    def return_json_orders(self):
        """ Return order list confirmed
        """
        def trim_text(value, limit):
            """ Trim text for max value passes
            """
            value = (value or '').strip()
            return value[:limit]

        def account_date(value):
            """ Format date for account program
            """
            date = ('%s' % value)[:10].strip()
            if not date:
                return ''
            return '%s%s%s' % (
                date[:4],
                date[5:7],
                date[8:10],
            )

        payload = {}
        orders = request.env['sale.order'].sudo().search([
            # ('account_state', '=', 'confirmed')
            ])
        for order in orders:
            payload[order.id] = []
            partner = order.partner_id

            # Header: Partner
            if partner.ref:
                update_id = False
            else:
                update_id = partner.id

            header = '%-9s%-40s%1s%-40s%-40s%-5s%-40s%-20s%-60s%-60s%-15s' % (
                partner.ref or '',
                trim_text(partner.name, 40),
                'C' if partner.is_company else 'P',
                trim_text(
                    '%s %s' % (
                        partner.street or '', partner.street2 or ''), 40),
                trim_text(partner.city, 40),
                partner.zip or '',
                trim_text(
                    partner.country_id.name if partner.country_id else '', 40),
                trim_text(partner.phone, 20),
                trim_text(partner.email, 60),
                trim_text(partner.website, 60),
                partner.vat or '',
            )

            # Header Order:
            header += '%-15s%-8s%-8s%-9s%-9s' % ( # Order:
                trim_text(order.name or '', 15),
                account_date(order.date_order),
                account_date(order.validity_date),
                order.payment_term_id.account_ref or '',
                order.user_id.account_ref or '',
            )

            # -----------------------------------------------------------------
            # Export line:
            # -----------------------------------------------------------------
            for line in order.order_line:
                product = line.product_id
                try:
                    vat_code = line.tax_id[0].account_ref or ''
                except:
                    vat_code = False
                default_code = product.default_code
                if not default_code:
                    default_code = '#%s' % product.id
                detail = '%s%-24s%-40s%-3s%-40s%15.2f%15.2f%-30s%-4s\r\n' % (
                    header,
                    trim_text(default_code, 24),
                    trim_text(product.name, 40),
                    product.uom_id.account_ref or '',
                    trim_text(line.name, 40),
                    line.product_uom_qty,
                    line.price_unit,
                    line.discount,  # Scale!!
                    vat_code,
                )
                payload[order.id].append(detail)
        return payload

