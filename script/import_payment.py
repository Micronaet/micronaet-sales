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
import sys
import erppeek
import ConfigParser


# -----------------------------------------------------------------------------
# Read configuration parameter:
# -----------------------------------------------------------------------------
# From config file:
cfg_file = os.path.expanduser('./openerp.cfg')

config = ConfigParser.ConfigParser()
config.read([cfg_file])
dbname = config.get('dbaccess', 'dbname')
user = config.get('dbaccess', 'user')
pwd = config.get('dbaccess', 'pwd')
server = config.get('dbaccess', 'server')
port = config.get('dbaccess', 'port')   # verify if it's necessary: getint

# -----------------------------------------------------------------------------
# Connect to ODOO:
# -----------------------------------------------------------------------------
odoo = erppeek.Client(
    'http://%s:%s' % (server, port), 
    db=dbname, user=user, password=pwd,
    )
    
# Pool used:
payment_pool = odoo.model('account.payment.term') 

data = {
    '2': 'RIMESSA DIRETTA',
    '3': 'RIMESSA DIRETTA 30 GGDFFM+15 GG',
    '4': 'bb: 20% all\'ordine, saldo a merce pronta',
    '5': 'CONTRASSEGNO ASSEGNO CIRCOLARE',
    '6': 'CONTRASSEGNO ASSEGNO BANCARIO',
    '7': 'Ricevuta Bancaria 30gg Fine Mese',
    '8': 'Ricevuta Bancaria 60gg Fine Mese',
    '9': 'Ricevuta Bancaria 90gg Fine Mese',
    '10': 'Ricevuta Bancaria 120gg FM',
    '11': 'Ricevuta Bancaria 30/60gg Fine Mese',
    '12': 'Ricevuta Bancaria 30/60/90gg Fine Mese',
    '13': 'Ricevuta Bancaria 60/90gg Fine Mese',
    '14': 'Ricevuta Bancaria 60/90/120gg Fine Mese',
    '15': 'Ricevuta Bancaria 90gg al 10 MS',
    '17': 'Ricevuta Bancaria 60gg Fine Mese +10MS',
    '18': 'RI.BA 90/120',
    '19': 'Bonifico Bancario 30gg FM +15gg',
    '20': 'Bonifico Bancario all\'ordine',
    '21': 'Bonifico Bancario ad emissione fattura',
    '22': 'Bonifico Bancario ad avviso merce pronta',
    '23': 'BB: 30% all\'ordine, saldo a merce pronta',
    '24': 'Bonifico Bancario 30GG FM',
    '25': 'Bonifico Bancario',
    '26': 'Acconto BB 30% saldo BB 30GG FM',
    '27': 'BB: 50% alla conferma saldo a consegna',
    '28': 'Bonifico Bancario 90GG DF',
    '30': 'Da Concordare all\'ordine',
    '33': 'Acconto 20% saldo Ri.Ba. 30gg',
    '34': 'Acconto 20% saldo Ri.Ba. 30/60gg F.M.',
    '35': 'Acconto 20% saldo Ri.Ba. 60/90gg F.M.',
    '37': '30% bb anticipato saldo ri.ba 60 gg',
}

# -----------------------------------------------------------------------------
# Load origin name from XLS
# -----------------------------------------------------------------------------
i = 0
for account_ref in data:
    i += 1
    name = data[account_ref]
    
    data = {
        'account_ref': account_ref,
        'name': name,
        }
    
    payment_ids = product_pool.search([
        ('account_ref', '=', account_ref)])
    if payment_ids:
        product_pool.write(product_ids, data)
    else:
        product_pool.create(data)    

