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

file_in = './data/artioerp.txt'
force_start = False

# -----------------------------------------------------------------------------
# Utility:
# -----------------------------------------------------------------------------
def clean_field(value):
    ''' Clean extra space
    '''
    try:
        value = value or ''
        value = value.strip()
        return value
    except: 
        return value    

def clean_float(value):
    ''' Clean and give float
    '''
    value = clean_field(value).replace(',', '.')
    try:
        return float(value)
    except: 
        #print 'Cannot convert: %s' % value
        return 0.0

# -----------------------------------------------------------------------------
# Connect to ODOO:
# -----------------------------------------------------------------------------
odoo = erppeek.Client(
    'http://%s:%s' % (server, port), 
    db=dbname, user=user, password=pwd,
    )
    
# Pool used:
product_pool = odoo.model('product.product') 
#suppinfo_pool = odoo.model('product.supplierinfo') 
#pl_pool = odoo.model('pricelist.partnerinfo') 

#supplier_id =  28297 # XXX CONFEZIONI ELENA DI YE ZHIXIN
uom_id = 1 # NR

# -----------------------------------------------------------------------------
# Load origin name from XLS
# -----------------------------------------------------------------------------
cols = i = 0
for line in open(file_in):
    i += 1
    if force_start and force_start > i:
        print '%s. Jumper forced!' % i
        continue
    line = line.strip()
    row = line.split(';')
    if not cols:
        cols = len(row)
    if len(row) != cols:
        print '%s. Different col number!' % i
        continue
    
    default_code = row[0].strip()
    name = clean_field(row[1])
    uom = clean_field(row[2].strip())
    vat = clean_field(row[3].strip())
    lst_price = clean_float(row[6])
    data = {
        'default_code': default_code,
        'name': name,
        'lst_price': lst_price,
        'uom_id': uom_id,
        #'uos_id': uom_id,
        #'uom_po_id': uom_id
        }
    
    product_ids = product_pool.search([
        ('default_code', '=', default_code)])
    if product_ids:
        try:
            product_pool.write(product_ids, data)
            print '%s. Updated %s' % (i, default_code)
        except:    
            print '%s. Error updating %s' % (i, default_code)
    else:
        try:
            product_pool.create(data)    
            print '%s. Created %s' % (i, default_code)
        except:    
            print '%s. Error creating %s' % (i, default_code)

