from odoo import models, api, fields, _
from datetime import datetime, date


class AdditionalExitClearance(models.TransientModel):
    _name = 'additional.exit.clearance'

    name = fields.Char(string="Reference", required=False, related='exit_id.name')
    exit_id = fields.Many2one(comodel_name="exit.management", string="Exit Management", required=False )
    line_ids = fields.One2many(comodel_name="additional.exit.clearance.line", inverse_name="line_id", string="Clearances",
                               required=False, )

    def append_exit_clearance(self):
        for record in self:
            exit_clearance = self.env['exit.clearance']
            if record.line_ids:
                seq_list = []
                for seq in record.exit_id.clearance_ids:
                    seq_list.append(seq.sequence)
                sequence = max(seq_list) + 1
                for line in record.line_ids:
                    values = {
                        'name': line.name,
                        'signatory_id': line.signatory_id.id,
                        'employee_id': record.exit_id.employee_id.id,
                        'exit_id': record.exit_id.id,
                        'sequence': sequence,
                        'department_id': line.signatory_id.department_id.id,
                        'transaction_date': fields.Datetime.now(),
                        'dependency_id': line.dependency_id.id,
                        'state': 'draft',
                    }
                    sequence += 1
                    exit_clearance_res = exit_clearance.create(values)
                    email_template_clearance_approval = self.env.ref('hr_exit_management.email_template_sending_clearance_signatories')
                    exit_clearance_res.message_post_with_template(email_template_clearance_approval.id)


class AdditionalExitClearanceLine(models.TransientModel):
    _name = 'additional.exit.clearance.line'

    name = fields.Char(string="Description", required=False, )
    signatory_id = fields.Many2one(comodel_name="hr.employee", string="Responsible", required=False)
    dependency_id = fields.Many2one(comodel_name="hr.employee", string="Dependency", required=False)
    line_id = fields.Many2one(comodel_name="additional.exit.clearance", string="Clearances", required=False)