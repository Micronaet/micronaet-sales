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
import xlrd
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

#file_in = './data/fopenerp.ARC'
file_in = './data/copenerp.ARC'
supplier = False
customer = True

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
        print 'Cannot convert: %s' % value
        return 0.0

# -----------------------------------------------------------------------------
# Connect to ODOO:
# -----------------------------------------------------------------------------
odoo = erppeek.Client(
    'http://%s:%s' % (server, port), 
    db=dbname, user=user, password=pwd,
    )
    
# Pool used:
partner_pool = odoo.model('res.partner')

# -----------------------------------------------------------------------------
# Load origin name from XLS
# -----------------------------------------------------------------------------
cols = i = 0
import pdb; pdb.set_trace()
for line in open(file_in):
    i += 1
    line = line.strip()
    row = line.split(';')
    if not cols:
        cols = len(row)
    if len(row) != cols:
        print '%s. Different col number!' % i
        continue

    ref = clean_field(row[0])
    lastname = clean_field(row[1])
    firstname = clean_field(row[2])
    name = (lastname + ' ' + firstname).strip()
    street = clean_field(row[3].strip())
    zip_number = clean_field(row[4])
    city = clean_field(row[5])
    province = clean_field(row[6])
    if province:
        city += ' (%s)' % province
    phone = clean_field(row[7])    
    fax = clean_field(row[8])    
    email = clean_field(row[9])
    fiscalcode = clean_field(row[10])
    vat = clean_field(row[11])
    private = 'S' == clean_field(row[12])
    country_code = clean_field(row[13])
    agent_code = clean_field(row[15])
    agent_name = clean_field(row[16])
    
    data = {
        'is_company': True,
        'supplier': supplier,
        'customer': customer,
        'ref': ref,
        'name': name,
        'street': street,
        'zip': zip_number,
        'city': city,
        'phone': phone,
        #'fax': fax,
        'email': email,
        'vat': vat,        
        }
    
    partner_ids = partner_pool.search([
        ('ref', '=', ref)])
    if partner_ids:
        partner_pool.write(partner_ids, data)
        print '%s. Updated %s' % (i, ref)
    else:
        try:
            partner_pool.create(data)    
            print '%s. Created %s' % (i, ref)
        except:    
            print '%s. Error creating %s' % (i, ref)

