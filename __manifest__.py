{
    'name': 'Universal SMS Connector (Multi-Provider)',
    'version': '18.0.1.0.0',
    'category': 'Tools/SMS',
    'summary': 'Multi-provider SMS Gateway (Boomcast, MiMSMS, AWS SNS)',
    'author': 'Torab Ramin',
    'license': 'LGPL-3',
    'depends': ['base', 'mail', 'phone_validation', 'sms', 'iap'],
    'external_dependencies': {'python': ['boto3']}, # For AWS
    'data': [
        'security/ir.model.access.csv',
        'data/ir_cron_data.xml',
        'views/sms_provider_views.xml',
        'views/sms_log_views.xml',
        'views/sms_compose_views.xml',
        'views/menus.xml',
    ],
    'installable': True,
    'application': True,
}