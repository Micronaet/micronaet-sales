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
import sys
import logging
from odoo import api, fields, models, tools, exceptions, SUPERUSER_ID
from odoo.addons import decimal_precision as dp
from odoo.tools.translate import _


_logger = logging.getLogger(__name__)


class ExcelPricelistExtractProductWizard(models.TransientModel):
    _name = 'excel.pricelist.extract.product.wizard'
    _description = 'Extract manual product'

    # -------------------------------------------------------------------------
    #                               BUTTON EVENT:
    # -------------------------------------------------------------------------
    # Order phase:
    @api.multi
    def excel_extract(self):
        """ Extract excel movement for selected order
        """
        excel_pool = self.env['excel.writer']
        product_pool = self.env['product.product']
        line_pool = self.env['sale.order.line']

        # Domain generation:
        domain = [
            ('excel_pricelist_id', '=', False),
            ('type', '!=', 'service'),
        ]

        if self.start_code:
            domain.append(
                ('default_code', '%ilike', '%s%%' % self.start_code))

        # ---------------------------------------------------------------------
        #                       Excel Extract:
        # ---------------------------------------------------------------------
        ws_name = 'Prodotti manuali'
        excel_pool.create_worksheet(ws_name)

        # ---------------------------------------------------------------------
        # Format:
        # ---------------------------------------------------------------------
        excel_pool.set_format()
        f_title = excel_pool.get_format('title')
        f_header = excel_pool.get_format('header')

        f_white_text = excel_pool.get_format('text')
        # f_green_text = excel_pool.get_format('bg_green')
        # f_yellow_text = excel_pool.get_format('bg_yellow')

        f_white_number = excel_pool.get_format('number')
        # f_green_number = excel_pool.get_format('bg_green_number')
        # f_yellow_number = excel_pool.get_format('bg_yellow_number')

        # ---------------------------------------------------------------------
        # Setup page:
        # ---------------------------------------------------------------------
        excel_pool.column_width(ws_name, [
            20, 15, 25, 2, 2, 20, 10,
            8, 8, 8, 8, 8, 8, 8, 8,
            20, 20,
            ])

        # ---------------------------------------------------------------------
        # Extra data:
        # ---------------------------------------------------------------------
        now = fields.Datetime.now()

        row = 0
        excel_pool.write_xls_line(ws_name, row, [
            'Filtro = Stato prodotto manuali (non servizio), inizio codice: "%s"' % (
                self.start_code or '',
                )], default_format=f_title)

        row += 1
        excel_pool.write_xls_line(ws_name, row, [
             'Codice', 'Codice reale', 'Nome', 'UM', 'Usato',
             ], default_format=f_header)

        # ---------------------------------------------------------------------
        # Read data
        # ---------------------------------------------------------------------
        products = product_pool.search(domain)
        _logger.warning('Report status filter with: %s [Tot. %s]' % (
            domain, len(products)))
        for product in products:  # TODO sort?
            row += 1

            'Codice', 'Codice reale', 'Nome', 'UM', 'Usato',

            excel_pool.write_xls_line(ws_name, row, [
                # description
                product.default_code,
                product.real_code,
                product.name,
                product.uom_id.name,
                '',  # TODO check in order
                ], default_format=f_white_text)

        # ---------------------------------------------------------------------
        # Save file:
        # ---------------------------------------------------------------------
        return excel_pool.return_attachment('Stato_prodotti_non_usati')

    # -------------------------------------------------------------------------
    #                             COLUMNS DATA:
    # -------------------------------------------------------------------------
    start_code = fields.Char(
        string='Inizio codice')

