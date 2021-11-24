# -*- coding: utf-8 -*-

{
    'name': 'Inventory Menu',
    'version': '1.0',
    'summary': '',
    'sequence': 1,
    'description': """Inventory Menu""",
    'license': 'AGPL-3',
    'category': 'Inventory',
    'depends': ['stock', 'qms_inventory'],
    'data': [
        'views/stock_actions.xml',
        'views/stock_menu_view.xml',
    ],
    'demo': [],
    'qweb': [],
    'installable': True,
    'application': True,
    'auto_install': False,
}
