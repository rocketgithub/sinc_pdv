# -*- coding: utf-8 -*-
{
    'name': "sinc-pdv",

    'summary': """
        sinc-pdv""",

    'description': """
        sinc-pdv
    """,

    'author': "My Company",
    'website': "http://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/openerp/addons/base/module/module_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','base_setup'],

    'data': [
        'views/base_config_settings_views.xml',
    ],
}