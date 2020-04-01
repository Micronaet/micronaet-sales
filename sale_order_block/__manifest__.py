# Copyright 2019  Micronaet SRL (<https://micronaet.com>).
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

{
    'name': 'Sale order in block',
    'version': '11.0.2.0.0',
    'category': 'Sales',
    'description': '''
        Manage report block for sales
        ''',
    'summary': 'Sale, Block, report',
    'author': 'Micronaet S.r.l. - Nicola Riolini',
    'website': 'http://www.micronaet.it',
    'license': 'AGPL-3',
    'depends': [
        'sales',
        'web',
    ],
    'data': [
        # 'security/ir.model.access.csv',
        # 'views/excel_report_view.xml',
    ],
    'external_dependencies': {},
    'application': False,
    'installable': True,
    'auto_install': False,
}
