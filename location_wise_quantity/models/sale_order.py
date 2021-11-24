from odoo import api, fields, models, _
from lxml import etree, html
from odoo.exceptions import UserError
from datetime import datetime


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    state = fields.Selection([
        ('draft', 'Quotation'),
        ('sent', 'Quotation Sent'),
        ('sale', 'Sales Order'),
        ('done', 'Locked'),
        ('cancel', 'Cancelled'),
    ], string='Status', readonly=True, copy=False, index=True, default='draft', related='order_id.state', store=True)
