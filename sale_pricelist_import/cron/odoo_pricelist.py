# -*- coding: utf-8 -*-
###############################################################################
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
import odoorpc
import ConfigParser

# -----------------------------------------------------------------------------
# Read configuration parameter:
# -----------------------------------------------------------------------------
# From config file:
cfg_file = os.path.expanduser('./local.cfg')
pid_file = '/tmp/odoo_pricelist.pid'

pid = str(os.getpid())
if os.path.isfile(pid_file):
    print("%s already exists, exiting" % pid_file)
    sys.exit()

# Write PID File:
f_pid = open(pid_file, 'w')
f_pid.write(pid)
f_pid.close()

# -----------------------------------------------------------------------------
# PID Block:
try:
    import_block = 50

    config = ConfigParser.ConfigParser()
    config.read([cfg_file])
    dbname = config.get('dbaccess', 'dbname')
    user = config.get('dbaccess', 'user')
    pwd = config.get('dbaccess', 'pwd')
    server = config.get('dbaccess', 'server')
    port = config.get('dbaccess', 'port')  # verify if it's necessary: getint

    # -------------------------------------------------------------------------
    # Connect to ODOO:
    # -------------------------------------------------------------------------
    odoo = odoorpc.ODOO(server, port=port)
    odoo.login(dbname, user, pwd)

    # Pool used:
    pricelist_pool = odoo.env['excel.pricelist.item']

    pricelist_ids = pricelist_pool.search([('state', '=', 'scheduled')])
    for pricelist_id in pricelist_ids:
        block = 0
        while not pricelist_pool.etl_available_pricelist_form_file(
                pricelist_id, import_block):
            print('Blocco %s da %s' % (
                block,
                import_block,
            ))
            block += 1

# -----------------------------------------------------------------------------

finally:
    os.unlink(pid_file)
