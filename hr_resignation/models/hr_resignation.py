from datetime import datetime, date
from odoo import models, fields, api, _, tools, SUPERUSER_ID
from odoo.exceptions import ValidationError, UserError
from dateutil.relativedelta import relativedelta


class HrResignationType(models.Model):
    _name = 'hr.resignation.type'
    _order = 'sequence'
    _description = 'Resignation Type'

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
        return super(HrResignationType, self).create(values)

    def write(self, values):
        if 'name' in values:
            name = values.get('name')
            values['name'] = str(name).upper()
        return super(HrResignationType, self).write(values)


class HrResignation(models.Model):
    _name = 'hr.resignation'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Resignation Letter"
    _order = 'expected_revealing_date desc, name'

    name = fields.Char(string='Resignation Reference', required=False, default='New')
    employee_id = fields.Many2one('hr.employee', string="Employee", default=lambda self: self.env['hr.employee'].sudo().search([('user_id', '=', self.env.user.id)], limit=1),
                                  help='Name of the employee for whom the request is creating')
    department_id = fields.Many2one('hr.department', string="Branch / Department",help='Department of the employee')
    company_id = fields.Many2one('res.company', string="Company", help='Company of the employee')
    job_id = fields.Many2one(comodel_name="hr.job", string="Job Position", required=False)
    date_filed = fields.Date(string="Date Filed", required=False, default=date.today())
    joined_date = fields.Date(string="Actual Joining Date", required=False, help='Joining date of the employee')
    expected_revealing_date = fields.Date(string="Expected Last Working Date", required=True,
                                          help='Date on which he is revealing from the company')
    resignation_type_id = fields.Many2one(comodel_name="hr.resignation.type", string="Probability Reason for Leaving", required=False)
    attachment_number = fields.Integer(compute='_get_attachment_number', string="Number of Attachments")
    attachment_ids = fields.One2many('ir.attachment', 'res_id', domain=[('res_model', '=', 'hr.resignation')],
                                     string='Attachments')
    reason = fields.Text(string="as", help='Specify Reason of Separation')
    remarks = fields.Text(string="Remarks", help='Specify Remarks of Separation')
    manager_id = fields.Many2one('hr.employee', string="Manager")
    state = fields.Selection(string="State", selection=[('draft', 'Draft'), ('manager_approval', 'Manager Approval'),
                                                        ('ongoing', 'Exit Clearance on Progress'), ('done', 'Done'),
                                                        ('refuse', 'Refuse')], required=False, default=False)
    clearance_ids = fields.One2many(comodel_name="hr.resignation.clearance", inverse_name="resignation_id", string="Exit Clearance", required=False, )

    def _get_attachment_number(self):
        read_group_res = self.env['ir.attachment'].read_group(
            [('res_model', '=', 'school.needs'), ('res_id', 'in', self.ids)],
            ['res_id'], ['res_id'])
        attach_data = dict((res['res_id'], res['res_id_count']) for res in read_group_res)
        for record in self:
            record.attachment_number = attach_data.get(record.id, 0)

    def action_get_attachment_tree_view(self):
        attachment_action = self.env.ref('base.action_attachment')
        action = attachment_action.read()[0]
        action['context'] = {'default_res_model': self._name, 'default_res_id': self.ids[0]}
        action['domain'] = str(['&', ('res_model', '=', self._name), ('res_id', 'in', self.ids)])
        action['search_view_id'] = (self.env.ref('hr_resignation.ir_attachment_view_search_inherit_resignation').id, )
        return action

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

    @api.onchange('employee_id')
    def _onchange_employee_id(self):
        if self.employee_id:
            self.job_id = self.employee_id.job_id.id
            self.department_id = self.employee_id.department_id.id
            self.company_id = self.employee_id.company_id.id
            self.manager_id = self.employee_id.parent_id.id
            self.joined_date = self.employee_id.date_joined

    @api.constrains('employee_id', 'expected_revealing_date', 'joined_date')
    def _check_dates(self):
        for rec in self:
            # revealing_date = datetime.strptime(rec.expected_revealing_date, '%Y-%m-%d').date()
            resignation_request = self.env['hr.resignation'].search([('employee_id', '=', rec.employee_id.id), ('id', '!=', rec.id),
                                                                     ('expected_revealing_date', '=', rec.expected_revealing_date)])
            if resignation_request:
                raise ValidationError(_('There is a duplicate resignation request in confirmed or'
                                        'approved state for this employee'))
            if rec.joined_date >= rec.expected_revealing_date:
                raise ValidationError(_('Revealing date must be anterior to joining date'))
    
    def get_mail_channel(self, sender, receiver):
        mail_channels = self.env['mail.channel']
        if sender and receiver:
            sender_partner = sender.partner_id
            receiver_partner = receiver.partner_id
            if sender_partner and receiver_partner:
                mail_channels_res = mail_channels.sudo().search(
                    [('public', '=', 'private'), ('channel_type', '=', 'chat'),
                     ('channel_partner_ids', 'in', [sender_partner.id, receiver_partner.id]),
                     '|', ('name', 'ilike', sender_partner.name + ', ' + receiver_partner.name),
                     ('name', 'ilike', receiver_partner.name + ', ' + sender_partner.name)], limit=1,
                    order='create_date desc')
                if mail_channels_res:
                    result = mail_channels_res
                else:
                    partners = [(4, sender_partner.id, None), (4, receiver_partner.id, None)]
                    mail_channel_create = mail_channels.sudo().create(
                        {'name': receiver_partner.name + ', ' + sender_partner.name,
                         'public': 'private',
                         'channel_type': 'chat',
                         'channel_partner_ids': partners})
                    result = mail_channel_create
                return result

    def create_mail_message(self, channel, sender, receiver, body):
        if channel and sender and receiver:
            mail_message = self.env['mail.message']
            sender_partner = sender.partner_id
            receiver_partner = receiver.partner_id
            if sender_partner and receiver_partner:
                vals = {
                    'date': datetime.now(),
                    'email_from': '\"' + sender_partner.name + '\"<' + sender_partner.email + '>',
                    'author_id': sender_partner.id,
                    'record_name': channel.name,
                    'model': 'mail.channel',
                    'res_id': int(channel.id),
                    'message_type': 'comment',
                    'subtype_id': self.env.ref('mail.mt_comment').id,
                    'reply_to': '\"' + sender_partner.name + '\"<' + sender_partner.email + '>',
                    'channel_ids': [(4, channel.id, None)],
                    'body': body
                }
                result = mail_message.sudo().create(vals)
                return result

    def action_confirm(self):
        if self.employee_id.user_id.id == self.env.user.id:
            self.state = 'manager_approval'
            sender = self.employee_id.user_id
            receiver = self.manager_id.user_id
            channel = self.get_mail_channel(sender, receiver)
            body = "<p>Hello Sir/Ma'am, I am requesting your approval of my resignation letter. Please check on your portal.<br/>Thank you!</p>"
            self.create_mail_message(channel, sender, receiver, body)
        else:
            raise ValidationError(_("You are not allowed to this action. Please contact the administrator"))

    def action_refuse(self):
        if self.env.user.has_group('hr_resignation.group_resignation_manager') and \
                (self.manager_id.user_id.id == self.env.user.id or self.employee_id.parent_id.user_id.id == self.env.user.id):
            self.state = 'refuse'
            sender = self.manager_id.user_id
            receiver = self.employee_id.user_id
            channel = self.get_mail_channel(sender, receiver)
            body = "<p>We're sorry to inform you that your request has been refuse due to the ff. reasons:<br/>" + self.remarks + "</p>"
            self.create_mail_message(channel, sender, receiver, body)
        else:
            raise ValidationError(_("You are not allowed to this action. Please contact the administrator"))

    def action_approve(self):
        if self.manager_id.user_id.id == self.env.uid or self.employee_id.parent_id.user_id.id == self.env.uid:
            self.state = 'ongoing'
            sender = self.manager_id.user_id
            receiver = self.employee_id.user_id
            channel = self.get_mail_channel(sender, receiver)
            body = "<p>Your request has been approved. Exit Clearance is now being processed. Thank you!</p>"
            self.create_mail_message(channel, sender, receiver, body)
            clearance = self.env['hr.resignation.clearance']
            template_id = self.env['hr.resignation.clearance.template'].search([('job_id', '=', self.job_id.id), 
                                                                                ('department_id', '=', self.department_id.id), 
                                                                                ('company_id', '=', self.company_id.id)], limit=1)
            print (template_id.template_ids.ids, template_id.name)

            if template_id and template_id.template_ids:
                for rec in template_id.template_ids:
                    values = {
                        'name': rec.name,
                        'signatory_id': rec.signatory_id.id,
                        'sequence': rec.sequence,
                        'state': 'draft',
                        'employee_id': self.employee_id.id,
                        'resignation_id': self.id
                    }
                    clearance.create(values)
                    sender = self.employee_id.user_id
                    receiver = rec.signatory_id.user_id
                    if sender != receiver:
                        channel = self.get_mail_channel(sender, receiver)
                        body = "<p>Please check the exit clearance of " + self.employee_id.name + " in your portal. Thank you!</p>"
                        self.create_mail_message(channel, sender, receiver, body)
            else:
                raise ValidationError(_("No template available for clearance. Please contact the HR Personnel to create a template for clearance."))
        else:
            raise ValidationError(_("You are not allowed to this action. Please contact the administrator"))

    @api.constrains('employee_id')
    def check_employee(self):
        # Checking whether the user is creating leave request of his/her own
        for rec in self:
            if not self.env.user.has_group('hr_resignation.group_resignation_hr_manager'):
                if rec.employee_id.user_id.id and rec.employee_id.user_id.id != self.env.uid:
                    raise ValidationError(_('You cannot create request for other employees'))


