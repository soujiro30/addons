from odoo import models, api, fields


class HRResignationRemarksApprove(models.TransientModel):
    _name = 'hr.resignation.approve'
    _description = 'Resignation Approve'

    resignation_id = fields.Many2one(comodel_name="hr.resignation", string="Resignation", required=False, )
    remarks = fields.Text(string="Remarks", required=True, )

    def action_approve(self):
        resignation_id = self.env['hr.resignation'].sudo().browse(self.resignation_id.id)
        resignation_id.write({'remarks': self.remarks})
        resignation_id.action_approve()


class HRResignationRemarksRefuse(models.TransientModel):
    _name = 'hr.resignation.refuse'
    _description = 'Resignation Refuse'

    resignation_id = fields.Many2one(comodel_name="hr.resignation", string="Resignation", required=False, )
    remarks = fields.Text(string="Remarks", required=True, )

    def action_refuse(self):
        resignation_id = self.env['hr.resignation'].sudo().browse(self.resignation_id.id)
        resignation_id.write({'remarks': self.remarks})
        resignation_id.action_refuse()


class HRClearanceRemarksApprove(models.TransientModel):
    _name = 'hr.clearance.approve'
    _description = 'Clearance Approve'

    resignation_id = fields.Many2one(comodel_name="hr.resignation.clearance", string="Resignation", required=False, )
    remarks = fields.Text(string="Remarks", required=True, )

    def action_approve(self):
        resignation_id = self.resignation_id
        resignation_id.write({'remarks': self.remarks})
        resignation_id.action_approve()


class HRClearanceRemarksRefuse(models.TransientModel):
    _name = 'hr.clearance.refuse'
    _description = 'Clearance Refuse'

    resignation_id = fields.Many2one(comodel_name="hr.resignation.clearance", string="Resignation", required=False, )
    remarks = fields.Text(string="Remarks", required=True, )

    def action_refuse(self):
        resignation_id = self.resignation_id
        resignation_id.write({'remarks': self.remarks})
        resignation_id.action_refuse()