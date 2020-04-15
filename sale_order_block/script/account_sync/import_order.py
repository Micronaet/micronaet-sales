# -*- coding: utf-8 -*-
###############################################################################
#
# ODOO (ex OpenERP)
# Open Source Management Solution
# Copyright (C) 2001-2015 Micronaet S.r.l. (<http://www.micronaet.it>)
# Developer: Nicola Riolini @thebrush (<https://it.linkedin.com/in/thebrush>)
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################

import os
import odoorpc
import ConfigParser
import sys

# -----------------------------------------------------------------------------
#                             Read Parameters:
# -----------------------------------------------------------------------------
cfg_file = './odoo.cfg'
config = ConfigParser.ConfigParser()
config.read(cfg_file)

# General parameters:
server = config.get('odoo', 'server')
port = eval(config.get('odoo', 'port'))
database = config.get('odoo', 'database')
user = config.get('odoo', 'user')
password = config.get('odoo', 'password')

file_in = config.get('account', 'input')
file_out = config.get('account', 'output')
command = config.get('account', 'command')


# -----------------------------------------------------------------------------
# Utility:
# -----------------------------------------------------------------------------
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


# -----------------------------------------------------------------------------
#                               Start procedure:
# -----------------------------------------------------------------------------
odoo = odoorpc.ODOO(server, port=port)
odoo.login(database, user, password)

# Pool used:
order_pool = odoo.env['sale.order']
partner_pool = odoo.env['res.partner']

order_ids = order_pool.search([('account_state', '=', 'confirmed')])
print('Sale order confirmed, total %s' % len(order_ids))
for order in order_pool.browse(order_ids):
    partner = order.partner_id

    # Write file
    account_file = open(file_in, 'w')

    # -------------------------------------------------------------------------
    # Header: Partner
    # -------------------------------------------------------------------------
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

    # -------------------------------------------------------------------------
    # Header Order:
    # -------------------------------------------------------------------------
    header += '%-15s%-8s%-8s%-9s%-9s' % (
        # Order:
        trim_text(order.name or '', 15),
        account_date(order.date_order),
        account_date(order.validity_date),
        order.payment_term_id.account_ref or '',
        order.user_id.account_ref or '',
    )

    # -------------------------------------------------------------------------
    # Export line:
    # -------------------------------------------------------------------------
    for line in order.order_line:
        product = line.product_id
        try:
            vat_code = line.tax_id[0].account_ref or ''
        except:
            vat_code = False
        detail = '%s%-24s%-40s%-3s%-40s%15.2f%15.2f%-30s%-4s\r\n' % (
            header,
            trim_text(product.default_code, 24),
            trim_text(product.name, 40),
            product.uom_id.account_ref or '',
            trim_text(line.name, 40),
            line.product_uom_qty,
            line.price_unit,
            line.discount,  # Scale!!
            vat_code,
        )
        account_file.write(detail)
    account_file.close()

    # -------------------------------------------------------------------------
    # Launch Account import:
    # -------------------------------------------------------------------------
    os.system(command)

    # -------------------------------------------------------------------------
    # Read result and udpate partner:
    # -------------------------------------------------------------------------
    account_file = open(file_out, 'r')
    result = account_file.readline()
    if result.startswith('OK'):
        if not update_id:
            partner_pool.write([update_id], {
                'ref': result.split(';')[-1].strip(),
            })

        # Update order if OK
        order_pool.write([order.id], {
            'account_state': 'imported',
            })
        print('Imported %s order' % order.name)
        # TODO os.remove(file_in)
        # TODO os.remove(file_out)
    else:
        print('Not imported %s order' % order.name)

    import pdb; pdb.set_trace()