class HrResignationClearance(models.Model):
    _name = 'hr.resignation.clearance'
    _order = 'sequence, name'
    _description = 'Resignation Clearance'

    resignation_id = fields.Many2one(comodel_name="hr.resignation", string="Resignation", required=False, )
    signatory_id = fields.Many2one(comodel_name="hr.employee", string="Signatory", required=False, )
    employee_id = fields.Many2one(comodel_name="hr.employee", string="Employee", required=False, )
    name = fields.Char(string="Description", required=False, )
    remarks = fields.Text(string="Remarks", required=False, )
    state = fields.Selection(string="State", selection=[('draft', 'Draft'), ('approve', 'Approve'),
                                                        ('refuse', 'Refuse')], required=False, default='draft')
    sequence = fields.Integer(string="Sequence", required=False, default=10)

    def get_mail_channel(self, sender, receiver):
        mail_channels = self.env['mail.channel']
        if sender and receiver:
            sender_partner = sender.partner_id
            receiver_partner = receiver.partner_id
            if sender_partner and receiver_partner:
                mail_channels_res = mail_channels.sudo().search(
                    [('public', '=', 'private'), ('channel_type', '=', 'chat'),
                     ('channel_partner_ids', 'in', [sender_partner.id, receiver_partner.id]),
                     '|', ('name', 'ilike', sender_partner.name + ', ' + receiver_partner.name),
                     ('name', 'ilike', receiver_partner.name + ', ' + sender_partner.name)], limit=1,
                    order='create_date desc')
                if mail_channels_res:
                    result = mail_channels_res
                else:
                    partners = [(4, sender_partner.id, None), (4, receiver_partner.id, None)]
                    mail_channel_create = mail_channels.sudo().create(
                        {'name': receiver_partner.name + ', ' + sender_partner.name,
                         'public': 'private',
                         'channel_type': 'chat',
                         'channel_partner_ids': partners})
                    result = mail_channel_create
                return result

    def create_mail_message(self, channel, sender, receiver, body):
        if channel and sender and receiver:
            mail_message = self.env['mail.message']
            sender_partner = sender.partner_id
            receiver_partner = receiver.partner_id
            if sender_partner and receiver_partner:
                vals = {
                    'date': datetime.now(),
                    'email_from': '\"' + sender_partner.name + '\"<' + sender_partner.email + '>',
                    'author_id': sender_partner.id,
                    'record_name': channel.name,
                    'model': 'mail.channel',
                    'res_id': int(channel.id),
                    'message_type': 'comment',
                    'subtype_id': self.env.ref('mail.mt_comment').id,
                    'reply_to': '\"' + sender_partner.name + '\"<' + sender_partner.email + '>',
                    'channel_ids': [(4, channel.id, None)],
                    'body': body
                }
                result = mail_message.sudo().create(vals)
                return result

    def action_approve(self):
        if self.env.user.has_group('hr_resignation.group_resignation_clearance_approval') and self.signatory_id.user_id.id == self.env.user.id:
            self.state = "approve"
            sender = self.signatory_id.user_id
            receiver = self.employee_id.user_id
            channel = self.get_mail_channel(sender, receiver)
            body = "<p>Your exit clearance regarding with " + self.name + " has been approved. Thank you!</p>"
            self.create_mail_message(channel, sender, receiver, body)
        else:
            raise ValidationError(_("You are not allowed to do this action. Please contact the administrator"))

    def action_refuse(self):
        if self.env.user.has_group('hr_resignation.group_resignation_clearance_approval') and self.signatory_id.user_id.id == self.env.user.id:
            self.state = "refuse"
            sender = self.signatory_id.user_id
            receiver = self.employee_id.user_id
            channel = self.get_mail_channel(sender, receiver)
            body = "<p>We're sorry to inform that your exit clearance regarding with " + self.name + "has been refuse due to the following reason <br/>" + self.remarks + "</p>"
            self.create_mail_message(channel, sender, receiver, body)
        else:
            raise ValidationError(_("You are not allowed to do this action. Please contact the administrator"))


