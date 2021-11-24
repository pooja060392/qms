from odoo import api, fields, models,_
import base64
from odoo.tools import float_compare, float_round
from odoo.exceptions import UserError, ValidationError
import json
import time
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from lxml import etree, html


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    sale_type = fields.Selection([('sale', 'Sale'), ('sample_gift', 'Sample/Gift'),
                                ('gift', 'Gift')], string='Sale Type')
    # paking_line = fields.One2many('packing.line','packing_id')
    sample_return = fields.Boolean('Sample Return')
    amount_returned = fields.Boolean('Amt. Returned')
    no_of_cartoon = fields.Integer('Number Of Cartons')
    shipping_tracking_number = fields.Char('Shipping Tracking Number')
    check_shiping_tracking = fields.Boolean('Check Shipping Tracking')
    shiping_tracking_status = fields.Char('Shipping Tracking Status', readonly=True)
    related_code = fields.Selection([('incoming', 'Vendors'), ('outgoing', 'Customers'), ('internal', 'Internal'),
                                     ('mrp_operation', 'Manufacturing Operation')],
                            'Type of Operation',compute="_related_picking_code", store=True)
    attachment_ids = fields.Many2many('ir.attachment', 'attachment_stock_rel', 'stock_id', 'attach_id',
                                      string='Signed Copy', track_visibility='onchange')
    courier_no = fields.Char('Courier Number')
    courier_name = fields.Char('Courier Name')
    display_return = fields.Boolean('Display Return')
    inv_date = fields.Date('Invoice Date')
    inv_number = fields.Char('Invoice Number')
    address_attachment = fields.Binary('Declaration Form')
    invoice_attachment = fields.Binary('Courier Invoice')
    file_name = fields.Char()
    file_name_address = fields.Char()
    delivery_date = fields.Date('Delivery Date')
    tracking_number = fields.Char('Tracking Number')
    transport_num = fields.Char('Transport Number')
    vehicle_no = fields.Char('Vehicle Number')
    remarks = fields.Text('Remarks')
    is_returned = fields.Boolean()
    return_picking_id = fields.Many2one('stock.picking','Return Picking ')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('waiting', 'Waiting Another Operation'),
        ('confirmed', 'Waiting'),
        ('partially_available', 'Partial Available'),
        ('assigned', 'Ready'),
        ('done', 'Done'),
        ('cancel', 'Cancelled'),
    ], string='Status', compute='_compute_state',
        copy=False, index=True, readonly=True, store=True, track_visibility='onchange',
        help=" * Draft: not confirmed yet and will not be scheduled until confirmed.\n"
             " * Waiting Another Operation: waiting for another move to proceed before it becomes automatically available (e.g. in Make-To-Order flows).\n"
             " * Waiting: if it is not ready to be sent because the required products could not be reserved.\n"
             " * Ready: products are reserved and ready to be sent. If the shipping policy is 'As soon as possible' this happens as soon as anything is reserved.\n"
             " * Done: has been processed, can't be modified or cancelled anymore.\n"
             " * Cancelled: has been cancelled, can't be confirmed anymore.")
    qc_transfer = fields.Boolean(
        'Is QC Transfer', default=False,
        copy=False, index=True, compute='_compute_qc_transfer',
        store=True
    )
    location_id = fields.Many2one(
        'stock.location', "Source Location",
        default=lambda self: self.env['stock.picking.type'].browse(
            self._context.get('default_picking_type_id')).default_location_src_id,
        readonly=True, required=True,
        states={'draft': [('readonly', False)],
                'assigned': [('readonly', False)],
                'waiting': [('readonly', False)],
                'confirmed': [('readonly', False)]
                })
    picking_type_id = fields.Many2one(
        'stock.picking.type', 'Operation Type',
        required=True,
        states={'done': [('readonly', True)], 'cancel': [('readonly', True)]})

    # Pooja: add fields
    user_id = fields.Many2one("res.users", string="Salesperson", track_visibility='onchange')

    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
        res = super(StockPicking, self).fields_view_get(
            view_id=view_id, view_type=view_type, toolbar=toolbar, submenu=submenu)
        doc = etree.XML(res['arch'])
        for node in doc.xpath("//field[@name='location_id']"):
            if 'active_id' in self._context:
                search_id = self.env['stock.picking'].search([('sale_id', '=', self._context['active_id'])])
                for data in search_id:
                    if data.related_code == 'outgoing':
                        node.set('domain', "[('usage', '=', 'internal'),"
                                           "('manufacturing_location', '!=', True),"
                                           "('quality_location', '!=', True),"
                                           "('sample_location', '!=', True)]")
            if 'id' in 'params' in self._context:
                search_id = self.env['stock.picking'].search([('sale_id', '=', self._context['params']['id'])])
                for data in search_id:
                    if data.related_code == 'outgoing':
                        node.set('domain', "[('usage', '=', 'internal'),"
                                           "('manufacturing_location', '!=', True),"
                                           "('quality_location', '!=', True),"
                                           "('sample_location', '!=', True)]")
        res['arch'] = etree.tostring(doc, encoding='unicode')
        return res

    # @api.onchange('location_id')
    # def onchange_location_id(self):
    #     picking_type_obj = self.env['stock.picking.type']
    #     warehouse_obj = self.env['stock.warehouse']
    #     for data in self:
    #         warehouse_id = warehouse_obj.search([('company_id', '=', data.company_id.id)], limit=1)
    #         search_id = picking_type_obj.search([
    #             ('default_location_src_id', '=', data.location_id.id),
    #             ('code', '=', 'outgoing'),
    #             ('warehouse_id', '=', warehouse_id.id)
    #         ], limit=1)
    #         if search_id:
    #             print(search_id)
    #             data.picking_type_id = search_id.id
    #         for rec in data.move_lines:
    #             rec.location_id = data.location_id.id
    #             if search_id:
    #                 rec.picking_type_id = search_id.id

    @api.depends('location_id')
    def _compute_qc_transfer(self):
        for rec in self:
            if rec.location_id.quality_location is True:
                rec.qc_transfer = True


    def action_assign(self):
        res = super(StockPicking, self).action_assign()
        for pick in self:
            for move in pick.move_lines:
                if move.state == 'partially_available':
                    pick.state = 'partially_available'
                    break
        return res


    def send_intimation(self):
        self.ensure_one()
        active_ids = self.env.context.get('active_ids', []) or []
        stock = self.env['stock.picking'].browse(active_ids)
        ir_model_data = self.env['ir.model.data']
        try:
            template_id = ir_model_data.get_object_reference('qms_stock_picking', 'send_intimation_mail_template')[1]
        except ValueError:
            template_id = False
        try:
            compose_form_id = ir_model_data.get_object_reference('mail', 'email_compose_message_wizard_form')[1]
        except ValueError:
            compose_form_id = False
        ctx = {
            'default_model': 'stock.picking',
            'default_res_id': self.ids[0],
            'default_use_template': bool(template_id),
            'default_template_id': template_id,
            'default_composition_mode': 'comment',
            'mark_so_as_sent': True,
            'custom_layout': 'delivery.mail_template_data_delivery_notification',
            'proforma': self.env.context.get('proforma', False),
            'force_email': True,
            'default_partner_ids': [(6,0, [self.sale_id.partner_id.id,self.sale_id.user_id.partner_id.id])]
        }
        return {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(compose_form_id, 'form')],
            'view_id': compose_form_id,
            'target': 'new',
            'context': ctx,
        }

    @api.depends('picking_type_id')
    def _related_picking_code(self):
        for rec in self:
            if rec.picking_type_id:
                rec.related_code = rec.picking_type_id.code


    # NEHA: Mail triggers to SP on Delivery Confrim

    # def action_mail_send(self):
    #     for data in self:
    #         if data.sale_id and data.user_id:
    #             # action_id = self.env.ref('qms_sale_order.action_sale_order_fill_days').id
    #             # params = "web#id=%s&view_type=form&model=sale.order&action=%s" % (
    #             #     data.id, action_id
    #             # )qty_ava
    #             # sale_url = str(params)
    #             template = self.env.ref('qms_stock_picking.delivery_mail_template')
    #             if template:
    #                 values = template.generate_email(data.id)
    #                 values['email_to'] = data.user_id.partner_id.email or data.user_id.email
    #                 values['email_from'] = self.env.user.email or self.env.user.partner_id.email
    #                 values['email_cc'] = self.env.user.email or self.env.user.partner_id.email
    #                 mail = self.env['mail.mail'].create(values)
    #                 try:
    #                     mail.send()
    #                 except Exception:
    #                     pass


    def button_validate(self):
        res = super(StockPicking, self).button_validate()
        # \NEHA: send mail to SP
        # if self.sale_id:
        #     self.action_mail_send()
        lot_lst = []
        for line in self.move_lines:

            if self.sale_type == 'sample_gift':
                if self.sample_return is True:
                    if line.quantity_done == 0.0:
                        line.sale_line_id.return_qty = line.product_uom_qty
                    else:
                        line.sale_line_id.return_qty = line.quantity_done
                if line.sale_line_id.type == 'sample':
                    line.sale_line_id.return_status = 'waiting_return'
                if line.sale_line_id.type == 'gift':
                    line.sale_line_id.return_status = 'nothing'
            if line.purchase_line_id:
                for ml in line.move_line_ids:
                    if ml.lot_id:
                        lot_lst.append(ml.lot_id.id)
                # line.purchase_line_id.lot_ids = [(6,0, lot_lst)]
                lot_lst = []
        return res


    # def button_validate(self):
    #     template = self.env.ref('qms_stock_picking.template_for_order_confirmation')
    #     # get users
    #     get_group = self.env.ref('qms_sale_order.group_order_confirmation_user')
    #     users_ids = get_group.users.filtered(lambda x: x.email)
    #     for user in users_ids:
    #         if template:
    #             values = template.generate_email(self.id)
    #             values['email_to'] = user.partner_id.email
    #             values['email_from'] = self.user_id.partner_id.email
    #             mail = self.env['mail.mail'].create(values)

    def action_generate_backorder_wizard(self):
        view = self.env.ref('stock.view_backorder_confirmation')
        wiz = self.env['stock.backorder.confirmation'].create(
            {'pick_ids': [(4, p.id) for p in self],
             'related_code': self.picking_type_id.code}
        )
        return {
            'name': _('Create Backorder?'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'stock.backorder.confirmation',
            'views': [(view.id, 'form')],
            'view_id': view.id,
            'target': 'new',
            'res_id': wiz.id,
            'context': {'default_related_code': self.picking_type_id.code},
        }



    # def action_done(self):
    #     res = super(StockPicking, self).action_done()
    #     if self.sale_type == 'sale':
    #         template = self.env.ref('qms_stock_picking.delivery_mail_template')
    #         template.email_from = self.env.user.login
    #         template.send_mail(self.id, force_send=True)
    #     return res


    def action_cancel(self):
        res = super(StockPicking, self).action_cancel()
        for picking in self:
            for line in picking.move_lines:
                if line.sale_line_id:
                    line.sale_line_id.return_status = 'cancel'
        return res

    @api.model
    def create(self, vals):
        if 'origin' in vals and vals['origin']:
            sale = self.env['sale.order'].search([('name', '=', vals['origin'])], limit=1)
            warehouse_id = self.env['stock.warehouse'].search([('company_id', '=', vals.get('company_id'))], limit=1)
            # if not warehouse_id:
            #     raise ValidationError('Warehouse not defined on Company')
            if sale:
                # Pooja: Add code for adding salespersons
                vals['user_id'] = sale.user_id.id
                if sale.sale_type == 'sale':
                    vals['delivery_date'] = sale.delivery_date or False
                    # if warehouse_id:
                    #     vals['location_id'] = warehouse_id.out_type_id.default_location_src_id.id
                if sale.sale_type == 'sample_gift':
                    type_id = warehouse_id.sample_picking_type
                    vals['picking_type_id'] = type_id.id
                    vals['location_id'] = type_id.default_location_src_id.id
                # if sale.sale_type == 'gcrm':
                #     vals['sale_type'] = sale.sale_type or False
                #     if sale.courier_no:
                #         vals['courier_no'] = sale.courier_no
                #     if sale.courier_name:
                #         vals['courier_name'] = sale.courier_name
                #     if sale.inv_date:
                #         vals['inv_date'] = sale.inv_date
                #     if sale.inv_number:
                #         vals['inv_number'] = sale.inv_number
        picking = super(StockPicking, self).create(vals)
        if 'origin' in vals:
            sale = self.env['sale.order'].search([('name', '=', vals['origin'])], limit=1)
            # if sale.sale_type == 'gcrm':
            #     address_pdf = self.env.ref('qms_sale_order.address_report').render_qweb_pdf(sale.id)
            #     pdf = self.env.ref('ms_sale_order.invoice_order_report').render_qweb_pdf(sale.id)
            #     picking.address_attachment = base64.b64encode(address_pdf[0])
            #     picking.invoice_attachment = base64.b64encode(pdf[0])
            #     picking.file_name = 'Declaration Form.pdf'
            #     picking.file_name_address = 'Invoice Courier.pdf'
            if sale.sale_type == 'sale':
                picking.scheduled_date = sale.delivery_date or False
        return picking


    def write(self, values):
        res = super(StockPicking, self).write(values)
        if 'attachment_ids' in values:
            template = self.env.ref('qms_stock_picking.signed_copy_mail_template')
            action_id = self.env.ref('stock.action_picking_tree_all').id
            params = "/web#id=%s&view_type=form&model=stock.picking&action=%s" % (
                self.id, action_id
            )
            current_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
            stock_url = str(current_url) + str(params)
            template.email_from = self.env.user.login
            if self.sale_id:
                template.email_to = self.partner_id.email or self.sale_id.user_id.partner_id.email or ''
            if not self.sale_id:
                template.email_to = self.partner_id.email or ''
            template.body_html = template.body_html.replace('_stock_url', stock_url)
            template.attachment_ids = [attach.id for attach in self.attachment_ids]
            template.send_mail(self.id, force_send=True)
        if 'attachment_ids' in values:
            for attchment in self.attachment_ids:
                attchment.write({
                    'res_model': 'stock.picking',
                    'res_id': self.id
                })
        return res

# class PackingLine(models.Model):
#     _name = 'packing.line'
#
#     packing_id = fields.Many2one('stock.picking')
#     product_id = fields.Many2one('product.product')
#     product_qty = fields.Float('Product Available Qty')
#     type = fields.Char('Type')
#     size = fields.Char('Size')
#     piece = fields.Char('Cost To Us/Piece')


class ReturnPicking(models.TransientModel):
    _inherit = 'stock.return.picking'

    # class ReturnPicking(models.TransientModel):
    #     _inherit = 'stock.return.picking'

    def _create_returns(self):
        is_valid = False
        # for i in self.product_return_moves:
        #     if i.quantity > i.stock_quantity:
        #         is_valid = False
        #         break
        #     else:
        #         is_valid = True
        # if is_valid:
        ''' Method inherit for check return sample type or sale type
        if sample return then true sample return boolean'''
        # TODO sle: the unreserve of the next moves could be less brutal
        for return_move in self.product_return_moves.mapped('move_id'):
            return_move.move_dest_ids.filtered(lambda m: m.state not in ('done', 'cancel'))._do_unreserve()

        # create new picking for returned products
        picking_type_id = self.picking_id.picking_type_id.return_picking_type_id.id or self.picking_id.picking_type_id.id
        new_picking = self.picking_id.copy({
            'move_lines': [],
            'picking_type_id': picking_type_id,
            'state': 'draft',
            'return_picking_id': self.picking_id.id,
            # 'display_return': True if self.picking_id.sale_type == 'display' else False,
            'sample_return': True if self.picking_id.sale_type == 'sample_gift' else False,
            'origin': _("Return of %s") % self.picking_id.name,
            'location_id': self.picking_id.location_dest_id.id,
            'location_dest_id': self.location_id.id,
            'is_returned': True})
        new_picking.message_post_with_view('mail.message_origin_link',
                                           values={'self': new_picking, 'origin': self.picking_id},
                                           subtype_id=self.env.ref('mail.mt_note').id)
        returned_lines = 0
        for return_line in self.product_return_moves:
            if not return_line.move_id:
                raise UserError(_("You have manually created product lines, please delete them to proceed"))
            # TODO sle: float_is_zero?
            if return_line.quantity:
                returned_lines += 1
                vals = self._prepare_move_default_values(return_line, new_picking)
                r = return_line.move_id.copy(vals)
                vals = {}

                # +--------------------------------------------------------------------------------------------------------+
                # |       picking_pick     <--Move Orig--    picking_pack     --Move Dest-->   picking_ship
                # |              | returned_move_ids              ↑                                  | returned_move_ids
                # |              ↓                                | return_line.move_id              ↓
                # |       return pick(Add as dest)          return toLink                    return ship(Add as orig)
                # +--------------------------------------------------------------------------------------------------------+
                move_orig_to_link = return_line.move_id.move_dest_ids.mapped('returned_move_ids')
                move_dest_to_link = return_line.move_id.move_orig_ids.mapped('returned_move_ids')
                vals['move_orig_ids'] = [(4, m.id) for m in move_orig_to_link | return_line.move_id]
                vals['move_dest_ids'] = [(4, m.id) for m in move_dest_to_link]
                r.write(vals)
        if not returned_lines:
            raise UserError(_("Please specify at least one non-zero quantity."))
        new_picking.action_assign()
        new_picking.action_confirm()
        return new_picking.id, picking_type_id
        # else:
        #     raise ValidationError('Quantity value is more than Stock Quantity')

        @api.model
        def default_get(self, fields):
            if len(self.env.context.get('active_ids', list())) > 1:
                raise UserError("You may only return one picking at a time!")
            res = super(ReturnPicking, self).default_get(fields)

            move_dest_exists = False
            product_return_moves = []
            picking = self.env['stock.picking'].browse(self.env.context.get('active_id'))
            if picking:
                res.update({'picking_id': picking.id})
                if picking.state != 'done':
                    raise UserError(_("You may only return Done pickings"))
                for move in picking.move_lines:
                    if move.scrapped:
                        continue
                    if move.move_dest_ids:
                        move_dest_exists = True
                    quantity = move.product_qty - sum(
                        move.move_dest_ids.filtered(
                            lambda m: m.state in ['confirmed', 'partially_available', 'assigned', 'done']). \
                            mapped('ordered_qty'))
                    quantity = float_round(quantity, precision_rounding=move.product_uom.rounding)
                    product_return_moves.append((0, 0, {'product_id': move.product_id.id, 'quantity': quantity,
                                                        'move_id': move.id, 'uom_id': move.product_id.uom_id.id,
                                                        'stock_quantity': quantity}))

                if not product_return_moves:
                    raise UserError(
                        _(
                            "No products to return (only lines in Done state and not fully returned yet can be returned)!"))
                if 'product_return_moves' in fields:
                    res.update({'product_return_moves': product_return_moves})
                if 'move_dest_exists' in fields:
                    res.update({'move_dest_exists': move_dest_exists})
                if 'parent_location_id' in fields and picking.location_id.usage == 'internal':
                    res.update({
                        'parent_location_id': picking.picking_type_id.warehouse_id and picking.picking_type_id.warehouse_id.view_location_id.id or picking.location_id.location_id.id})
                if 'original_location_id' in fields:
                    res.update({'original_location_id': picking.location_id.id})
                if 'location_id' in fields:
                    location_id = picking.location_id.id
                    if picking.picking_type_id.return_picking_type_id.default_location_dest_id.return_location:
                        location_id = picking.picking_type_id.return_picking_type_id.default_location_dest_id.id
                    res['location_id'] = location_id
            return res


class ReturnPickingLine(models.TransientModel):
    _inherit = "stock.return.picking.line"

    stock_quantity = fields.Float(string='Ordered Quantity', force_save="1")
