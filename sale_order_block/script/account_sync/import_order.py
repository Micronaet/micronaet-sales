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
def get_block_margin(block, history):
    """ Get block margin
    """
    if not block:
       return 1.0
    if block not in history:        
        current_total = block.current_total  # sum of subtotal
        if not current_total:
            history[block] = 1.0  # as is
        else:    
            # Forced or calculated
            history[block] = (block.total or block.real_total) / current_total
    return history[block]
        
        
def trim_text(value, limit):
    """ Trim text for max value passes
    """
    value = (value or '').strip()
    return value[:limit]


def account_date(value):
    """ Format date for account program
    """
    if not value:
        return ''
    date = ('%s' % value)[:10]
    return '%s%s%s' % (
        date[:4],
        date[5:7],
        date[8:10],
    )

def clean_text(data):
    res = ''
    for c in data:
        if c in '\r\n\t':
            res += ' '
        elif ord(c) < 127:
            res += c
        else:  # replaced char
            res += '.'
    return res        

# -----------------------------------------------------------------------------
#                               Start procedure:
# -----------------------------------------------------------------------------
history = {}  # Block margin history
odoo = odoorpc.ODOO(server, port=port)
odoo.login(database, user, password)

# Pool used:
order_pool = odoo.env['sale.order']
partner_pool = odoo.env['res.partner']

order_ids = order_pool.search([('account_state', '=', 'confirmed')])
print('Trovati %s ordini confermati in importazione...' % len(order_ids))
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
    row = 0
    for line in order.order_line:
        row += 1
        block = line.block_id
        margin = get_block_margin(block, history)
        product = line.product_id
        try:
            vat_code = line.tax_id[0].account_ref or ''
        except:
            vat_code = False
        default_code = product.default_code
        if not default_code:
            default_code = '#%s' % product.id
        detail = '%s%-24s%-40s%-3s%-40s%15.2f%15.2f%-30s%-4s\r' % (
            header,
            trim_text(clean_text(default_code), 24),
            trim_text(clean_text(product.name), 40),
            product.uom_id.account_ref or '',
            trim_text(clean_text(line.name), 40),
            line.product_uom_qty,
            line.price_unit * margin,
            line.discount,  # Scale!!
            vat_code,
        )
        try:
            account_file.write(detail)
            account_file.flush()
            print 'Riga esportata: %s' % row    
        except:
            print 'Errore esportando riga: %s' % row
    account_file.close()

    # -------------------------------------------------------------------------
    # Launch Account import:
    # -------------------------------------------------------------------------
    #os.system(command)
    wait = raw_input('''
        Preparato ordine: %s, lanciare l'importazione da Mexal... 
        (premere INVIO quando finito)
        ''' % order.name)

    # -------------------------------------------------------------------------
    # Read result and udpate partner:
    # -------------------------------------------------------------------------
    account_file = open(file_out, 'r')
    result = account_file.readline()
    account_file.close()
    if result.startswith('OK'):
        if not update_id:
            partner_pool.write([update_id], {
                'ref': result.split(';')[-1].strip(),
            })

        # Update order if OK
        order_pool.write([order.id], {
            'account_state': 'imported',
            })
        print('Importazione %s confermata!' % order.name)
        import pdb; pdb.set_trace()
        os.remove(file_in)
        os.remove(file_out)
    else:
        print('Importazione %s non confermata!' % order.name)

wait = raw_input('Procedura terminata, premere INVIO per chiudere.')
