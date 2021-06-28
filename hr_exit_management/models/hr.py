from odoo import models, fields, api, _
from datetime import datetime, date
from dateutil.relativedelta import relativedelta
from odoo.exceptions import ValidationError


class HrEmployeesInherited(models.Model):
    _inherit = 'hr.employee'

    @api.depends('resignation_ids')
    def _compute_no_of_resignation(self):
        for rec in self:
            rec.resignation_count = len(rec.resignation_ids.ids)

    resignation_ids = fields.One2many(comodel_name="hr.resignation", inverse_name="employee_id", string="Resignation(s)", required=False, )
    resignation_count = fields.Integer(string="Resignation Count", required=False, compute="_compute_no_of_resignation")
    date_joined = fields.Date(string="Date Hired", required=False)
    date_separated = fields.Date(string="Date Separated", required=False, )
    departure_reason = fields.Selection([
        ('resigned', 'Resigned'),
        ('fired', 'Terminated'),
        ('layoff', 'Layoff/Retrenchment'),
        ('retired', 'Retired')
    ], string="Departure Reason", groups="hr.group_hr_user", copy=False, tracking=True)

    def cron_retirement_reminder(self):
        employees = self.env['hr.employee'].search([('date_separated', '=', False), ('age', '>=', 60)])
        if employees:
            for employee in employees:
                email_template_retirement_reminder = self.env.ref('hr_exit_management.email_template_retirement_reminder')
                employee.message_post_with_template(email_template_retirement_reminder.id)

    def cron_exit_clearance_reminder(self):
        for record in self:
            pending_clearance = self.env['exit.clearance'].search([('state', 'in', ['draft', 'hold']),
                                                                   ('signatory_id', '=', record.id)])

            mail_mail = self.env['mail.mail']
            receiver_user = record.user_id
            sender_user = self.env.user
            if receiver_user or sender_user:
                sender_email = sender_user.partner_id.email
                author = sender_user.company_id.partner_id
                receiver_email = receiver_user.partner_id.email
                body_html = "<p>Dear " + record.name + ",</p><br/><p>We would like to remind you about your pending exit clearance approvals. Please see below the list of clearance waiting for your approval.</p>"
                for clearance in pending_clearance:
                    body_html += "<li><p>   Description: <b>" + clearance.name + "</b> - Employee: <b>" + clearance.employee_id.name + "</b></p></li>"
                body_html += "<br/><p>Thank you!</p>"
                vals = {
                    'subject': "Exit Clearance Reminder for %s" % record.name,
                    'date': fields.Datetime.now(),
                    'email_from': '\"' + author.name + '\"<' + sender_email + '>',
                    'email_to': receiver_email,
                    'author_id': author.id,
                    'recipient_ids': [(4, receiver_user.partner_id.id)],
                    'body_html': body_html,
                    'auto_delete': False,
                    'message_type': 'email',
                    'notification': True,
                    'model': record._name,
                    'res_id': record.id,
                }
                result = mail_mail.sudo().create(vals)
                result.sudo().send()
                return result


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
            date_joined = fields.Date.today()
            first_contract = self.sudo().search([('employee_id', '=', values['employee_id'])],limit=1, order='date_start')
            if first_contract:
                date_joined = first_contract.date_start
            employee = self.env['hr.employee'].browse(values['employee_id'])
            if not employee.date_joined:
                employee.write({'date_joined': date_joined})
        return res

    def write(self, values):
        res = super(HrContractInherited, self).write(values)
        if res:
            date_joined = fields.Date.today()
            first_contract = self.sudo().search([('employee_id', '=', self.employee_id.id)], limit=1,
                                                order='date_start')
            if first_contract:
                date_joined = first_contract.date_start
            employee = self.env['hr.employee'].browse(self.employee_id.id)
            if not employee.date_joined:
                employee.write({'date_joined': date_joined})
        return res

class EmployeeCertificateInherited(models.Model):
    _inherit = 'employee.certificate'

    exit_id = fields.Many2one(comodel_name="exit.management", string="EM Reference", required=False,
                              domain="[('employee_id', '=', employee_id)]")

    @api.onchange('exit_id')
    def onchange_exit_id(self):
        if self.exit_id:
            self.employee_id = self.exit_id.employee_id.id
            self.certificate_type = 'COE'

    def _assign_coe_to_exit_management(self):
        for record in self:
            exit_management = self.env['exit.management'].search([('employee_id', '=', record.employee_id.id)], limit=1)
            if exit_management:
                if exit_management.resignation_type_id.coe and not exit_management.coe_reference:
                    exit_management.sudo().write({'coe_reference': record.id})

    def write(self, vals):
        res = super(EmployeeCertificateInherited, self).write(vals)
        if vals.get('state') == 'approved' or vals.get('certificate_type') == 'COE':
            self._assign_coe_to_exit_management()
        if 'exit_id' in vals:
            exit_id = self.exit_id
            exit_id.write({'coe_reference': self.id})
        return res

    @api.model
    def create(self, vals):
        res = super(EmployeeCertificateInherited, self).create(vals)
        if vals.get('state') == 'approved' or vals.get('certificate_type') == 'COE':
            res._assign_coe_to_exit_management()
        if 'exit_id' in vals:
            exit_id = self.env['exit.management'].browse(vals['exit_id'])
            exit_id.write({'coe_reference': res.id})
        return res


class HrDepartureWizard(models.TransientModel):
    _inherit = 'hr.departure.wizard'

    departure_reason = fields.Selection([
        ('resigned', 'Resigned'),
        ('fired', 'Terminated'),
        ('layoff', 'Layoff/Retrenchment'),
        ('retired', 'Retired')
    ], string="Departure Reason", default='resigned', help="Based on employee departure selection")


class PersonnelRequisition(models.Model):
    _inherit = "hr.personnel.requisition"

    @api.onchange('request_type', 'job_id', 'department_id', 'company_id')
    def onchange_request_type(self):
        result = {}
        for record in self:
            if record.request_type == 'Replacement' and record.job_id and record.department_id and record.company_id:
                partner_list = []
                check_exit_management = self.env['exit.management'].search([('job_id', '=', record.job_id.id),
                                                                            ('department_id', '=', record.department_id.id),
                                                                            ('company_id', '=', record.company_id.id)])
                if check_exit_management:
                    for em in check_exit_management:
                        if em.employee_id.user_id.partner_id.id not in partner_list:
                            partner_list.append(em.employee_id.user_id.partner_id.id)
                result['domain'] = {'replacement_employee_id': [('id', 'in', partner_list)]}
        return result
