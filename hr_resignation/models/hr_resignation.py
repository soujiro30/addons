from datetime import datetime, date
from odoo import models, fields, api, _, tools, SUPERUSER_ID
from odoo.exceptions import ValidationError, UserError
from dateutil.relativedelta import relativedelta


class ExitManagementType(models.Model):
    _name = 'exit.management.type'
    _order = 'sequence, name'
    _description = 'Exit Management Type'

    name = fields.Char(string="Name", required=False)
    can_employee_request = fields.Boolean(string="Can Employee Request")
    check_reason = fields.Boolean(string="With Reason")
    exit_clearance = fields.Boolean(string="Exit Clearance")
    exit_interview = fields.Boolean(string="Exit Interview")
    sequence = fields.Integer(string="Sequence", required=False, default=10)
    required_checklist = fields.Many2many(comodel_name="exit.management.required.checklist",  string="Required Checklist", )

    @api.constrains('name')
    def check_names(self):
        for record in self:
            if record.name:
                domain = [('name', '=ilike', record.name), ('id', '!=', record.id)]
                found = self.search(domain)
                if found:
                    raise ValidationError('Name already exists!')

    @api.model
    def create(self, values):
        if 'name' in values:
            name = values.get('name')
            values['name'] = str(name).upper()
        return super(ExitManagementType, self).create(values)

    def write(self, values):
        if 'name' in values:
            name = values.get('name')
            values['name'] = str(name).upper()
        return super(ExitManagementType, self).write(values)


class ExitManagementRequiredChecklist(models.Model):
    _name = 'exit.management.required.checklist'
    _description = 'Required Checklist'
    _order = 'name'

    name = fields.Char(string="Name", required=False)
    sequence = fields.Integer(string="Sequence", required=False, default=10)


class ExitManagementProbabilityReason(models.Model):
    _name = 'exit.management.probability.reason'
    _description = 'Probability Reason'
    _order = 'sequence'

    name = fields.Char(string="Name", required=False)
    sequence = fields.Integer(string="Sequence", required=False, default=10)

    @api.constrains('name')
    def check_names(self):
        for record in self:
            if record.name:
                domain = [('name', '=ilike', record.name), ('id', '!=', record.id)]
                found = self.search(domain)
                if found:
                    raise ValidationError('Name already exists!')

    @api.model
    def create(self, values):
        if 'name' in values:
            name = values.get('name')
            values['name'] = str(name).upper()
        return super(ExitManagementProbabilityReason, self).create(values)

    def write(self, values):
        if 'name' in values:
            name = values.get('name')
            values['name'] = str(name).upper()
        return super(ExitManagementProbabilityReason, self).write(values)


