# -*- coding: utf-8 -*-

{
    'name': 'Remove Expired Lots',
    'version': '1.0',
    'summary': '',
    'sequence': 1,
    'description': """Remove Expired Lots""",
    'license': 'AGPL-3',
    'category': 'Inventory',
    'depends': ['stock'],
    'data': [
        'views/stock_view.xml',
    ],
    'demo': [],
    'qweb': [],
    'installable': True,
    'application': True,
    'auto_install': False,
}
