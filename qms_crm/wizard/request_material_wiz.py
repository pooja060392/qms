from odoo import api, fields, models

class RequestMaterial(models.Model):
    _name = 'request.material'

    type = fields.Selection([('sample','Sample'),('gift','Gift')],string='Type')
