# -*- coding: utf-8 -*-
# SilkSoft.org Module.

{
    'name': 'SilkSoft Modification Requests',
    'version': '15.0.1.0.1',
    'category': 'Hidden/Tools',
    'summary': 'Modification Requests for Non Administrative Employees For Odoo 15',
    'sequence': '5',
    'author': 'Amr Salama',
    'license': 'LGPL-3',
    'company': 'SilkSoft',
    'maintainer': 'SilkSoft',
    'support': 'To Be Added',
    'website': 'https://silksoft.org',
    'depends': ['hr_attendance'],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'views/modification_request_views.xml',
        'views/menu_items.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'images': ['static/description/icon.png'],
    'qweb': [],
}