class HrResignation(models.Model):
    _name = 'hr.resignation'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Resignation"
    _order = 'effective_date desc, name'

    name = fields.Char(string='Resignation Reference', required=False, default='New')
    employee_id = fields.Many2one('hr.employee', string="Employee", default=lambda self: self.env['hr.employee'].sudo().search([('user_id', '=', self.env.user.id)], limit=1),
                                  help='Name of the employee for whom the request is creating')
    department_id = fields.Many2one('hr.department', string="Department",help='Department of the employee')
    company_id = fields.Many2one('res.company', string="Company", help='Company of the employee')
    job_id = fields.Many2one(comodel_name="hr.job", string="Job Title", required=False)
    date_filed = fields.Date(string="Date Filed", required=False, default=date.today())
    date_joined = fields.Date(string="Date Hired", required=False, help='Joining date of the employee')
    effective_date = fields.Date(string="Effectivity Date", required=True,
                                          help='Date on which he is revealing from the company')
    notice_period = fields.Integer(string="Notice Period", required=False, default=30)
    resignation_type_id = fields.Many2one(comodel_name="exit.management.type", string="Type", required=False,
                                          domain="[('can_employee_request', '=', True)]")
    check_reason = fields.Boolean(string="With Reason", related='resignation_type_id.check_reason', store=True)
    probability_reason_id = fields.Many2one(comodel_name="exit.management.probability.reason", string="Probability Reason of Leaving", required=False, )
    reason = fields.Html(string="Reason", help='Specify Reason of Separation')
    manager_id = fields.Many2one('hr.employee', string="Immediate Head / Manager")
    state = fields.Selection(string="Status", selection=[('draft', 'Draft'), ('manager_approval', 'Manager Approval'),
                                                        ('done', 'Done'), ('refuse', 'Refuse')], required=False, default=False)

    @api.model
    def create(self, values):
        values['state'] = 'draft'
        if values.get('name', 'New') == 'New':
            seq_date = None
            if 'date_filed' in values:
                seq_date = fields.Datetime.context_timestamp(self, fields.Datetime.to_datetime(values['date_filed']))
            values['name'] = self.env['ir.sequence'].next_by_code('hr.resignation', sequence_date=seq_date) or '/'
        res = super(HrResignation, self).create(values)
        return res

    def write(self, values):
        res = super(HrResignation, self).write(values)
        return res

    @api.onchange('effective_date', 'date_filed', 'notice_period')
    def onchange_effective_date(self):
        for record in self:
            if record.effective_date and record.date_filed:
                notice_period = record.notice_period
                check_notice_period = self.env['ir.config_parameter'].sudo().get_param('hr_resignation.notice_period',
                                                                                       notice_period)
                if int(check_notice_period) > 0:
                    notice_period = int(check_notice_period)
                adjusted_date = record.date_filed + relativedelta(days=notice_period)
                if record.effective_date < adjusted_date:
                    raise ValidationError(_("Please set your effective date properly"))

    @api.onchange('employee_id')
    def _onchange_employee_id(self):
        if self.employee_id:
            self.job_id = self.employee_id.job_id.id
            self.department_id = self.employee_id.department_id.id
            self.company_id = self.employee_id.company_id.id
            self.manager_id = self.employee_id.parent_id.id
            self.date_joined = self.employee_id.date_joined

    @api.constrains('employee_id', 'effective_date', 'date_joined')
    def _check_dates(self):
        for rec in self:
            resignation_request = self.env['hr.resignation'].search([('employee_id', '=', rec.employee_id.id), ('id', '!=', rec.id),
                                                                     ('effective_date', '=', rec.effective_date)])
            if resignation_request:
                raise ValidationError(_('There is a duplicate resignation request in confirmed or'
                                        'approved state for this employee'))
            if rec.date_joined:
                if rec.date_joined >= rec.effective_date:
                    raise ValidationError(_('Revealing date must be anterior to joining date'))

    def action_confirm(self):
        for record in self:
            if record.employee_id.user_id.id == record.env.user.id:
                record.state = 'manager_approval'
                email_template_managers_approval = self.env.ref('hr_resignation.email_template_manager_waiting_approval')
                record.message_post_with_template(email_template_managers_approval.id)
            else:
                raise ValidationError(_("You are not allowed to this action. Please contact the administrator"))

    def action_refuse(self):
        for record in self:
            if self.env.user.has_group('hr_resignation.group_resignation_manager') and \
                    (record.manager_id.user_id.id == self.env.user.id or record.employee_id.parent_id.user_id.id == self.env.user.id):
                record.state = 'refuse'
            else:
                raise ValidationError(_("You are not allowed to this action. Please contact the administrator"))

    def action_approve(self):
        for record in self:
            if self.env.user.has_group('hr_resignation.group_resignation_manager') and \
                    (record.manager_id.user_id.id == self.env.uid or record.employee_id.parent_id.user_id.id == self.env.uid):
                record.state = 'done'
                notice_period = record.notice_period
                check_notice_period = self.env['ir.config_parameter'].sudo().get_param('hr_resignation.notice_period', notice_period)
                if int(check_notice_period) > 0:
                    notice_period = int(check_notice_period)
                adjusted_date = record.date_filed + relativedelta(days=notice_period)
                if record.effective_date > adjusted_date:
                    effective_date = record.effective_date
                else:
                    effective_date = fields.Date.today() + relativedelta(days=notice_period)
                values = {
                    'employee_id': record.employee_id.id,
                    'department_id': record.department_id.id,
                    'job_id': record.job_id.id,
                    'company_id': record.company_id.id,
                    'date_filed': fields.Date.today(),
                    'date_joined': record.date_joined,
                    'notice_period': notice_period,
                    'effective_date': effective_date,
                    'probability_reason_id': record.probability_reason_id.id,
                    'resignation_type_id': record.resignation_type_id.id,
                    'reason': record.reason,
                    'state': 'draft',
                    'name': 'New',
                    'resignation_id': record.id
                }
                self.env['exit.management'].sudo().create(values)
                # res.action_confirm()
            else:
                raise ValidationError(_("You are not allowed to this action. Please contact the administrator"))
