from odoo import api, fields, models, _
from lxml import etree
from datetime import datetime
from num2words import num2words
from odoo.exceptions import UserError


class AccountInvoice(models.Model):
    _name = 'account.invoice'
    _inherit = 'account.invoice'

    lead_id = fields.Many2one('crm.lead', string='Opportunity', copy=False, index=True)
    lead_flow = fields.Boolean('Flow Followed', copy=False, index=True, default=False)

    @api.multi
    def action_move_create(self):
        res = super(AccountInvoice, self).action_move_create()
        for invoice in self:
            if invoice.type in ('out_invoice', 'out_refund'):
                if invoice.move_id:
                    invoice.move_id.update({
                        'lead_id': invoice.lead_id.id,
                        'lead_flow': invoice.lead_flow
                    })
        return res