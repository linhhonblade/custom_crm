# -*- coding: utf-8 -*-
{
    'name': "custom_crm",

    'summary': """
        Custom module crm for aht""",

    'description': """
        Allow salesperson can search contact to prevent duplicate
    """,

    'author': "linhhonblade",
    'website': "https://github.com/linhhonblade",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/14.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Sales/CRM',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['crm'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/contact_views.xml',
        'views/crm_lead_views.xml',
        'views/res_partner_views.xml',
        'data/custom_crm_data.xml',
        'security/custom_crm_security.xml'
    ],
    # only loaded in demonstration mode
    'demo': [],
}