class HrResignationClearanceTemplate(models.Model):
    _name = 'hr.resignation.clearance.template'
    _order = 'name'
    _description = 'Clearance Template'

    department_id = fields.Many2one('hr.department', string="Branch / Department", help='Department of the employee')
    company_id = fields.Many2one('res.company', string="Company", help='Company of the employee')
    job_id = fields.Many2one(comodel_name="hr.job", string="Job Position", required=False)
    name = fields.Char(string="Name", required=False, default='New')
    template_ids = fields.One2many(comodel_name="hr.exit.clearance.template", inverse_name="clearance_template_id", string="Templates", required=False, )

    @api.constrains('job_id', 'department_id', 'company_id')
    def checking_records(self):
        for rec in self:
            records = self.search([('job_id', '=', rec.job_id.id), ('department_id', '=', rec.department_id.id),
                                   ('company_id', '=', rec.company_id.id), ('id', '!=', rec.id)], limit=1)
            if records:
                raise ValidationError(_('The template is already exists. Please check the records.'))

    @api.model
    def create(self, values):
        if values.get('name', 'New') == 'New':
            seq_date = None
            values['name'] = self.env['ir.sequence'].next_by_code('hr.resignation.clearance.template', sequence_date=seq_date) or '/'
        res = super(HrResignationClearanceTemplate, self).create(values)
        return res


class HrExitClearanceTemplate(models.Model):
    _name = 'hr.exit.clearance.template'
    _order = 'sequence, name'
    _description = 'Resignation Clearance Template'

    clearance_template_id = fields.Many2one(comodel_name="hr.resignation.clearance.template", string="Resignation Template", required=False, )
    signatory_id = fields.Many2one(comodel_name="hr.employee", string="Signatory", required=False, )
    name = fields.Char(string="Description", required=False, )
    sequence = fields.Integer(string="Sequence", required=False, default=10)
