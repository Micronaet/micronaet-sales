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
        records = request.env['sale.order'].sudo().search([
            # ('account_state', '=', 'confirmed')
            ])
        return records.read(['name', 'validity_date'])

