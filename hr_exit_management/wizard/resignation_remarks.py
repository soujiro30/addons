from odoo import models, api, fields


class HRResignationRemarksApprove(models.TransientModel):
    _name = 'hr.resignation.approve'
    _description = 'Resignation Approve'

    resignation_id = fields.Many2one(comodel_name="hr.resignation", string="Resignation", required=False, )
    remarks = fields.Text(string="Remarks", required=True, )

    def action_approve(self):
        resignation_id = self.env['hr.resignation'].sudo().browse(self.resignation_id.id)
        resignation_id.action_approve()
        resignation_id.write({'remarks': self.remarks})


class HRResignationRemarksRefuse(models.TransientModel):
    _name = 'hr.resignation.cancel'
    _description = 'Resignation Cancel'

    resignation_id = fields.Many2one(comodel_name="hr.resignation", string="Resignation", required=False, )
    remarks = fields.Text(string="Remarks", required=True, )
    probability_cancellation_id = fields.Many2one(comodel_name="exit.management.probability.cancellation",
                                                  string="Probable Reason for Cancellation", required=False, )

    def action_cancel(self):
        resignation_id = self.env['hr.resignation'].sudo().browse(self.resignation_id.id)
        resignation_id.action_cancel()
        resignation_id.write({'remarks': self.remarks, 'probability_cancellation_id': self.probability_cancellation_id.id})


class HRClearanceRemarksApprove(models.TransientModel):
    _name = 'hr.clearance.approve'
    _description = 'Clearance Approve'

    clearance_id = fields.Many2one(comodel_name="exit.clearance", string="Resignation", required=False, )
    remarks = fields.Text(string="Remarks", required=True, )

    def action_approve(self):
        clearance = self.env['exit.clearance'].sudo().browse(self.clearance_id.id)
        clearance.write({'remarks': self.remarks})
        clearance.action_approve()


class HRClearanceRemarksRefuse(models.TransientModel):
    _name = 'hr.clearance.refuse'
    _description = 'Clearance Refuse'

    clearance_id = fields.Many2one(comodel_name="exit.clearance", string="Resignation", required=False, )
    remarks = fields.Text(string="Remarks", required=True, )

    def action_hold(self):
        clearance = self.env['exit.clearance'].sudo().browse(self.clearance_id.id)
        clearance.write({'remarks': self.remarks})
        clearance.action_hold()


class ExitManagementHold(models.TransientModel):
    _name = 'exit.management.hold'
    _description = 'Exit Management Hold'

    exit_id = fields.Many2one(comodel_name="exit.management", string="Exit Reference", required=False, )
    remarks = fields.Text(string="Remarks", required=True, )

    def action_hold(self):
        exit_id = self.env['exit.management'].sudo().browse(self.exit_id.id)
        exit_id.write({'remarks': self.remarks})
        exit_id.action_hold()


class ExitManagementCancel(models.TransientModel):
    _name = 'exit.management.cancel'
    _description = 'Exit Management Cancel'

    exit_id = fields.Many2one(comodel_name="exit.management", string="Exit Reference", required=False, )
    remarks = fields.Text(string="Remarks", required=True, )
    probability_cancellation_id = fields.Many2one(comodel_name="exit.management.probability.cancellation",
                                                  string="Probable Reason for Cancellation", required=False, )

    def action_cancel(self):
        exit_id = self.env['exit.management'].sudo().browse(self.exit_id.id)
        exit_id.action_cancel()
        exit_id.write({'remarks': self.remarks, 'probability_cancellation_id': self.probability_cancellation_id.id})
