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
    effective_date = fields.Date(string="Effectivity Date", required=True, tracking=True,)
    notice_period = fields.Integer(string="Notice Period", required=False, default=30)
    resignation_type_id = fields.Many2one(comodel_name="exit.management.type", string="Type", required=False,
                                          domain="[('can_employee_request', '=', True)]")
    check_reason = fields.Boolean(string="With Reason", related='resignation_type_id.check_reason', store=True)
    probability_reason_id = fields.Many2one(comodel_name="exit.management.probability.reason",
                                            string="Probable Reason", required=False, tracking=True,)
    probability_cancellation_id = fields.Many2one(comodel_name="exit.management.probability.cancellation", tracking=True,  string="Probable Reason for Cancellation", required=False, )
    subject = fields.Char(string="Subject", required=False)
    reason = fields.Html(string="Message", help='Message to Resigned')
    remarks = fields.Text(string="Remarks", required=False, )
    manager_id = fields.Many2one('hr.employee', string="Immediate Head / Manager", tracking=True)
    state = fields.Selection(string="Status", selection=[('draft', 'Draft'), ('manager_approval', 'Waiting for Manager\'s Approval'),
                                                        ('done', 'Approved'), ('cancel', 'Cancelled')], required=False, default=False, tracking=True,)
    attachment_ids = fields.Many2many('ir.attachment', 'res_id', domain=[('res_model', '=', 'hr.resignation')], string="Email Attachments")
    check_managers_approval = fields.Boolean(string="Check Managers Approval",  compute='compute_managers_approval')
    check_send = fields.Boolean(string="Check Send", compute='compute_send')

    @api.depends('manager_id', 'state')
    def compute_managers_approval(self):
        for record in self:
            if record.manager_id:
                manager = self.env['hr.employee'].sudo().browse(record.manager_id.id)
                if manager.user_id.id == self.env.user.id and record.state == 'manager_approval':
                    check_managers_approval = True
                else:
                    check_managers_approval = False
            else:
                check_managers_approval = False
            record.check_managers_approval = check_managers_approval

    @api.depends('employee_id', 'state')
    def compute_send(self):
        for record in self:
            if record.employee_id:
                employee_id = self.env['hr.employee'].sudo().browse(record.employee_id.id)
                if employee_id.user_id.id == self.env.user.id and record.state == 'draft':
                    check_send = True
                else:
                    check_send = False
                record.check_send = check_send

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
                employee_id = self.env['hr.employee'].sudo().browse(record.employee_id.id)
                record.job_id = employee_id.job_id.id
                record.department_id = employee_id.department_id.id
                record.company_id = employee_id.company_id.id
                record.manager_id = employee_id.parent_id.id
                record.date_joined = employee_id.date_joined
                record.resignation_type_id = self.env.ref('hr_exit_management.exit_management_type_1').id
                record.effective_date = fields.Date.today() + relativedelta(days=record.resignation_type_id.notice_period)
                record.subject = "Resignation: %s" % employee_id.name
                # if not record.employee_id.parent_id:
                #     raise ValidationError(_("You don't have an immediate head or manager"))

    @api.constrains('resignation_type_id', 'effective_date', 'date_filed')
    def check_notice_period(self):
        for record in self:
            if record.effective_date and record.date_filed and record.resignation_type_id:
                notice_period = record.date_filed + relativedelta(days=record.resignation_type_id.notice_period)
                if record.effective_date < notice_period:
                    raise ValidationError(_("Please set your effective date properly prior to notice period."))

    def action_confirm(self):
        for record in self:
            employee_id = self.env['hr.employee'].sudo().browse(record.employee_id.id)
            if employee_id.user_id.id == record.env.user.id or self.env.user.has_group('hr_exit_management.group_exit_management_admin'):
                if not record.manager_id:
                    raise ValidationError(_("You don't have an immediate head/manager. Please contact the HR Personnel."))
                if not self.date_joined:
                    raise ValidationError(_("Please contact the HR Personnel to specify the actual date of joining. "))
                record.state = 'manager_approval'
                mail_mail = self.env['mail.mail']
                manager_id = self.env['hr.employee'].sudo().browse(record.manager_id.id)
                receiver_user = manager_id.user_id
                sender_user = self.env.user
                if receiver_user or sender_user:
                    sender_email = sender_user.partner_id.email
                    author = sender_user.company_id.partner_id
                    receiver_email = receiver_user.partner_id.email
                    body_html = record.reason
                    attachment_list = []
                    if record.attachment_ids:
                        for attachment in record.attachment_ids:
                            attachment_list.append((4, attachment.id))
                    vals = {
                        'subject': record.subject,
                        'date': fields.Datetime.now(),
                        'email_from': '\"' + sender_user.name + '\"<' + sender_email + '>',
                        'email_to': receiver_email,
                        'author_id': receiver_user.id,
                        'recipient_ids': [(4, receiver_user.partner_id.id)],
                        'attachment_ids': attachment_list,
                        'body_html': body_html,
                        'auto_delete': True,
                        'reply_to': '\"' + sender_user.name + '\"<' + sender_email + '>',
                        'message_type': 'notification',
                        'notification': True,
                        'model': record._name,
                        'res_id': record.id,
                    }
                    record_sudo = record.sudo()
                    record_sudo.message_subscribe(partner_ids=employee_id.parent_id.user_id.partner_id.ids)
                    record.message_post(body=_(body_html), subject=record.subject, subtype_xmlid="mail.mt_comment",
                                        message_type='comment', record_name=record.name)
                    mail_mail.sudo().create(vals).send()
            else:
                raise ValidationError(_("You are not allowed to this action. Please contact the administrator"))

    def action_cancel(self):
        for record in self:
            if record.manager_id.user_id.id == self.env.user.id or record.employee_id.parent_id.user_id.id == self.env.user.id:
                record.state = 'cancel'
            else:
                raise ValidationError(_("You are not allowed to this action. Please contact the administrator"))

    def action_approve(self):
        for record in self:
            if record.manager_id.user_id.id == self.env.uid or record.employee_id.parent_id.user_id.id == self.env.uid:
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
                    exit_management.sudo().create(values)
                    email_template_hr_exit_notification = self.env.ref('hr_exit_management.email_template_hr_exit_notification')
                    record.message_post_with_template(email_template_hr_exit_notification.id)
                    email_template_managers_approved = self.env.ref('hr_exit_management.email_template_managers_approved')
                    record.message_post_with_template(email_template_managers_approved.id)
                else:
                    raise ValidationError(_("Cannot proceed to exit management because %s exists on the said record." % record.employee_id.name))
            else:
                raise ValidationError(_("You are not allowed to this action. Please contact the administrator"))

    def action_view_exit_management(self):
        self.ensure_one()
        return {
            'name': _('Exit Management'),
            'type': 'ir.actions.act_window',
            'view_mode': 'tree,form',
            'res_model': 'exit.management',
            'domain': [('resignation_id', '=', self.id)],
            'target': 'current',
            'context': {
                'default_resignation_id': self.id,
            },
        }