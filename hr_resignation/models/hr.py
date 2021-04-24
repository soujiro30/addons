from odoo import models, fields, api, _


class HrEmployeesInherited(models.Model):
    _inherit = 'hr.employee'

    @api.depends('resignation_ids')
    def _compute_no_of_resignation(self):
        for rec in self:
            rec.resignation_count = len(rec.resignation_ids.ids)

    resignation_ids = fields.One2many(comodel_name="hr.resignation", inverse_name="employee_id", string="Resignation(s)", required=False, )
    resignation_count = fields.Integer(string="Resignation Count", required=False, compute="_compute_no_of_resignation")
    date_joined = fields.Date(string="Actual date of Joining", required=False, )
    date_separated = fields.Date(string="Date Separated", required=False, )


class HrEmployeePublicInherited(models.Model):
    _inherit = 'hr.employee.public'
    date_joined = fields.Date(string="Actual date of Joining", required=False, )
    date_separated = fields.Date(string="Date Separated", required=False, )
