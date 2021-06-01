from odoo import models, api, fields, _
from odoo.exceptions import ValidationError
from datetime import datetime, date
from dateutil.relativedelta import relativedelta


class ExitManagement(models.Model):
    _name = 'exit.management'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Exit Management"
    _order = 'effective_date desc, name'

    name = fields.Char(string='Reference', required=False, default='New')
    employee_id = fields.Many2one('hr.employee', string="Employee", default=lambda self: self.env['hr.employee'].sudo().search([('user_id', '=', self.env.user.id)], limit=1),
                                  help='Name of the employee for whom the request is creating')
    department_id = fields.Many2one('hr.department', string="Department", help='Department of the employee')
    company_id = fields.Many2one('res.company', string="Company", help='Company of the employee')
    job_id = fields.Many2one(comodel_name="hr.job", string="Job Title", required=False)
    contract_id = fields.Many2one(comodel_name="hr.contract", string="Current Contract", required=False, )
    resignation_id = fields.Many2one(comodel_name="hr.resignation", string="Resignation Reference", required=False, )
    date_filed = fields.Date(string="Date Filed", required=False, default=date.today())
    date_joined = fields.Date(string="Date Hired", required=False, help='Joining date of the employee')
    effective_date = fields.Date(string="Effectivity Date", required=True,
                                          help='Date on which he / she is leaving from the company')
    notice_period = fields.Integer(string="Notice Period (Days)", required=False, default=30)
    resignation_type_id = fields.Many2one(comodel_name="exit.management.type", string="Type", required=False)
    check_reason = fields.Boolean(string="With Reason", related='resignation_type_id.check_reason', store=True)
    exit_clearance = fields.Boolean(string="Check Exit Clearance", related='resignation_type_id.exit_clearance', store=True)
    exit_interview = fields.Boolean(string="Check Exit Interview", related='resignation_type_id.exit_interview', store=True)
    probability_reason_id = fields.Many2one(comodel_name="exit.management.probability.reason", string="Probability Reason of Leaving", required=False, )
    reason = fields.Html(string="Reason", help='Specify Reason of Separation')
    state = fields.Selection(string="State", selection=[('draft', 'Draft'), ('ongoing', 'Exit Procedures on Going'), ('done', 'Done'),
                                                        ('hold', 'On Hold')], required=False, default=False)
    clearance_ids = fields.One2many(comodel_name="exit.clearance", inverse_name="resignation_id", string="Exit Clearance", required=False, )
    required_checklist_ids = fields.Many2many(comodel_name="exit.management.required.checklist",
                                              string="Required Checklist")
    survey_id = fields.Many2one(comodel_name='survey.survey', string="Exit Interview Form", domain=[('category', '=', 'exit_management')],)
    response_id = fields.Many2one('survey.user_input', "Response", ondelete="set null")
    survey_sent = fields.Boolean(string="Sent Survey")
    survey_completed = fields.Boolean(string="Completed Survey", compute="compute_survey_completed", store=True)
    link = fields.Char(string="Link", required=False)
    complete_procedure = fields.Boolean(string="Complete Procedure", compute="compute_complete_procedure", store=True)

    @api.depends('response_id')
    def compute_survey_completed(self):
        for record in self:
            if record.response_id:
                if record.response_id.state == 'done':
                   record.survey_completed = True
                else:
                    record.survey_completed = False
            else:
                record.survey_completed = False

    @api.depends('clearance_ids', 'response_id', 'exit_interview', 'exit_clearance')
    def compute_complete_procedure(self):
        complete_procedure = False
        for record in self:
            if record.exit_interview and record.response_id:
                if record.response_id.state == 'done':
                    complete_procedure = True
                else:
                    complete_procedure = False
            if record.exit_clearance and record.clearance_ids:
                undone_clearance = record.clearance_ids.filtered(lambda x: x.state in ['draft', 'hold'])
                if undone_clearance:
                        complete_procedure = False
                else:
                    complete_procedure = True
            if not record.exit_clearance and not record.exit_interview:
                complete_procedure = True
            record.complete_procedure = complete_procedure

    def action_create_survey(self):
        self.ensure_one()
        survey_id = self.survey_id
        if not self.response_id and not self.survey_sent:
            partner_id = self.employee_id.user_id.partner_id
            response = survey_id._create_answer(partner=partner_id)
            link = (survey_id.public_url + "?answer_token=%s" % response.token)
            self.write({'response_id': response.id, 'survey_sent': True, 'link': link})

    def action_send_email_survey(self):
        for record in self:
            email_template_exit_sending_survey = self.env.ref('hr_resignation.email_template_exit_sending_survey')
            record.message_post_with_template(email_template_exit_sending_survey.id)

    def action_start_survey(self):
        self.ensure_one()
        if not self.response_id:
            partner_id = self.employee_id.user_id.partner_id
            response = self.survey_id._create_answer(partner=partner_id)
            self.response_id = response.id
        else:
            response = self.response_id
        return self.survey_id.with_context(survey_token=response.token).action_start_survey()

    def action_print_survey(self):
        self.ensure_one()
        if not self.response_id:
            return self.survey_id.action_print_survey()
        else:
            response = self.response_id
            return self.survey_id.with_context(survey_token=response.token).action_print_survey()

    @api.model
    def create(self, values):
        values['state'] = 'draft'
        if values.get('name', 'New') == 'New':
            seq_date = None
            if 'date_filed' in values:
                seq_date = fields.Datetime.context_timestamp(self, fields.Datetime.to_datetime(values['date_filed']))
            values['name'] = self.env['ir.sequence'].next_by_code('exit.management', sequence_date=seq_date) or '/'
        res = super(ExitManagement, self).create(values)
        return res

    def write(self, values):
        res = super(ExitManagement, self).write(values)
        return res

    def action_confirm(self):
        if self.env.user.has_group('hr_resignation.group_exit_clearance_hr_personnel'):
            self.state = 'ongoing'
            if self.exit_clearance:
                self.get_exit_clearance_template()
            if self.exit_interview:
                self.action_create_survey()
        else:
            raise ValidationError(_("You are not allowed to this action. Please contact the administrator"))

    @api.onchange('effective_date', 'notice_period', 'exit_clearance', 'exit_interview')
    def onchange_effective_date(self):
        for record in self:
            if record.notice_period and (record.exit_clearance or record.exit_interview):
                notice_period = record.notice_period
                check_notice_period = self.env['ir.config_parameter'].sudo().get_param('hr_resignation.notice_period',
                                                                                       notice_period)
                if int(check_notice_period) > 0:
                    notice_period = int(check_notice_period)
                adjusted_date = fields.Date.today() + relativedelta(days=notice_period)
                if record.effective_date:
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
            self.contract_id = self.employee_id.contract_id.id

    @api.constrains('employee_id', 'effective_date', 'date_joined')
    def _check_dates(self):
        for rec in self:
            resignation_request = self.env['exit.management'].search(
                [('employee_id', '=', rec.employee_id.id), ('id', '!=', rec.id),
                 ('effective_date', '=', rec.effective_date)])
            if resignation_request:
                raise ValidationError(_('There is a duplicate resignation request in confirmed or'
                                        'approved state for this employee'))
            if rec.date_joined:
                if rec.date_joined >= rec.effective_date:
                    raise ValidationError(_('Revealing date must be anterior to joining date'))

    def get_exit_clearance_template(self):
        for record in self:
            clearance = self.env['exit.clearance']
            template_id = self.env['exit.clearance.template'].search([('job_id', '=', record.job_id.id),
                                                                      ('department_id', '=',  record.department_id.id),
                                                                      ('company_id', '=', record.company_id.id)], limit=1)

            if template_id and template_id.template_ids:
                for rec in template_id.template_ids:
                    values = {
                        'name': rec.name,
                        'clearance_type_id': rec.clearance_type_id.id,
                        'signatory_id': rec.signatory_id.id,
                        'sequence': rec.sequence,
                        'state': 'draft',
                        'employee_id': record.employee_id.id,
                        'resignation_id': record.id
                    }
                    res = clearance.create(values)
                    email_template_clearance_approval = self.env.ref('hr_resignation.email_template_sending_clearance_signatories')
                    res.message_post_with_template(email_template_clearance_approval.id)
            else:
                raise ValidationError(_("No exit clearance template available . Please contact the HR Personnel to create a template for clearance."))

    def action_hold(self):
        if self.env.user.has_group('hr_resignation.group_exit_clearance_hr_personnel'):
            self.state = 'hold'
        else:
            raise ValidationError(_("You are not allowed to do this action. Please contact the administrator"))

    def action_done(self):
        if self.env.user.has_group('hr_resignation.group_exit_clearance_hr_personnel'):
            if self.complete_procedure:
                self.state = 'done'
                last_contract = self.env['hr.contract'].sudo().search([('employee_id', '=', self.employee_id.id),
                                                                       ('state', '=', 'open')], limit=1, order='date_start desc')
                if last_contract:
                    last_contract.write({'date_end': self.effective_date, 'state': 'close'})
                employee = self.employee_id
                employee.write({'date_separated': self.effective_date})
            else:
                raise ValidationError(_("The clearance procedure is not yet done. Please check the records properly."))
        else:
            raise ValidationError(_("You are not allowed to do this action. Please contact the administrator"))


