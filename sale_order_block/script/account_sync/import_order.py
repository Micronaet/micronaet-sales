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

import erppeek
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
    value = value.strip()
    return value[:limit]


def account_date(value):
    """ Format date for account program
    """
    if not date:
        ''
    return '%s%s%s' % (
        value[:4],
        value[5:7],
        value[8:10],
    )


# -----------------------------------------------------------------------------
#                               Start procedure:
# -----------------------------------------------------------------------------
odoo = erppeek.Client(
    'http://%s:%s' % (server, port),
    db=database,
    user=user,
    password=password
    )

# Pool used:
order_pool = odoo.model('sale.order')

order_ids = order_pool.search([('account_state', '=', 'confirmed')])
print('Sale order confirmed, total %s' % len(order_ids))

for order in order_pool.browse(order_ids):
    account_file = open(file_in, 'w')
    partner = order.partner_id

    # Header: Partner
    header = '%-9s|%-40s|%1s|%-40s|%-40s|%-5s|%-40s|%-20s|%-60s|%-60s|' \
             '%-15s' % (
                 partner.ref,
                 trim_text(partner.name, 40),
                 'C' if partner.is_company else 'P',
                 trim_text('%s %s' % (partner.street, partner.street2), 40),
                 trim_text(partner.city, 40),
                 partner.zip or '',
                 trim_text(
                    partner.country_id.name if partner.country_id else ''),
                 trim_text(partner.phone, 20),
                 trim_text(partner.email, 60),
                 trim_text(partner.website, 60),
                 partner.vat,
    )

    # Header Order:
    header += '|%-15s|%-8s|%-8s|%-9s|%-9s' % (
        # Order:
        order.name,
        account_date(order.date_order),
        account_date(order.validity_date),
        order.payment_term_id.account_ref or '',
        order.user_id.account_ref or '',
    )

    # Export line:
    for line in order.order_line:
        product = line.product_id
        detail = '%s|%18s|%40s|%3s|%40s|%15.2f|%15.2f|%30s\r\n' % (
            header,
            trim_text(product.default_code, 18),
            trim_text(product.name, 40),
            '',  # UOM product.uom_id.account_ref,
            trim_text(line.name, 40),
            line.product_uom_qty,
            line.price_unit,
            line.discount,  # Scale!!
        )

