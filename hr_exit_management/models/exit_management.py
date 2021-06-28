from odoo import models, api, fields, _
from odoo.exceptions import ValidationError
from datetime import datetime, date
from dateutil.relativedelta import relativedelta


class ExitManagementType(models.Model):
    _name = 'exit.management.type'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'sequence, name'
    _description = 'Exit Management Type'

    name = fields.Char(string="Name", required=False)
    can_employee_request = fields.Boolean(string="Can Employee Request")
    check_reason = fields.Boolean(string="With Reason")
    exit_clearance = fields.Boolean(string="Exit Clearance")
    exit_interview = fields.Boolean(string="Exit Interview")
    coe = fields.Boolean(string="Certificate of Employment")
    departure_reason = fields.Selection([
        ('resigned', 'Resignation'),
        ('fired', 'Termination'),
        ('layoff', 'Layoff/Retrenchment'),
        ('retired', 'Retirement')
    ], string="Departure Reason", tracking=True, help="Based on employee departure selection")
    sequence = fields.Integer(string="Sequence", required=False, default=10)
    employee_list = fields.Many2many(comodel_name="turnover.list.employee",  string="Turn Over List By Employee", )
    employer_list = fields.Many2many(comodel_name="turnover.list.employer", string="Turn Over List By Employer", )
    notice_period = fields.Integer(string="Notice Period (Days)", required=False, )
    user_ids = fields.Many2many(comodel_name="res.users", string="HR Responsible", required=False, )
    form_ids = fields.One2many(comodel_name="exit.management.type.forms", inverse_name="type_id",
                                 string="Interview Forms", required=False, )

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


class ExitManagementTypeForms(models.Model):
    _name = 'exit.management.type.forms'
    _description = 'Interview Forms for Exit Management Type'

    type_id = fields.Many2one(comodel_name="exit.management.type", string="Type", required=False, )
    survey_id = fields.Many2one(comodel_name="survey.survey", string="Forms", required=False, )
    company_id = fields.Many2one(comodel_name="res.company", string="Company", required=False, )


class TurnoverListEmployee(models.Model):
    _name = 'turnover.list.employee'
    _description = 'Turn Over List by Employee'
    _order = ' name'

    name = fields.Char(string="Name", required=False, )


class TurnoverListEmployer(models.Model):
    _name = 'turnover.list.employer'
    _description = 'Turn Over List by Employer'
    _order = ' name'

    name = fields.Char(string="Name", required=False, )


class ExitManagementProbabilityReason(models.Model):
    _name = 'exit.management.probability.reason'
    _description = 'Probable Reason'
    _order = 'sequence'

    name = fields.Char(string="Name", required=False)
    description = fields.Text(string="Description", required=False, )
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


class ExitManagementProbabilityCancellation(models.Model):
    _name = 'exit.management.probability.cancellation'
    _description = 'Probable Reason for Cancellation'
    _order = 'sequence'

    name = fields.Char(string="Name", required=False)
    description = fields.Text(string="Description", required=False, )
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
        return super(ExitManagementProbabilityCancellation, self).create(values)

    def write(self, values):
        if 'name' in values:
            name = values.get('name')
            values['name'] = str(name).upper()
        return super(ExitManagementProbabilityCancellation, self).write(values)


