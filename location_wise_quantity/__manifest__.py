{
    'name' : 'Product Quantity Information',
    'version' : '1.0',
    'summary': '',
    'description': """
    """,
    'category': 'Sale',
    'website': '',
    'depends' : ['sale', 'stock'],
    'data': [
        'wizard/quantity_wiz_view.xml',
        'views/sale_order_view.xml',
    ],
    'installable': True,
    'application': True,
}
