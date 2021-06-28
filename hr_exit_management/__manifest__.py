# -*- coding: utf-8 -*-
{
    'name': "Exit Management",
    'summary': """Handle the exit process of the employee.""",
    'author': "Niel John Balogo",
    'category': 'Uncategorized',
    'version': '0.1',
    'depends': ['base', 'hr', 'hr_contract', 'mail', 'survey', 'hr_coe',
                'hr_personnel_requisition', 'hr_employee_dob'],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'wizard/resignation_remarks_views.xml',
        'wizard/additional_exit_clearance_views.xml',
        'views/exit_management_type_views.xml',
        'views/exit_clearance_template_views.xml',
        'views/hr_resignation_views.xml',
        'wizard/validate_turnover_checklist_views.xml',
        'views/hr_views.xml',
        'views/exit_management_views.xml',
        'data/mail_templates.xml',
        'views/survey_views.xml',
        'views/menuitem_views.xml',
        'data/ir_sequence_data.xml',
        'data/ir_cron_data.xml',
        'data/exit_management_type_data.xml',
        'data/exit_management_probability_reason_data.xml',
        'report/template/coe_template.xml',
        # 'views/res_config_settings_views.xml',
    ],
}