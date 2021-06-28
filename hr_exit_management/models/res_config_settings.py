from odoo import models, api, fields, _


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    notice_period = fields.Integer(string='Notice Period (Days)', default=30,
                                   help='Basis on the number of days before the employee leaves the company.')