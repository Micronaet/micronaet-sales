# Copyright 2019  Micronaet SRL (<https://micronaet.com>).
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

{
    'name': 'Sale order in block',
    'version': '11.0.2.0.0',
    'category': 'Sales',
    'description': """
        Manage report block for sales
        """,
    'summary': 'Sale, Block, report',
    'author': 'Micronaet S.r.l. - Nicola Riolini',
    'website': 'http://www.micronaet.it',
    'license': 'AGPL-3',
    'depends': [
        'sale',
        'account',
        'product',
        'sale_management',
        'web',
    ],
    'data': [
        'security/sales_group.xml',
        'security/ir.model.access.csv',

        'views/block_view.xml',
        'views/discount_view.xml',
        'report/sales_report.xml',
    ],
    'external_dependencies': {
        # TODO python-slugify
    },
    'application': False,
    'installable': True,
    'auto_install': False,
}
