# Copyright 2019  Micronaet SRL (<https://micronaet.com>).
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

{
    'name': 'Minimal sale block menu',
    'version': '11.0.2.0.0',
    'category': 'Sales',
    'description': """
        Manage report block for sales
        """,
    'summary': 'Sale, Block, menu',
    'author': 'Micronaet S.r.l. - Nicola Riolini',
    'website': 'http://www.micronaet.it',
    'license': 'AGPL-3',
    'depends': [
        'sale',
        'sale_management',
        'sale_order_block',
        'web',
    ],
    'data': [
        'views/menu_view.xml',
    ],
    'external_dependencies': {},
    'application': False,
    'installable': True,
    'auto_install': False,
}