class HrResignationClearance(models.Model):
    _name = 'exit.clearance'
    _order = 'sequence'
    _description = 'Exit Clearance'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    resignation_id = fields.Many2one(comodel_name="exit.management", string="Exit Management", required=False, )
    signatory_id = fields.Many2one(comodel_name="hr.employee", string="Responsible", required=False, )
    user_id = fields.Many2one(comodel_name="res.users", string="Users", required=False, related='signatory_id.user_id', store=True)
    employee_id = fields.Many2one(comodel_name="hr.employee", string="Employee", required=False, )
    name = fields.Char(string="Description", required=False, )
    clearance_type_id = fields.Many2one(comodel_name="exit.clearance.type", string="Clearance Type", required=False, )
    description = fields.Text(string="Description", required=False, )
    remarks = fields.Text(string="Remarks", required=False, )
    state = fields.Selection(string="Status", selection=[('draft', 'No Yet Approved'), ('approve', 'Approved'),
                                                        ('hold', 'Hold')], required=False, default='draft')
    transaction_date = fields.Datetime(string="Transaction Date", required=False, )
    sequence = fields.Integer(string="Sequence", required=False, default=10)

    def action_approve(self):
        if self.env.user.has_group('hr_resignation.group_exit_clearance_approval') and self.signatory_id.user_id.id == self.env.user.id:
            self.state = "approve"
            self.transaction_date = fields.Datetime.now()
            em_id = self.env['exit.management'].browse(self.resignation_id.id)
            not_yet_approved = 0
            for clearance in em_id.clearance_ids:
                if clearance.state == 'draft':
                    not_yet_approved += 1
            if not_yet_approved == 0:
                em_id.action_done()
        else:
            raise ValidationError(_("You are not allowed to do this action. Please contact the administrator"))

    def action_hold(self):
        if self.env.user.has_group('hr_resignation.group_exit_clearance_approval') and self.signatory_id.user_id.id == self.env.user.id:
            self.state = "hold"
            self.transaction_date = fields.Datetime.now()
        else:
            raise ValidationError(_("You are not allowed to do this action. Please contact the administrator"))

    def action_remind_approval(self):
        for record in self:
            email_template_clearance_approval_reminder = self.env.ref('hr_resignation.email_template_clearance_approval_reminder')
            record.message_post_with_template(email_template_clearance_approval_reminder.id)


