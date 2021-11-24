
from odoo import fields, models

class Company(models.Model):
    _inherit = 'res.company'

    # gift_approval_amount = fields.Monetary(string='Double validation amount', default=500,
    #                                           help="Minimum amount for which a double validation is required")
    pan = fields.Char("Pan Number")
    drug_lic_number = fields.Char("Drug License Number")
    fax_number = fields.Char("Fax Number")