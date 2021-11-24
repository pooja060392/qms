{
    'name' : 'CRM Linking',
    'version' : '1.0',
    'summary': '',
    'description': """
    """,
    'category': 'CRM',
    'website': '',
    'depends' : ['crm', 'sale_crm'],
    'data': [
        'views/config_view.xml',
        'views/crm_lead_view.xml',
        'views/account_view.xml',
        'views/stock_picking_view.xml',
        'views/sale_order_view.xml',
    ],
    'installable': True,
    'application': True,
}
