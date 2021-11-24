{
    'name': 'CRM',
    'version': '1.0',
    'category': '',
    'sequence': 75,
    'summary': 'CRM',
    'description': "",
    'depends': ['base', 'crm', 'sale', 'sale_crm', 'calendar'],
    'data': [
        'security/security_view.xml',
        'wizard/request_material_view.xml',
        'views/crm_lead.xml'
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
