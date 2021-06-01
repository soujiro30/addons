# -*- coding: utf-8 -*-
{
    'name': "Exit Management",
    'summary': """Handle the resignation process of the employee.""",
    'author': "Niel John Balogo",
    'category': 'Uncategorized',
    'version': '0.1',
    'depends': ['base', 'hr', 'hr_contract', 'mail', 'survey'],
    'data': [
        'security/hr_resignation_security.xml',
        'security/ir.model.access.csv',
        'wizard/resignation_remarks_views.xml',
        'views/exit_management_type_views.xml',
        'views/exit_clearance_template_views.xml',
        'views/hr_resignation_views.xml',
        'views/exit_management_views.xml',
        'data/mail_templates.xml',
        'views/hr_views.xml',
        'views/survey_views.xml',
        'views/menuitem_views.xml',
        'data/ir_sequence_data.xml',
        'data/ir_cron_data.xml',
        'data/exit_management_type_data.xml',
        'data/exit_management_probability_reason_data.xml',
        'data/exit_interview_data.xml',
        'views/res_config_settings_views.xml',
    ],
}
