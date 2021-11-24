from odoo import api, fields, models, _
from lxml import etree
from datetime import datetime
from num2words import num2words
from odoo.exceptions import UserError


class AccountMove(models.Model):
    _name = 'account.move'
    _inherit = 'account.move'

    lead_id = fields.Many2one('crm.lead', string='Opportunity', copy=False, index=True)
    lead_flow = fields.Boolean('Flow Followed', copy=False, index=True, default=False)