class HrResignationClearanceTemplate(models.Model):
    _name = 'exit.clearance.template'
    _order = 'name'
    _description = 'Exit Procedure Template'

    department_id = fields.Many2one('hr.department', string="Branch / Department", help='Department of the employee')
    company_id = fields.Many2one('res.company', string="Company", help='Company of the employee')
    job_id = fields.Many2one(comodel_name="hr.job", string="Job Position", required=False)
    name = fields.Char(string="Name", required=False, default='New')
    template_ids = fields.One2many(comodel_name="exit.clearance.template.line", inverse_name="clearance_template_id", string="Templates", required=False, )

    @api.constrains('job_id', 'department_id', 'company_id')
    def checking_records(self):
        for rec in self:
            records = self.search([('job_id', '=', rec.job_id.id), ('department_id', '=', rec.department_id.id),
                                   ('company_id', '=', rec.company_id.id),
                                   ('id', '!=', rec.id)], limit=1)
            if records:
                raise ValidationError(_('The template is already exists. Please check the records.'))

    @api.model
    def create(self, values):
        if values.get('name', 'New') == 'New':
            seq_date = None
            values['name'] = self.env['ir.sequence'].next_by_code('exit.clearance.template', sequence_date=seq_date) or '/'
        res = super(HrResignationClearanceTemplate, self).create(values)
        return res


class HrExitClearanceTemplate(models.Model):
    _name = 'exit.clearance.template.line'
    _order = 'sequence'
    _description = 'Exit Procedure Template Line'

    clearance_template_id = fields.Many2one(comodel_name="exit.clearance.template", string="Resignation Template", required=False, )
    signatory_id = fields.Many2one(comodel_name="hr.employee", string="Signatory", required=False, )
    name = fields.Char(string="Description", required=False, )
    description = fields.Text(string="Description", required=False, )
    sequence = fields.Integer(string="Sequence", required=False, default=10)
    clearance_type_id = fields.Many2one(comodel_name="exit.clearance.type", string="Clearance Type", required=False, )


class HrExitClearanceType(models.Model):
    _name = 'exit.clearance.type'
    _description = 'Exit Procedure Type'
    _order = 'sequence, name'

    name = fields.Char(string="Clearance Type", required=False, )
    sequence = fields.Integer(string="Sequence", required=False, default=10)