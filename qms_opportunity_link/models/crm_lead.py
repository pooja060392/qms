# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class CrmLead(models.Model):
    _inherit = "crm.lead"

    @api.depends('invoice_ids')
    def _compute_invoice_count(self):
        for lead in self:
            nbr = 0
            for order in lead.invoice_ids:
                nbr += 1
            lead.invoice_count = nbr

    @api.depends('picking_ids')
    def _compute_picking_count(self):
        for lead in self:
            nbr = 0
            for order in lead.picking_ids:
                nbr += 1
            lead.picking_count = nbr

    @api.depends('move_ids')
    def _compute_move_count(self):
        for lead in self:
            nbr = 0
            for order in lead.move_ids:
                nbr += 1
            lead.move_count = nbr

    invoice_ids = fields.One2many('account.invoice', 'lead_id', string='Invoice')
    picking_ids = fields.One2many('stock.picking', 'lead_id', string='Picking')
    move_ids = fields.One2many('account.move', 'lead_id', string='Account Moves')
    lead_flow = fields.Boolean('Flow Followed', copy=False, index=True, default=True)
    invoice_count = fields.Integer(compute='_compute_invoice_count',
                                        string="Number of Invoices", store=True)
    picking_count = fields.Integer(compute='_compute_picking_count',
                                   string="Number of Pickings", store=True)
    move_count = fields.Integer(compute='_compute_move_count',
                                   string="Number of Accounting Moves", store=True)
