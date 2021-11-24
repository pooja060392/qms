from odoo.exceptions import UserError, AccessError
from odoo.tools import float_is_zero, float_compare, DEFAULT_SERVER_DATETIME_FORMAT
from collections import defaultdict
from datetime import datetime
from dateutil.relativedelta import relativedelta
from odoo.tools.misc import split_every
from psycopg2 import OperationalError
from odoo import api, fields, models, registry, _
from odoo.osv import expression
from datetime import timedelta
import odoo.addons.decimal_precision as dp

class ProcurementRule(models.Model):
    _inherit = 'procurement.rule'


    def _run_manufacture(self, product_id, product_qty, product_uom, location_id, name, origin, values):
        ''' Method inherit for stop create MO from sample type sale oder'''
        Production = self.env['mrp.production']
        ProductionSudo = Production.sudo().with_context(force_company=values['company_id'].id)
        bom = self._get_matching_bom(product_id, values)
        if not bom:
            msg = _(
                'There is no Bill of Material found for the product %s. Please define a Bill of Material for this product.') % (
                  product_id.display_name,)
            raise UserError(msg)

        # create the MO as SUPERUSER because the current user may not have the rights to do it (mto product launched by a sale for example)
        sale_id = self.env['sale.order'].search([('name', '=', origin)],limit=1)
        production_pack_id = self.env['prod.pack.line']
        if sale_id.sale_type == 'sale':
            production = ProductionSudo.create(
                self._prepare_mo_vals(product_id, product_qty, product_uom, location_id, name, origin, values, bom))
            if sale_id.packing_line:
                for line in sale_id.packing_line:
                    production_pack_id.create({
                                               'prod_pack_id': production.id,
                                               'product_id': line.product_id.id,
                                               'type': line.type,
                                               'size': line.size,
                                               'price': line.price})
        origin_production = values.get('move_dest_ids') and values['move_dest_ids'][
            0].raw_material_production_id or False
        orderpoint = values.get('orderpoint_id')
        if orderpoint:
            production.message_post_with_view('mail.message_origin_link',
                                              values={'self': production, 'origin': orderpoint},
                                              subtype_id=self.env.ref('mail.mt_note').id)
        if origin_production:
            production.message_post_with_view('mail.message_origin_link',
                                              values={'self': production, 'origin': origin_production},
                                              subtype_id=self.env.ref('mail.mt_note').id)
        return True

    def _prepare_mo_vals(self, product_id, product_qty, product_uom, location_id, name, origin, values, bom):
        warehouse_id = self.env['stock.warehouse'].search([('company_id', '=', self.company_id.id)])
        sale_id = self.env['sale.order'].search([('name', '=', origin)], limit=1)
        delivery_date = datetime.strptime(sale_id.delivery_date, "%Y-%m-%d")
        date_deadline = delivery_date - timedelta(sale_id.shiping_day)
        return {
            'origin': origin,
            'product_id': product_id.id,
            'product_qty': product_qty,
            'product_uom_id': product_uom.id,
            'location_src_id': warehouse_id.manu_type_id.default_location_dest_id.id,
            'location_dest_id': warehouse_id.manu_type_id.default_location_dest_id.id,
            'bom_id': bom.id,
            'sale_id': sale_id.id,
            'date_planned_finished': date_deadline,
            'delivery_date': sale_id.delivery_date,
            'date_planned_start': fields.Datetime.to_string(self._get_date_planned(product_id, values)),
            # 'date_planned_finished': values['date_planned'],
            'procurement_group_id': values.get('group_id').id if values.get('group_id', False) else False,
            'propagate': self.propagate,
            'picking_type_id': warehouse_id.manu_type_id.id,
            'company_id': values['company_id'].id,
            'move_dest_ids': values.get('move_dest_ids') and [(4, x.id) for x in values['move_dest_ids']] or False,
        }



class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    sale_id = fields.Many2one('sale.order','Sale Ref')