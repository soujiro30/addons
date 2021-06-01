from odoo import models, fields, api, _
from datetime import datetime, date
from dateutil.relativedelta import relativedelta


class HrEmployeesInherited(models.Model):
    _inherit = 'hr.employee'

    @api.depends('resignation_ids')
    def _compute_no_of_resignation(self):
        for rec in self:
            rec.resignation_count = len(rec.resignation_ids.ids)

    resignation_ids = fields.One2many(comodel_name="hr.resignation", inverse_name="employee_id", string="Resignation(s)", required=False, )
    resignation_count = fields.Integer(string="Resignation Count", required=False, compute="_compute_no_of_resignation")
    date_joined = fields.Date(string="Date Hired", required=False, default=fields.Date.today())
    date_separated = fields.Date(string="Date Separated", required=False, )

    def cron_retirement_reminder(self):
        employees = self.env['hr.employee'].search([('date_separated', '=', False), ('age', '>=', 60)])
        if employees:
            for employee in employees:
                email_template_retirement_reminder = self.env.ref('hr_resignation.email_template_retirement_reminder')
                employee.message_post_with_template(email_template_retirement_reminder.id)


class HrEmployeePublicInherited(models.Model):
    _inherit = 'hr.employee.public'

    date_joined = fields.Date(string="Date Hired", required=False, )
    date_separated = fields.Date(string="Date Separated", required=False, )


class HrContractInherited(models.Model):
    _inherit = 'hr.contract'

    @api.model
    def create(self, values):
        res = super(HrContractInherited, self).create(values)
        if res:
            date_joined = date.today()
            first_contract = self.sudo().search([('employee_id', '=', values['employee_id'])],limit=1, order='date_start')
            if first_contract:
                date_joined = first_contract.date_start
            employee = self.env['hr.employee'].browse(values['employee_id'])
            employee.write({'date_joined': date_joined})
        return res