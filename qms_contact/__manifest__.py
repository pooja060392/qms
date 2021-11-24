# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.


{
    'name': 'Contacts',
    'category': 'Sales/CRM',
    'sequence': 150,
    'summary': 'Centralize your address book',
    'description': """
This module gives you a quick view of your contacts directory, accessible from your home page.
You can track your vendors, customers and other contacts.
""",
    'depends': ['base', 'contacts', 'crm', 'sale'],
    'data': [

        'security/ir.model.access.csv',
        'security/security_view.xml',

        'views/brand_view.xml',
        'views/division_view.xml',
        'views/res_partner_view.xml',
        'views/res_user_view.xml',

        'menu/menu_view.xml'
    ],
    'application': True,
}
