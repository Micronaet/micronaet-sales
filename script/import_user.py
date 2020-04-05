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
import random
import string


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

file_in = './data/utenti.txt'

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
users_pool = odoo.model('res.users')

# -----------------------------------------------------------------------------
# Load origin name from XLS
# -----------------------------------------------------------------------------
cols = i = 0

def get_password(length=12):
    """ Generate a random string of fixed length 
    """
    letters = 'QWERTYUIOPASDFGHJKLZXCVBNMqwertyuiopasdfghjklzxcvbnm1234567890_-.,[]()='
    return ''.join(random.choice(letters) for i in range(length))

user_list = []
for line in open(file_in):
    i += 1
    line = line.strip()
    row = line.split('|')
    if not cols:
        cols = len(row)
    if len(row) != cols:
        print '%s. Different col number!' % i
        continue

    lastname = clean_field(row[0])
    firstname = clean_field(row[1])
    name = (lastname + ' ' + firstname).strip()
    login = (lastname + '.' + firstname).replace(' ', '').lower()
    password = get_password()
    
    data = {
        'name': name,
        'login': login,
        'password': password,
        }
    
    users_ids = users_pool.search([
        ('login', 'ilike', login)])
    if users_ids:
        users_pool.write(users_ids, data)
        print '%s. Updated %s' % (i, login)
    else:
        try:
            users_pool.create(data)    
            print '%s. Created %s' % (i, login)
        except:    
            print '%s. Error creating %s' % (i, login)
    user_list.append((name, login, password))
for record in user_list:
    print '%s|%s|%s' % record    
