{
    'name': 'Procurement',
    'version': '11.0.0.1',
    'category': 'Purchase',
    'sequence': 75,
    'summary': 'Procurement related report and notification',
    'description': "Procurement related report and notification ",
    'depends': ['purchase', 'sale'],
    'data': [
        'views/product_view.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}