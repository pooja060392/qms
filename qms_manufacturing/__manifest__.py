{
    'name': 'QMS Manufacturing',
    'version': '1.0',
    'category': '',
    'sequence': 75,
    'summary': 'Manufacturing',
    'description': "",
    'depends': ['base','sale','mrp'],
    'data': [
        'security/ir.model.access.csv',
        # 'wizard/mrp_product_line.xml',
        'views/mrp_production_view.xml',
        'views/sale_order_view.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
