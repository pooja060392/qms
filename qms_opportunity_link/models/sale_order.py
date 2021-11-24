from odoo import api, fields, models, _
from lxml import etree, html
from odoo.exceptions import UserError
from datetime import datetime


class SaleOrder(models.Model):
    _inherit = "sale.order"

    lead_flow = fields.Boolean('Flow Followed', copy=False, index=True, default=False)

    @api.multi
    def action_invoice_create(self, grouped=False, final=False):
        rec = super(SaleOrder, self).action_invoice_create(grouped=False, final=False)
        invoice_id = self.env['account.invoice'].search([('id', '=', rec[0])])
        invoice_id.lead_id = self.opportunity_id.id
        invoice_id.lead_flow = self.lead_flow
        return rec

    @api.multi
    def action_confirm(self):
        obj = super(SaleOrder, self).action_confirm()
        for rec in self:
            for pick in rec.picking_ids:
                pick.update({
                    'lead_id': rec.opportunity_id.id,
                    'lead_flow': rec.lead_flow,
                })
        return obj