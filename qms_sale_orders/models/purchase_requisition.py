# -*- coding: utf-8 -*-

from odoo import api, fields, models


class PurchaseRequisition(models.Model):
    _inherit = "purchase.requisition"

    opportunity_id = fields.Many2one('crm.lead', string='Opportunity')
    sale_order_id = fields.Many2one('purchase.requisition', string='Sale Reference')
