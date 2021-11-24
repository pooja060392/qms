# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Qms Partial Production',
    'version': '12.0.0.1',
    'author': 'Geo Technosoft',
    'category': 'Manufacturing',
    'sequence': 5,
    'license': 'LGPL-3',
    'depends': ['base', 'mrp', 'stock'],
    'description': """
         This module allow partial production
    """,
    'data': [
        'security/ir.model.access.csv',
        # 'wizard/mrp_produce_produce_view.xml',
        # 'views/mrp_production_view.xml',
        'views/mrp_workorder_view.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': True
}
