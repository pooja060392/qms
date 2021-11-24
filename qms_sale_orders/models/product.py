
from odoo import fields, models


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    slide_number = fields.Integer('Slide Number', track_visibility='onchange')
