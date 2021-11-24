# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _


class Division(models.Model):
    _name = 'division'

    name = fields.Char('Division Name')
    brands_line = fields.One2many('brand','brand_division_id',copy=True)