class ExitManagement(models.Model):
    _name = 'exit.management'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Exit Management"
    _order = 'effective_date desc, name'

    name = fields.Char(string='Reference', required=False, default='New')
    employee_id = fields.Many2one('hr.employee', string="Employee", default=lambda self: self.env['hr.employee'].sudo().search([('user_id', '=', self.env.user.id)], limit=1),
                                  help='Name of the employee for whom the request is creating', tracking=True,)
    department_id = fields.Many2one('hr.department', string="Department", help='Department of the employee',)
    company_id = fields.Many2one('res.company', string="Company", help='Company of the employee',)
    job_id = fields.Many2one(comodel_name="hr.job", string="Job Title", required=False)
    contract_id = fields.Many2one(comodel_name="hr.contract", string="Current Contract", required=False, )
    resignation_id = fields.Many2one(comodel_name="hr.resignation", string="Resignation Reference", required=False, )
    date_filed = fields.Date(string="Date Created", required=False, default=fields.Date.today())
    date_joined = fields.Date(string="Date Hired", required=False, help='Joining date of the employee')
    effective_date = fields.Date(string="Effectivity Date", required=True, tracking=True,
                                          help='Date on which he / she is leaving from the company')
    notice_period = fields.Integer(string="Notice Period (Days)", required=False, default=30)
    resignation_type_id = fields.Many2one(comodel_name="exit.management.type", string="Type", tracking=True, required=False)
    check_reason = fields.Boolean(string="With Reason", related='resignation_type_id.check_reason', store=True)
    exit_clearance = fields.Boolean(string="Check Exit Clearance", related='resignation_type_id.exit_clearance', store=True)
    exit_interview = fields.Boolean(string="Check Exit Interview", related='resignation_type_id.exit_interview', store=True)
    probability_reason_id = fields.Many2one(comodel_name="exit.management.probability.reason", string="Probable Reason",
                                            required=False, tracking=True,)
    probability_cancellation_id = fields.Many2one(comodel_name="exit.management.probability.cancellation", tracking=True, string="Probable Reason for Cancellation",
                                                  required=False, )
    reason = fields.Html(string="Reason", help='Specify Reason to Exit')
    cancel_remarks = fields.Text(string="Cancellation Remarks", required=False)
    remarks = fields.Text(string="Remarks", required=False)
    tag_ids = fields.Many2many(comodel_name="exit.interview.tags", string="Tags", )
    state = fields.Selection(string="State", selection=[('draft', 'Draft'), ('ongoing', 'On Going'), ('done', 'Done'),
                                                        ('hold', 'On Hold'), ('cancel', 'Cancelled')], required=False, default=False, tracking=True,)
    clearance_ids = fields.One2many(comodel_name="exit.clearance", inverse_name="exit_id", string="Exit Clearance", required=False, )
    employee_list = fields.Many2many(comodel_name="turnover.list.employee", string="Turn OverList By Employee", )
    employer_list = fields.Many2many(comodel_name="turnover.list.employer", string="Turn OverList By Employer", )
    survey_id = fields.Many2one(comodel_name='survey.survey', string="Exit Interview Form", domain=[('exit_management', '=', True)],)
    response_id = fields.Many2one('survey.user_input', "Response", ondelete="set null")
    survey_sent = fields.Boolean(string="Sent Survey")
    link = fields.Char(string="Link", required=False)
    survey_completed = fields.Boolean(string="Completed Survey", compute="compute_survey_completed", store=True)
    checklist_ids = fields.One2many(comodel_name="turnover.submission.checklist", inverse_name="exit_id",
                                             string="Turnover Checklist", required=False, )
    years_of_service = fields.Integer(string="Years of Service", required=False, compute='compute_years_of_service', store=True)
    coe_reference = fields.Many2one(comodel_name="employee.certificate", string="COE Reference", required=False)
    coe_state = fields.Selection(string="COE Status", selection=[('draft', 'Draft'), ('approved', 'Approved'),
                                                                 ('signed', 'Signed')], required=False, default='draft')

    def action_certificate_employment(self):
        for record in self:
            if not record.coe_reference:
                coe = self.env['employee.certificate']
                purpose = self.env['employee.purpose'].search([('name', '=ilike', 'Multi-Purpose')], limit=1)
                if not purpose:
                    purpose = self.env['employee.purpose'].sudo().create({'name': 'Multi-Purpose'})
                values = {
                    'employee_id': record.employee_id.id,
                    'certificate_type': 'COE',
                    'job_id': record.job_id.id,
                    'purpose': purpose.id,
                    'department_id': record.department_id.id,
                    'company_id': record.company_id.id,
                    'date_start': record.date_joined,
                    'exit_id': record.id,
                    'name': 'New'
                }
                res = coe.sudo().create(values)
                res.submit_request()
                res.confirm_request()
                res.verify_request()
                record.coe_reference = res
                record.coe_state = 'approved'

    def action_approval_coe(self):
        self.ensure_one()
        self.coe_state = 'signed'
        return {
            'name': _('Signed Certificate of Employment'),
            'type': 'ir.actions.act_window',
            'view_mode': 'tree,form',
            'res_model': 'employee.certificate',
            'target': 'current',
            'domain': [('exit_id', '=', self.id)],
            'context': {
                'default_exit_id': self.id,
            },
        }

    def print_report(self):
        self.ensure_one()
        coe = self.coe_reference
        coe.downloaded = True
        return self.env.ref('hr_exit_management.action_coe_pdf').report_action(self)

    @api.depends('date_joined', 'effective_date')
    def compute_years_of_service(self):
        for record in self:
            if record.date_joined and record.effective_date:
                years_of_service = round(((record.effective_date - record.date_joined).days + 1) / 365, 0)
                if years_of_service < 1:
                    years_of_service = 1
                record.years_of_service = years_of_service

    @api.depends('response_id')
    def compute_survey_completed(self):
        for record in self:
            if record.response_id:
                if record.response_id.state == 'done':
                    record.update({'survey_completed': True})

    def compute_complete_procedure(self):
        for record in self:
            initial_msg = 'Warning: Please see the requirements below: \n'
            message = ''
            if record.exit_interview and not record.survey_sent:
                message += '\tExit Interview not done yet.\n'
            if record.exit_clearance and record.clearance_ids:
                undone_clearance = record.clearance_ids.filtered(lambda x: x.state in ['draft', 'hold'])
                if undone_clearance:
                    for line in undone_clearance:
                        message += '\tExit Clearance: %s \n' % line.name
            employee_list = record.checklist_ids.filtered(lambda x: x.turnover_type == 'employee')
            employer_list = record.checklist_ids.filtered(lambda x: x.turnover_type == 'employer')
            if employee_list:
                turnover_list_employee = []
                for checklist in employee_list:
                    turnover_list_employee.append(checklist.turnover_employee_id.id)
                for r in record.resignation_type_id.employee_list:
                    if r.id not in turnover_list_employee:
                        message += '\tTurn Over By Employee: %s.\n' % r.name
            else:
                message += '\tTurn Over List By Employee Not Yet Submitted.\n'

            if employer_list:
                turnover_list_employer = []
                for checklist in employer_list:
                    turnover_list_employer.append(checklist.turnover_employer_id.id)
                for r in record.resignation_type_id.employer_list:
                    if r.id not in turnover_list_employer:
                        if r.id not in turnover_list_employer:
                            message += '\tTurn Over By Employer: %s.\n' % r.name
            else:
                message += '\tTurn Over List By Employer Not Yet Submitted.\n'

            if message:
                raise ValidationError(_(initial_msg + message))

    def action_create_survey(self):
        self.ensure_one()
        survey_id = self.survey_id
        if survey_id:
            if not self.response_id and not self.survey_sent:
                partner_id = self.employee_id.user_id.partner_id
                response = survey_id._create_answer(partner=partner_id)
                link = (survey_id.public_url + "?answer_token=%s" % response.token)
                self.write({'response_id': response.id, 'survey_sent': True, 'link': link})
        else:
            raise ValidationError(_("Please select an interview forms for the employee."))

    def action_send_email_survey(self):
        for record in self:
            if not self.response_id and not self.survey_sent:
                self.action_create_survey()
            email_template_exit_sending_survey = self.env.ref('hr_exit_management.email_template_exit_sending_survey')
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
        values['state'] = 'ongoing'
        if values.get('name', 'New') == 'New':
            seq_date = None
            if 'date_filed' in values:
                seq_date = fields.Datetime.context_timestamp(self, fields.Datetime.to_datetime(values['date_filed']))
            values['name'] = self.env['ir.sequence'].next_by_code('exit.management', sequence_date=seq_date) or '/'
        res = super(ExitManagement, self).create(values)
        if res:
            res._onchange_employee_id()
            res.check_exit_clearance()
            res.check_exit_interview()
            res.action_confirm()
            res.check_resignation_user_ids(values)
        return res

    def write(self, values):
        res = super(ExitManagement, self).write(values)
        self.check_resignation_user_ids(values)
        return res

    def exit_clearance_template(self, employee, job, department, company):
        result = []
        template_id = self.env['exit.clearance.template'].search([('job_id', '=', job), ('department_id', '=', department),
                                                                  ('company_id', '=', company)], limit=1)

        if template_id and template_id.template_ids:
            for rec in template_id.template_ids:
                values = {
                    'name': rec.name,
                    'department_id': rec.department_id.id,
                    'signatory_id': rec.signatory_id.id,
                    'sequence': rec.sequence,
                    'state': 'draft',
                    'clearance_template_line_id': rec.id,
                    'transaction_date': fields.Datetime.now(),
                    'dependency_id': rec.dependency_id.id,
                    'employee_id': employee,
                }
                result.append(values)
        return result

    @api.onchange('employee_id', 'exit_interview', 'resignation_type_id')
    def check_exit_interview(self):
        for record in self:
            if record.employee_id and record.resignation_type_id and record.exit_interview:
                if record.resignation_type_id.form_ids:
                    survey_id = None
                    for form in record.resignation_type_id.form_ids:
                        if form.company_id.id == record.company_id.id:
                            survey_id = form.survey_id.id
                    if survey_id is not None:
                        record.update({'survey_id': survey_id})
                    else:
                        raise ValidationError(_("No exit interview form available . Please contact the HR Personnel to create a template for clearance."))
                else:
                    raise ValidationError(_("No exit interview form available . Please contact the HR Personnel to create a template for clearance."))

    @api.onchange('employee_id', 'exit_clearance', 'resignation_type_id')
    def check_exit_clearance(self):
        for record in self:
            if record.employee_id and record.resignation_type_id and record.exit_clearance:
                clearance_list = list()
                clearance_ids = record.clearance_ids
                exit_clearance_template = record.exit_clearance_template(record.employee_id.id, record.job_id.id, record.department_id.id, record.company_id.id)
                if exit_clearance_template:
                    record.clearance_ids = None
                    for values in exit_clearance_template:
                        clearance_list.append([0, 0, values])
                    record.sudo().update({'clearance_ids': clearance_list})
                else:
                    raise ValidationError(_("No exit clearance template available . Please contact the HR Personnel to create a template for clearance."))

    def check_resignation_user_ids(self, values):
        for record in self:
            resignation_id = values.get('resignation_id') or record.resignation_id.id
            employee_id = values.get('employee_id') or record.employee_id.id
            type_id = values.get('resignation_type_id') or record.resignation_type_id.id
            resignation_type_id = self.env['exit.management.type'].sudo().browse(type_id)
            if not resignation_id:
                if resignation_type_id.user_ids:
                    if self.env.user.id not in resignation_type_id.user_ids.ids:
                        raise ValidationError(_("You are not allowed to create for this exit management.\n Please check the allowed users in EM Type."))
                    else:
                        if self.env.user.company_ids:
                            employee = self.env['hr.employee'].sudo().browse(employee_id)
                            if employee.company_id.id in self.env.user.company_ids.ids:
                                continue
                            else:
                                raise ValidationError(_("You are not allowed to create for this exit management.\n Please check the assigned company in your portal."))
                else:
                    raise ValidationError(_("No HR Responsible for this Exit Management Type."))

    @api.onchange('resignation_type_id')
    def onchange_resignation_type_id(self):
        result = {}
        for record in self:
            if record.resignation_type_id:
                result['domain'] = {'employee_list': [('id', 'in', record.resignation_type_id.employee_list.ids)],
                                    'employer_list': [('id', 'in', record.resignation_type_id.employer_list.ids)]}
        return result

    @api.onchange('resignation_type_id', 'date_filed')
    def get_effective_date(self):
        for record in self:
            if record.resignation_type_id and record.date_filed:
                self.effective_date = record.date_filed + relativedelta(days=record.resignation_type_id.notice_period)

    @api.onchange('employee_id')
    def _onchange_employee_id(self):
        if self.employee_id:
            self.job_id = self.employee_id.job_id.id
            self.department_id = self.employee_id.department_id.id
            self.company_id = self.employee_id.company_id.id
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

    def action_confirm(self):
        for record in self:
            if not record.date_joined:
                raise ValidationError(_("Please contact the HR Personnel to specify the actual date of joining. "))
            record.state = 'ongoing'
            if record.exit_clearance and record.clearance_ids:
                for clearance in record.clearance_ids:
                    if not clearance.clearance_template_line_id.dependency_id:
                        values = {
                            'signatory_id': clearance.signatory_id.id,
                            'employee_id': clearance.employee_id.id,
                            'state': clearance.state
                        }
                        clearance.activity_update(values)
                        email_template_clearance_approval = self.env.ref('hr_exit_management.email_template_sending_clearance_signatories')
                        clearance.message_post_with_template(email_template_clearance_approval.id)

    def action_hold(self):
        if self.env.user.has_group('hr_exit_management.group_exit_management_hr_personnel'):
            self.state = 'hold'
        else:
            raise ValidationError(_("You are not allowed to do this action. Please contact the administrator"))

    def action_done(self):
        for record in self:
            if self.env.user.has_group('hr_exit_management.group_exit_management_hr_personnel'):
                record.compute_complete_procedure()
                record.state = 'done'
                if not record.coe_reference:
                    raise ValidationError(_("Please create a certificate of employment for %s." % record.employee_id.name))
                last_contract = self.env['hr.contract'].sudo().search([('employee_id', '=', record.employee_id.id),
                                                                       ('state', '=', 'open')], limit=1, order='date_start desc')
                if last_contract:
                    last_contract.write({'date_end': record.effective_date, 'state': 'close'})
                employee = record.employee_id
                employee.write({'date_separated': record.effective_date,
                                'departure_reason': record.resignation_type_id.departure_reason,
                                'departure_description': record.reason,
                                'active': False})

                user_id = employee.user_id
                # user_id.write({'active': False})
            else:
                raise ValidationError(_("You are not allowed to do this action. Please contact the administrator"))

    def action_cancel(self):
        if self.env.user.has_group('hr_exit_management.group_exit_management_hr_personnel'):
            self.state = 'cancel'
        else:
            raise ValidationError(_("You are not allowed to do this action. Please contact the administrator"))

    @api.constrains('resignation_type_id', 'effective_date', 'date_filed')
    def check_notice_period(self):
        for record in self:
            if record.effective_date and record.date_filed and record.resignation_type_id:
                notice_period = record.date_filed + relativedelta(days=record.resignation_type_id.notice_period)
                if record.effective_date < notice_period:
                    raise ValidationError(_("Please set your effective date properly prior to notice period."))

    def cron_reminder(self):
        signatory_list = []
        pending_clearance = self.env['exit.clearance'].search([('state', 'in', ['draft', 'hold'])])
        for clearance in pending_clearance:

            if (clearance.transaction_date + relativedelta(days=2)) < fields.Datetime.now():
                if clearance.signatory_id.id not in signatory_list:
                    signatory_list.append(clearance.signatory_id.id)
        if signatory_list:
            for rec in signatory_list:
                cron_reminder = self.env['hr.employee'].browse(rec)
                cron_reminder.cron_exit_clearance_reminder()

    def cron_delay_process(self):
        records = self.search([('state', 'in', ['ongoing', 'hold'])])
        if records:
            for record in records:
                date_today = fields.Date.today()
                if record.effective_date < date_today:
                    email_template_remind_delay_process = self.env.ref('hr_exit_management.email_template_remind_delay_process')
                    record.message_post_with_template(email_template_remind_delay_process.id)

    def cron_set_effectivity_date_to_employee(self):
        date_today = fields.Date.today()
        records = self.search([('state', 'in', ['ongoing', 'hold'])])
        if records:
            for record in records:
                if record.effective_date <= date_today:
                    employee = self.env['hr.employee'].sudo().browse(record.employee_id.id)
                    employee.write({'date_separated': record.effective_date})


