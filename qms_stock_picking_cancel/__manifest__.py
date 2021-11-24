{
    'name': 'Stock Picking Cancel',
    'version': '11.0.0.1',
    'category': 'Warehouse',
    'sequence': 1,
    'summary': 'Cancel Done Picking or cancel done stock move',
    'description': """
        This module helps in reset stock move or cancel stock move or cancel stock picking.
        cancel Delivery order or cancel Receipt. Delivery order cancel / reverse .
        cancel done delivery order. 
        This module helps to reverse the done picking, allow to cancel picking and 
        set it to draft stage.
    """,
    'depends': ['stock'],
    'data': [
        'security/security_view.xml',
        'security/ir.model.access.csv',
        'wizard/cancel_move_wizard_view.xml',
        'views/stock_view.xml'
    ],
    'images': ['static/description/icon.png'],
    'price': 29.00,
    'currency': 'EUR',
    'license': 'OPL-1',
    'installable': True,
    'application': True,
}
