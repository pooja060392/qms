from odoo import api, fields, models,_
from odoo.exceptions import UserError

class ConfirmGCRM(models.TransientModel):
    _name = 'confirm.gcrm.order'

    exporters_ref = fields.Char("Exporters Ref")
    buyer_order_no = fields.Char("Buyers Order No.")
    pre_carriage_by = fields.Char("Pre Carriage By")
    place_of_receipt = fields.Char("Place Of Receipt By Pr-Carrier")
    vessel_flight_no = fields.Char("Vessel/Flight NO.")
    port_of_loading = fields.Char("Port Of Loading")
    port_of_dise = fields.Char("Port Of Dise")
    final_destn = fields.Char("Final Dest.")
    terms_of_payments = fields.Char("Terms Of Delivery Of Payments")
    marks_no = fields.Char("Marks & No.")
    kind_of_pkgs = fields.Char("No & Kind Of Pkgs.")
    des_of_goods = fields.Char("Des.Of Goods")
    container_no = fields.Char("Container No.")
    origin = fields.Char("Origin")
    destination = fields.Char("Destination")
    book_no = fields.Char('Book Number')
    po_receipt_date = fields.Date('PO Receipt Date')
    submitted_date = fields.Date('Submitted Date')
    submitted_to = fields.Char('Submitted To')
    courier_no = fields.Char('Courier No.')
    courier_name = fields.Char('Courier Name')
    inv_date = fields.Date('Invoice Date')
    inv_number = fields.Char('Invoice Number')



    def gcrm_order_confirm(self):
        # context = dict(self._context or {})
        lst = []
        active_ids = self.env.context.get('active_ids')
        batch_pik = self.env['stock.picking.batch']
        sales = self.env['sale.order'].browse(active_ids)
        if sales:
            for record in sales:
                record.related_sale_ids = [(6, 0, active_ids)]
                if record.sale_type != 'gcrm':
                    raise UserError(_('GCRM Order you can confirm !!!'))
                if record.sale_type == 'gcrm':
                    if record.state not in ('draft', 'sent'):
                        raise UserError(_('Only draft and sent order you can confirm !!!'))
                    else:
                        record.write({'courier_no': self.courier_no,
                                      'courier_name': self.courier_name,
                                      'inv_date': self.inv_date,
                                      'inv_number': self.inv_number,
                                      'book_no': self.book_no,
                                      'exporters_ref': self.exporters_ref,
                                      'buyer_order_no': self.buyer_order_no,
                                      'pre_carriage_by': self.pre_carriage_by,
                                      'place_of_receipt': self.place_of_receipt,
                                      'vessel_flight_no': self.vessel_flight_no,
                                      'port_of_loading': self.port_of_loading,
                                      'port_of_dise': self.port_of_dise,
                                      'final_destn': self.final_destn,
                                      'terms_of_payments': self.terms_of_payments,
                                      'marks_no': self.marks_no,
                                      'kind_of_pkgs': self.kind_of_pkgs,
                                      'des_of_goods': self.des_of_goods,
                                      'container_no': self.container_no,
                                      'origin': self.origin,
                                      'destination': self.destination,
                                      'submitted_to': self.submitted_to,
                                      'submitted_date': self.submitted_date})
                        record.action_confirm()
                        if record.delivery_order_line:
                            lst.append(record.delivery_order_line)
            if lst:
                batch_id = batch_pik.create({'user_id': record.warehouse_id.user_id.id})
                for pick in lst:
                    pick.write({'batch_id': batch_id.id})


