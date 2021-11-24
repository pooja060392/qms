# -*- coding: utf-8 -*-

{
    'name': 'Display Partner Address',
    'version': '1.0',
    'summary': 'Display Partner Address in invoice and delivery tab',
    'sequence': 1,
    'description': """
        Display Partner Address
        * Manage the partner contacts address type.
          - Shipping Address and  Invoice Address in new tab.
    """,

    'license': 'AGPL-3',
    'category': 'Partner',
    'depends': ['contacts', 'qms_contact'],
    'data': [
        'views/res_partner_view.xml',
    ],
    'demo': [],
    'qweb': [],
    'installable': True,
    'application': True,
    'auto_install': False,
}