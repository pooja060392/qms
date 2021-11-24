# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _

class Brand(models.Model):
    _name = 'brand'
    _rec_name = 'name'

    name = fields.Char('Brand Name')
    company_id = fields.Many2one('res.company', 'Company')
    brand_division_id = fields.Many2one('division')



