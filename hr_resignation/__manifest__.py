# -*- coding: utf-8 -*-
{
    'name': "Employee Resignation",

    'summary': """
        A module for resignation clearance of employee.""",

    'description': """
        Long description of module's purpose
    """,

    'author': "Niel John Balogo",
    'website': "http://www.yourcompany.com",

    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'hr', 'mail'],

    # always loaded
    'data': [
        'security/hr_resignation_security.xml',
        'security/ir.model.access.csv',
        'data/ir_sequence_data.xml',
        'wizard/resignation_remarks_views.xml',
        'views/hr_resignation_type_views.xml',
        'views/hr_resignation_clearance_template_views.xml',
        'views/hr_resignation_views.xml',
        'views/hr_views.xml',
        'views/menuitem_views.xml',
    ],
}
