from odoo import api, fields, models

class saleOrder(models.Model):
    _inherit = 'sale.order'

    @api.model
    def default_get(self, default_fields):
        sale_orders_line = self.env['sale.order.line']
        data = super(saleOrder, self).default_get(default_fields)
        sale_id = self.env.context.get('active_ids', [])
        crm_lead_id = self.env['crm.lead'].browse(sale_id)
        if sale_id:
            data['sale_type'] = 'sample'
        return data
