#!/usr/bin/python
# -*- coding: utf-8 -*-
###############################################################################
#
# ODOO (ex OpenERP)
# Open Source Management Solution
# Copyright (C) 2001-2015 Micronaet S.r.l. (<https://micronaet.com>)
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
import pdb
import sys
import logging
from odoo import api, fields, models, tools, exceptions, SUPERUSER_ID
from odoo.addons import decimal_precision as dp
from odoo.tools.translate import _
import base64
import xlrd


_logger = logging.getLogger(__name__)


class ExcelPricelistExtractProductWizard(models.TransientModel):
    _name = 'excel.pricelist.extract.product.wizard'
    _description = 'Extract manual product'

    # -------------------------------------------------------------------------
    #                               BUTTON EVENT:
    # -------------------------------------------------------------------------
    # Import phase:
    # -------------------------------------------------------------------------
    # Workflow confirmed to pending (or ready if all line are ready)
    # -------------------------------------------------------------------------
    @api.multi
    def import_pending_deletion(self):
        """ Import sale order line selected where q. is present
        """
        product_pool = self.env['product.product']

        # ---------------------------------------------------------------------
        # Save passed file:
        # ---------------------------------------------------------------------
        b64_file = base64.decodebytes(self.file)
        now = ('%s' % fields.Datetime.now())[:19]
        filename = '/tmp/sale_%s.xlsx' % \
                   now.replace(':', '_').replace('-', '_')
        f = open(filename, 'wb')
        f.write(b64_file)
        f.close()

        # ---------------------------------------------------------------------
        # Open Excel file:
        # ---------------------------------------------------------------------
        try:
            wb = xlrd.open_workbook(filename)
        except:
            raise exceptions.Warning(_('Cannot read XLS file'))

        ws = wb.sheet_by_index(0)

        # Check sheet mode:
        sheet_mode = ws.cell_value(0, 0)
        if sheet_mode != 'pricelist_manual_product':
            raise exceptions.Warning(
                'File di Excel non corretto, non è quello per la procedura di pulizia')

        start_import = False
        delete_ids = []
        for row in range(ws.nrows):
            line_ref = ws.cell_value(row, 0)
            if not start_import and line_ref == 'ID':
                start_import = True
                _logger.info('%s. Header line' % row)
                continue
            if not start_import:
                _logger.info('%s. Jump line' % row)
                continue

            # Extract needed data:
            product_id = ws.cell_value(row, 0)
            delete_code = ws.cell_value(row, 1)
            if not product_id or not delete_code or delete_code not in 'xXsS':
                continue  # Jump line not to be deleted

            # Hide not delete:
            product_id = int(product_id)
            delete_ids.append(product_id)

        delete_product = product_pool.browse(delete_ids)
        _logger.info('Deleted #%s product' % len(delete_ids))
        return delete_product.write({
            'active': False,
            'sale_ok': False,
            'purchase_ok': False,
        })

    # Extract phase:
    @api.multi
    def excel_extract(self):
        """ Extract excel movement for selected order
        """
        report_pool = self.env['excel.report']
        product_pool = self.env['product.product']
        line_pool = self.env['sale.order.line']
        user_pool = self.env['res.users']

        # Preload sold product:
        lines = line_pool.search([])
        sold_product = [line.product_id for line in lines]

        # Preload User
        creators = {}
        for user in user_pool.search([]):
            creators[user.id] = user.name

        # Domain generation:
        domain = [
            ('excel_pricelist_id', '=', False),
            ('type', '!=', 'service'),
        ]

        if self.start_code:
            domain.append(
                ('default_code', '=ilike', '%s%%' % self.start_code))

        # ---------------------------------------------------------------------
        #                       Excel Extract:
        # ---------------------------------------------------------------------
        ws_name = 'Prodotti manuali'
        report_pool.create_worksheet(ws_name, format_code='DEFAULT')

        # ---------------------------------------------------------------------
        # Setup page:
        # ---------------------------------------------------------------------
        report_pool.column_width(ws_name, [
            1, 8, 18, 18, 40, 8, 5, 15, 20, 50,
            ])
        report_pool.column_hidden(ws_name, [0])
        # ---------------------------------------------------------------------
        # Extra data:
        # ---------------------------------------------------------------------
        row = 0
        report_pool.write_xls_line(ws_name, row, [
            'pricelist_manual_product', 'Filtro = Stato prodotto manuali (non servizio), inizio codice: "%s"' % (
                self.start_code or '',
                )], style_code='title')

        row += 1
        report_pool.write_xls_line(ws_name, row, [
             'ID', 'Rimuovi', 'Codice', 'Codice reale', 'Nome', 'UM', 'Usato', 'Creazione', 'Utente', 'Note'
             ], style_code='header')

        # ---------------------------------------------------------------------
        # Read data
        # ---------------------------------------------------------------------
        products = product_pool.search(domain)
        total = len(products)
        _logger.warning('Report status filter with: %s [Tot. %s]' % (
            domain, total))
        for product in products:  # TODO sort?
            row += 1
            if not (row % 50):
                _logger.warning('Export %s of %s' % (row, total))
            if product in sold_product:
                used = 'X'
                product_id = ''
                delete = ''
            else:
                used = ''
                product_id = product.id
                delete = 'X'

            if product.real_code:
                note = 'Prodotto residuo da eliminazione listino'
            else:
                note = ''
            report_pool.write_xls_line(ws_name, row, [
                # description
                product_id,
                delete,
                product.default_code,
                product.real_code,
                product.name,
                product.uom_id.name,
                used,
                product.create_date,
                product.create_uid.name,
                note,
                ], style_code='text')

        # ---------------------------------------------------------------------
        # Save file:
        # ---------------------------------------------------------------------
        return report_pool.return_attachment('Stato_prodotti_non_usati')

    # -------------------------------------------------------------------------
    #                             COLUMNS DATA:
    # -------------------------------------------------------------------------
    start_code = fields.Char(
        string='Inizio codice')
    file = fields.Binary(
        'XLSX file', filters=None,
        help='Importa il file con le selezioni da eliminare')
