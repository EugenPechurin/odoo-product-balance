# -*- coding: utf-8 -*-
{
    'name': "Product balance",

    'summary': """
    """,

    'description': """
    """,

    'author': "My Company",
    'website': "http://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': [
    ],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/report_product_saldo.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
    ],
}