class ExitInterviewTags(models.Model):
    _name = 'exit.interview.tags'
    _description = "Tags"

    name = fields.Char(string="Name", required=False)


class ExitClearance(models.Model):
    _name = 'exit.clearance'
    _order = 'sequence'
    _description = 'Exit Clearance'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    exit_id = fields.Many2one(comodel_name="exit.management", string="Reference", required=False, ondelete='cascade',)
    signatory_id = fields.Many2one(comodel_name="hr.employee", string="Responsible", required=False, tracking=True,
                                   domain="[('department_id', '=', department_id)]")
    user_id = fields.Many2one(comodel_name="res.users", string="Users", required=False, related='signatory_id.user_id', store=True)
    employee_id = fields.Many2one(comodel_name="hr.employee", string="Employee", required=False, )
    name = fields.Char(string="Description", required=False, tracking=True,)
    department_id = fields.Many2one('hr.department', string="Department", help='Department of the employee')
    clearance_template_line_id = fields.Many2one(comodel_name="exit.clearance.template.line", string="Clearance Template Line", required=False, )
    remarks = fields.Text(string="Remarks", required=False, )
    state = fields.Selection(string="Status", selection=[('draft', 'Waiting for Approval'), ('approve', 'Approved'),
                                                        ('hold', 'On Hold')], required=False, default='draft', tracking=True,)
    transaction_date = fields.Datetime(string="Date Created", required=False, tracking=True,)
    approval_date = fields.Datetime(string="Date Approved", required=False, tracking=True,)
    sequence = fields.Integer(string="Sequence", required=False, default=10)
    dependency_id = fields.Many2one(comodel_name="hr.employee", string="Dependency", required=False, tracking=True)
    check_approval_done = fields.Boolean(string="Check Approval Done", compute='compute_check_approval')
    check_approval_hold = fields.Boolean(string="Check Approval Hold", compute='compute_check_approval')

    @api.constrains('dependency_id', 'signatory_id', 'exit_id')
    def check_cross_dependency(self):
        for record in self:
            domain = [('id', '!=', record.id), ('exit_id', '=', record.exit_id.id),
                      ('dependency_id', '=', record.signatory_id.id),
                      ('signatory_id', '=', record.dependency_id.id)]
            found = self.search(domain)
            if found:
                raise ValidationError('Cross dependency detected! Please check the records properly.')

    @api.depends('signatory_id', 'state')
    def compute_check_approval(self):
        for record in self:
            if record.signatory_id:
                signatory_id = self.env['hr.employee'].sudo().browse(record.signatory_id.id)
                if signatory_id.user_id.id == self.env.user.id and record.state == 'draft':
                    check_approval_done = True
                    check_approval_hold = True
                elif signatory_id.user_id.id == self.env.user.id and self.state == 'hold':
                    check_approval_done = True
                    check_approval_hold = False
                else:
                    check_approval_done = False
                    check_approval_hold = False
            else:
                check_approval_done = False
                check_approval_hold = False
            record.check_approval_done = check_approval_done
            record.check_approval_hold = check_approval_hold

    def action_approve(self):
        for record in self:
            if self.signatory_id.user_id.id == self.env.user.id:
                message = ""
                if record.dependency_id:
                    for line in record.exit_id.clearance_ids.filtered(lambda x: x.signatory_id.id == record.dependency_id.id):
                        if line.state != 'approve':
                            message += f"\nResponsible: {record.dependency_id.name}" \
                                                 f"\nDescription: {line.name}"
                if message:
                    raise ValidationError(_(f"The following clearance must be approved first:{message}"))
                else:
                    for line in record.exit_id.clearance_ids.filtered(lambda x: x.dependency_id.id == record.signatory_id.id):
                        email_template_clearance_approval = self.env.ref('hr_exit_management.email_template_sending_clearance_signatories')
                        line.message_post_with_template(email_template_clearance_approval.id)
                        values = {
                            'signatory_id': line.signatory_id.id,
                            'employee_id': line.employee_id.id,
                            'state': line.state
                        }
                        line.activity_update(values)
                    record.state = "approve"
                    record.approval_date = fields.Datetime.now()
                    check_clearance = self.env['exit.clearance'].search([('exit_id', '=', record.exit_id.id),
                                                                         ('state', 'in', ['draft', 'hold'])])
                    if not check_clearance:
                        exit_id = record.exit_id
                        email_hr_finish_clearance_approval = self.env.ref('hr_exit_management.email_hr_finish_clearance_approval')
                        exit_id.message_post_with_template(email_hr_finish_clearance_approval.id)
            else:
                raise ValidationError(_("You are not allowed to do this action. Please contact the administrator"))

    def action_hold(self):
        if self.signatory_id.user_id.id == self.env.user.id:
            self.state = "hold"
            self.transaction_date = fields.Datetime.now()
        else:
            raise ValidationError(_("You are not allowed to do this action. Please contact the administrator"))

    def activity_update(self, values):
        for record in self:
            signatory_id = values.get('signatory_id') or record.signatory_id.id
            employee_id = values.get('employee_id') or record.employee_id.id
            signatory = self.env['hr.employee'].sudo().browse(signatory_id)
            employee = self.env['hr.employee'].sudo().browse(employee_id)
            state = values.get('state') or record.state
            note = '%s\'s request in exit clearance is now waiting your approval' % employee.name
            if state in ('draft', 'hold'):
                date_deadline = fields.Date.today() + relativedelta(days=2)
                record.activity_schedule('hr_exit_management.mail_exit_clearance_approval',
                                         summary='Exit Clearance Approval',
                                         note=note, user_id=signatory.user_id.id,
                                         date_deadline=date_deadline)


