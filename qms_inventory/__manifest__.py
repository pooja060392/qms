{
    'name': 'Stock',
    'version': '1.0',
    'category': '',
    'sequence': 75,
    'summary': 'Stock',
    'description': "",
    'depends': ['stock', 'sale', 'mrp'],
    'data': [
        'security/ir.model.access.csv',
        'wizard/quantity_wiz_view.xml',
        'views/stock_picking_view.xml',
        'views/stock_location_view.xml',
        'views/mrp_view.xml',
        'views/inventory_report.xml',
        'views/purchase_order_view.xml',
        'views/product_product_view.xml',
        'views/stock_picking_type_view.xml',
        'views/labour_view.xml'
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}