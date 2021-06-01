from odoo import fields, models


class Survey(models.Model):
    _inherit = 'survey.survey'

    category = fields.Selection(selection_add=[('exit_management', 'Exit Management')])
    company_id = fields.Many2one(comodel_name="res.company", string="Company", required=False, default=lambda self: self.env.company)
