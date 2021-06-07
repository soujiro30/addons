from datetime import datetime, date
from odoo import models, fields, api, _, tools, SUPERUSER_ID
from odoo.exceptions import ValidationError, UserError
from dateutil.relativedelta import relativedelta


class HrResignation(models.Model):
    _name = 'hr.resignation'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Resignation"
    _order = 'effective_date desc, name'

    name = fields.Char(string='Resignation Reference', required=False, default='New')
    employee_id = fields.Many2one('hr.employee', string="Employee", readonly=True, default=lambda self: self.env['hr.employee'].sudo().search([('user_id', '=', self.env.user.id)], limit=1),
                                  help='Name of the employee for whom the request is creating')
    department_id = fields.Many2one('hr.department', string="Department", readonly=True, help='Department of the employee')
    company_id = fields.Many2one('res.company', string="Company", readonly=True, help='Company of the employee')
    job_id = fields.Many2one(comodel_name="hr.job", string="Job Title", readonly=True, required=False)
    date_filed = fields.Date(string="Date Filed", required=False, default=fields.Date.today())
    date_joined = fields.Date(string="Date Hired", required=False, help='Joining date of the employee')
    effective_date = fields.Date(string="Effectivity Date", required=True, track_visibility="always",
                                          help='Date on which he is revealing from the company')
    notice_period = fields.Integer(string="Notice Period", required=False, default=30)
    resignation_type_id = fields.Many2one(comodel_name="exit.management.type", string="Type", required=False,
                                          domain="[('can_employee_request', '=', True)]")
    check_reason = fields.Boolean(string="With Reason", related='resignation_type_id.check_reason', store=True)
    probability_reason_id = fields.Many2one(comodel_name="exit.management.probability.reason", track_visibility="always",
                                            string="Probability Reason of Leaving", required=False, )
    subject = fields.Char(string="Subject", required=False, track_visibility="always")
    reason = fields.Html(string="Message", help='Message to Resigned', track_visibility="always")
    remarks = fields.Text(string="Remarks", required=False, )
    manager_id = fields.Many2one('hr.employee', string="Immediate Head / Manager", track_visibility="always")
    state = fields.Selection(string="Status", selection=[('draft', 'Draft'), ('manager_approval', 'Waiting for Manager\'s Approval'),
                                                        ('done', 'Approved'), ('cancel', 'Cancelled')], required=False, default=False)
    attachment_ids = fields.Many2many('ir.attachment', 'res_id', domain=[('res_model', '=', 'hr.resignation')], string="Email Attachments")

    @api.model
    def create(self, values):
        values['state'] = 'draft'
        if values.get('name', 'New') == 'New':
            seq_date = None
            if 'date_filed' in values:
                seq_date = fields.Datetime.context_timestamp(self, fields.Datetime.to_datetime(values['date_filed']))
            values['name'] = self.env['ir.sequence'].next_by_code('hr.resignation', sequence_date=seq_date) or '/'
        res = super(HrResignation, self).create(values)
        if res:
            res._onchange_employee_id()
        return res

    def write(self, values):
        res = super(HrResignation, self).write(values)
        return res

    @api.onchange('employee_id')
    def _onchange_employee_id(self):
        for record in self:
            if record.employee_id:
                record.job_id = record.employee_id.job_id.id
                record.department_id = record.employee_id.department_id.id
                record.company_id = record.employee_id.company_id.id
                record.manager_id = record.employee_id.parent_id.id
                record.date_joined = record.employee_id.date_joined
                record.resignation_type_id = self.env.ref('hr_resignation.exit_management_type_1').id
                record.effective_date = fields.Date.today() + relativedelta(days=record.resignation_type_id.notice_period)

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

    @api.constrains('resignation_type_id', 'effective_date', 'date_filed')
    def check_notice_period(self):
        for record in self:
            if record.effective_date and record.date_filed and record.resignation_type_id:
                notice_period = record.date_filed + relativedelta(days=record.resignation_type_id.notice_period)
                if record.effective_date < notice_period:
                    raise ValidationError(_("Please set your effective date properly prior to notice period."))

    def action_confirm(self):
        for record in self:
            if record.employee_id.user_id.id == record.env.user.id or self.env.user.has_group('hr_resignation.group_resignation_admin'):
                record.state = 'manager_approval'
                email_template_managers_approval = self.env.ref('hr_resignation.email_template_manager_waiting_approval')
                record.message_post_with_template(email_template_managers_approval.id)
            else:
                raise ValidationError(_("You are not allowed to this action. Please contact the administrator"))

    def action_cancel(self):
        for record in self:
            if self.env.user.has_group('hr_resignation.group_resignation_manager') and \
                    (record.manager_id.user_id.id == self.env.user.id or record.employee_id.parent_id.user_id.id == self.env.user.id):
                record.state = 'cancel'
            else:
                raise ValidationError(_("You are not allowed to this action. Please contact the administrator"))

    def action_approve(self):
        for record in self:
            if self.env.user.has_group('hr_resignation.group_resignation_manager') and \
                    (record.manager_id.user_id.id == self.env.uid or record.employee_id.parent_id.user_id.id == self.env.uid):
                record.state = 'done'
                effective_date = fields.Date.today() + relativedelta(days=self.resignation_type_id.notice_period)
                record.effective_date = effective_date
                exit_management = self.env['exit.management']
                employee_exist = exit_management.search([('employee_id', '=', record.employee_id.id),
                                                         ('probability_reason_id', '=', record.probability_reason_id.id),
                                                         ('effective_date', '=', effective_date)], limit=1)
                if not employee_exist:
                    values = {
                        'employee_id': record.employee_id.id,
                        'department_id': record.department_id.id,
                        'job_id': record.job_id.id,
                        'company_id': record.company_id.id,
                        'date_filed': fields.Date.today(),
                        'date_joined': record.date_joined,
                        'effective_date': effective_date,
                        'probability_reason_id': record.probability_reason_id.id,
                        'resignation_type_id': record.resignation_type_id.id,
                        'reason': record.reason,
                        'state': 'draft',
                        'name': 'New',
                        'resignation_id': record.id
                    }
                    res = exit_management.sudo().create(values)
                    if res.resignation_type_id.exit_clearance:
                        exit_clearance_template = res.exit_clearance_template(record.employee_id.id, record.job_id.id, record.department_id.id, record.company_id.id)
                        clearance = self.env['exit.clearance']
                        if exit_clearance_template:
                            for vals in exit_clearance_template:
                                vals['resignation_id'] = res.id
                                clearance.create(vals)
                        else:
                            raise ValidationError(_("No exit clearance template available . Please contact the HR Personnel to create a template for clearance."))

            else:
                raise ValidationError(_("You are not allowed to this action. Please contact the administrator"))
