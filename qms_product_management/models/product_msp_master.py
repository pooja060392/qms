from odoo import api, fields, models, _
from odoo.addons import decimal_precision as dp
from odoo.exceptions import ValidationError, RedirectWarning, except_orm, AccessError, UserError


class ProductMSPMaster(models.Model):
    _name = 'product.msp.master'

    name = fields.Float(string="MSP %", required=True)
    active = fields.Boolean(string="Active", default=True)
