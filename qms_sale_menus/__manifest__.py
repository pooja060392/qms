# -*- coding: utf-8 -*-

{
    'name': 'GTS Sale Menu',
    'version': '1.0',
    'summary': '',
    'sequence': 1,
    'description': """GTS Sale Menu""",
    'license': 'AGPL-3',
    'category': 'Sales Management',
    'depends': ['sale', 'qms_sale_orders'],
    'data': [
        'views/sale_action_view.xml',
        'views/sale_menu_view.xml',
    ],
    'demo': [],
    'qweb': [],
    'installable': True,
    'application': True,
    'auto_install': False,
}
