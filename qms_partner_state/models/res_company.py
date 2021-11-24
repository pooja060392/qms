
from odoo import models, fields


class ResCompany(models.Model):
    _inherit = 'res.company'

    partner_state_enable = fields.Boolean(
        'Use partner state?',
        default=True
    )