class ExitClearanceTemplate(models.Model):
    _name = 'exit.clearance.template'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'name'
    _description = 'Exit Procedure Template'

    department_id = fields.Many2one('hr.department', string="Department", help='Department of the employee', tracking=True)
    company_id = fields.Many2one('res.company', string="Company", help='Company of the employee', tracking=True)
    job_id = fields.Many2one(comodel_name="hr.job", string="Job Position", required=False, tracking=True)
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
        res = super(ExitClearanceTemplate, self).create(values)
        return res


class ExitClearanceTemplateLine(models.Model):
    _name = 'exit.clearance.template.line'
    _order = 'sequence'
    _description = 'Exit Procedure Template Line'

    clearance_template_id = fields.Many2one(comodel_name="exit.clearance.template", string="Resignation Template", required=False, )
    signatory_id = fields.Many2one(comodel_name="hr.employee", string="Responsible", required=False,
                                   domain="[('department_id', '=', department_id)]")
    name = fields.Char(string="Description", required=False, )
    sequence = fields.Integer(string="Sequence", required=False, default=10)
    department_id = fields.Many2one(comodel_name="hr.department", string="Department", required=False, )
    dependency_id = fields.Many2one(comodel_name="hr.employee", string="Dependency", required=False, domain="[('id', '!=', signatory_id)]")

    @api.constrains('dependency_id', 'signatory_id', 'clearance_template_id')
    def check_cross_dependency(self):
        for record in self:
            domain = [('id', '!=', record.id), ('clearance_template_id', '=', record. clearance_template_id.id),
                      ('dependency_id', '=', record.signatory_id.id),
                      ('signatory_id', '=', record.dependency_id.id)]
            found = self.search(domain)
            if found:
                raise ValidationError('Cross dependency detected! Please check the records properly.')


class TurnoverSubmissionChecklistEmployee(models.Model):
    _name = 'turnover.submission.checklist'
    _description = 'Turnover Submission Checklist'

    turnover_employee_id = fields.Many2one(comodel_name="turnover.list.employee", string="Turnover Employee List", required=False, )
    turnover_employer_id = fields.Many2one(comodel_name="turnover.list.employer", string="Turnover Employer List", required=False, )
    name = fields.Char(string="Description", required=False, )
    date_submitted = fields.Date(string="Date Submitted", required=False, )
    exit_id = fields.Many2one(comodel_name="exit.management", string="EM Reference", required=False, )
    user_id = fields.Many2one(comodel_name="res.users", string="Responsible", required=False, default=lambda self: self.env.user.id)
    turnover_type = fields.Selection(string="Type", selection=[('employee', 'By Employee'),
                                                               ('employer', 'By Employer'), ], required=False, )
    notes = fields.Text(string="Notes")