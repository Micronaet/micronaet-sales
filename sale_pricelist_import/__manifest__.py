# Copyright 2019  Micronaet SRL (<https://micronaet.com>).
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

{
    'name': 'Import pricelist',
    'version': '11.0.2.0.0',
    'category': 'Sales',
    'description': """
        Manage pricelist files
        """,
    'summary': 'Sale, Pricelist, Management',
    'author': 'Micronaet S.r.l. - Nicola Riolini',
    'website': 'http://www.micronaet.it',
    'license': 'AGPL-3',
    'depends': [
        'sale',
        'sale_management',
        'web',
        'mail',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/pricelist_view.xml',
        'import_pricelist_scheduler.xml',
    ],
    'external_dependencies': {

    },
    'application': False,
    'installable': True,
    'auto_install': False,
}
