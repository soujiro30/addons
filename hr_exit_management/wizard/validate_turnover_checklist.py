from odoo import models, fields, api, _
from datetime import datetime, date


class ValidateTurnoverChecklistEmployee(models.TransientModel):
    _name = 'validate.turnover.checklist.employee'
    _description = 'Validate Turnover Checklist by Employee'

    exit_id = fields.Many2one(comodel_name="exit.management", string="EM Reference", required=False, )
    line_ids = fields.One2many(comodel_name="validate.turnover.checklist.employee.line", inverse_name="validate_id",
                               string="Lines", required=False, )

    @api.model
    def default_get(self, default_fields):
        res = super(ValidateTurnoverChecklistEmployee, self).default_get(default_fields)
        exit_management = self.env['exit.management'].browse(self._context.get('active_id'))
        turnover_list = []
        for chk in exit_management.checklist_ids.filtered(lambda x: x.turnover_type == 'employee'):
            turnover_list.append(chk.turnover_employee_id.id)
        docs = list()
        for r in exit_management.resignation_type_id.employee_list:
            if r.id not in turnover_list:
                docs.append([0, 0, {
                    'turnover_id': r.id,
                    'date_submitted': fields.Date.today()
                }])
        res.update({
            'exit_id': exit_management.id,
            'line_ids': docs
        })
        return res

    def action_validate_turnover(self):
        exit_management = self.env['exit.management'].browse(self._context.get('active_id'))
        validated_list = list()
        turnover_list = exit_management.employee_list.ids
        for r in self.line_ids:
            if r.submitted:
                validated_list.append({
                    'turnover_employee_id': r.turnover_id.id,
                    'name': r.turnover_id.name,
                    'date_submitted': r.date_submitted,
                    'notes': r.notes,
                    'turnover_type': 'employee',
                    'user_id': self.env.user.id,
                    'exit_id': exit_management.id
                })
                turnover_list.append(r.turnover_id.id)
        for r in validated_list:
            self.env['turnover.submission.checklist'].sudo().create(r)
        exit_management.sudo().write({'employee_list': [(6, 0, turnover_list)]})
        return {'type': 'ir.actions.act_window_close'}


class ValidateTurnoverChecklistEmployeeLine(models.TransientModel):
    _name = 'validate.turnover.checklist.employee.line'
    _description = 'Validate Turnover Checklist by Employee Line'

    validate_id = fields.Many2one(comodel_name="validate.turnover.checklist.employee", string="Validate List", required=False, )
    turnover_id = fields.Many2one(comodel_name="turnover.list.employee", string="Turnover List", required=False, )
    submitted = fields.Boolean(string="Submitted")
    date_submitted = fields.Date(string="Date Submitted", required=False, )
    notes = fields.Text(string="Notes")


class ValidateTurnoverChecklistEmployer(models.TransientModel):
    _name = 'validate.turnover.checklist.employer'
    _description = 'Validate Turnover Checklist by Employer'

    exit_id = fields.Many2one(comodel_name="exit.management", string="EM Reference", required=False, )
    line_ids = fields.One2many(comodel_name="validate.turnover.checklist.employer.line", inverse_name="validate_id",
                               string="Lines", required=False, )

    @api.model
    def default_get(self, default_fields):
        res = super(ValidateTurnoverChecklistEmployer, self).default_get(default_fields)
        exit_management = self.env['exit.management'].browse(self._context.get('active_id'))
        turnover_list = []
        for chk in exit_management.checklist_ids.filtered(lambda x: x.turnover_type == 'employer'):
            turnover_list.append(chk.turnover_employer_id.id)
        docs = list()
        for r in exit_management.resignation_type_id.employer_list:
            if r.id not in turnover_list:
                docs.append([0, 0, {
                    'turnover_id': r.id,
                    'date_submitted': fields.Date.today()
                }])
        res.update({
            'exit_id': exit_management.id,
            'line_ids': docs
        })
        return res

    def action_validate_turnover(self):
        exit_management = self.env['exit.management'].browse(self._context.get('active_id'))
        validated_list = list()
        turnover_list = exit_management.employer_list.ids
        for r in self.line_ids:
            if r.submitted:
                validated_list.append({
                    'turnover_employer_id': r.turnover_id.id,
                    'name': r.turnover_id.name,
                    'date_submitted': r.date_submitted,
                    'notes': r.notes,
                    'turnover_type': 'employer',
                    'user_id': self.env.user.id,
                    'exit_id': exit_management.id
                })
                turnover_list.append(r.turnover_id.id)
        for r in validated_list:
            self.env['turnover.submission.checklist'].sudo().create(r)
        exit_management.sudo().write({'employer_list': [(6, 0, turnover_list)]})
        return {'type': 'ir.actions.act_window_close'}


class ValidateTurnoverChecklistEmployerLine(models.TransientModel):
    _name = 'validate.turnover.checklist.employer.line'
    _description = 'Validate Turnover Checklist by Employer Line'

    validate_id = fields.Many2one(comodel_name="validate.turnover.checklist.employer", string="Validate List", required=False, )
    turnover_id = fields.Many2one(comodel_name="turnover.list.employer", string="Turnover List", required=False, )
    submitted = fields.Boolean(string="Submitted")
    date_submitted = fields.Date(string="Date Submitted", required=False, )
    notes = fields.Text(string="Notes")

