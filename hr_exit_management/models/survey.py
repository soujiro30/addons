from odoo import fields, models


class Survey(models.Model):
    _inherit = 'survey.survey'

    company_id = fields.Many2one(comodel_name="res.company", string="Company", required=False, default=lambda self: self.env.company)
    exit_management = fields.Boolean(string="Exit Management")