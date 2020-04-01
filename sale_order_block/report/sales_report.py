# Copyright 2019  Micronaet SRL (<https://micronaet.com>).
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

import os
import sys
import logging
from odoo import fields, api, models
from odoo import tools
from odoo.tools.translate import _

_logger = logging.getLogger(__name__)


class StockPicking(models.AbstractModel):
    ''' Stock picking extract
    '''
    _inherit = 'stock.picking'
    
    @api.multi
    def get_default_folder_path(self):
        '''
        '''
        path = os.path.expanduser('~/Account/DDT')
        os.system('mkdir -p %s' % path)
        return path

    @api.multi
    def get_default_folder_invoice_path(self):
        '''
        '''
        path = os.path.expanduser('~/Account/Invoice')
        os.system('mkdir -p %s' % path)
        return path

    @api.multi
    def extract_account_ddt_report(self):
        ''' Extract PDF report
        '''
        folder = self.get_default_folder_path()
        
        # TODO Sanitize file name:
        filename = (
            self.ddt_number or 'document_no_name').replace('/', '_')
        filename = filename + '.pdf'        
            
        fullname = os.path.join(folder, filename)
        
        REPORT_ID = 'logistic_account_report.action_report_ddt_lang'        
        pdf = self.env.ref(REPORT_ID).render_qweb_pdf(self.ids)
        f_pdf = open(fullname, 'wb')
        f_pdf.write(pdf[0])
        f_pdf.close()
        _logger.info('Extract DDT: %s' % fullname)
        return fullname

    @api.multi
    def extract_account_invoice_report(self):
        ''' Extract PDF report
        '''
        folder = self.get_default_folder_invoice_path()
        
        # TODO Sanitize file name:
        # Different name from NC and Invoice
        filename = (
            self.invoice_number or 'not_confirmed').replace('/', '_')
        fullname = os.path.join(folder, '%s.pdf' % filename)
        
        REPORT_ID = 'logistic_account_report.action_report_invoice_lang'        
        pdf = self.env.ref(REPORT_ID).render_qweb_pdf(self.ids)
        f_pdf = open(fullname, 'wb')
        f_pdf.write(pdf[0])
        f_pdf.close()
        _logger.info('Extract Invoice: %s' % fullname)
        return fullname

class ResPartner(models.Model):
    ''' Add extra function
    '''
    _inherit = 'res.partner'
    
    @api.multi
    def get_partner_extra_info(self, ):
        ''' Get partner extra info data (for address print)
            self: res.partner obj
        '''
        for o in self:
            if o:
                mask = '%s\n%s%s\n%s - %s (%s)\n%s\nTel.: %s  Mobile: %s\nEmail: %s'
                o.contact_info = mask % (
                    o.name or '',
                    o.street or '',
                    o.street2 or '',
                    o.zip or '', 
                    o.city or '',
                    o.state_id.name if o.state_id else '',
                    o.country_id.name if o.country_id else '',
                    o.phone or '',
                    o.mobile or '',
                    o.email or '',
                    )
            else:    
                o.contact_info = '/'
    
    contact_info = fields.Text('Extra info', compute='get_partner_extra_info')        
    
class ReportDdtLangParser(models.AbstractModel):
    ''' Load move report:
    '''
    _name = 'report.logistic_account_report.report_ddt_lang'
    
    @api.model
    def get_report_values(self, docids, data=None):
    # EX: def render_html(self, docids, data=None):
        ''' Render report parser:
        '''
        return {
            # Standard data:
            'doc_ids': docids,#self.ids,
            'doc_model': 'stock.picking',#picking_pool.model,#holidays_report.model,
            'docs': self.env['stock.picking'].search([('id', 'in', docids)]),
            
            # Extra function:
            #'get_partner_extra_info': self.get_partner_extra_info,
            }
        
        '''picking_pool = self.env['stock.picking']    
        pickings = picking_pool.search([]) # TODO Change filter here
        
        if not pickings.exists():
             raise Warning(
                 _('No movement to print!'))
        
        docids = pickings.ids # list of IDs
        docargs = {
            'doc_ids': docids,
            'doc_model': 'stock.picking',
            'docs': pickings,
            }
        return {
            'doc_ids': docids,#self.ids,
            'doc_model': 'stock.picking',#picking_pool.model,#holidays_report.model,
            'docs': pickings,
            }
        '''

class ReportInvoiceLangParser(models.AbstractModel):
    ''' Load move report:
    '''
    _name = 'report.logistic_account_report.report_invoice_lang'
    
    @api.model
    def get_report_values(self, docids, data=None):
        ''' Render report invoice parser:
        '''
        return {
            'doc_ids': docids,
            'doc_model': 'stock.picking',
            'docs': self.env['stock.picking'].search([('id', 'in', docids)]),
            }
        
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
