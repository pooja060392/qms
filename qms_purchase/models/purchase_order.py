from odoo import api, fields, models


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    @api.model
    def default_get(self, fields_list):
        defaults = super(PurchaseOrder, self).default_get(fields_list)
        if defaults:
            defaults['picking_type_id'] = ''
        return defaults

    po_billing_date = fields.Date('PO Billing Date')
    purchase_type = fields.Selection([('packaging', 'Packaging'),('normal', 'Normal')],string='Purchase Type')
    sale_id = fields.Many2one('sale.order','Sale Reference', copy=False)
    state = fields.Selection([
        ('draft', 'RFQ'),
        ('sent', 'RFQ Sent'),
        ('purchase', 'Purchase Order'),
        ('done', 'Locked'),
        ('cancel', 'Cancelled')
    ], string='Status', readonly=True, index=True, copy=False, default='draft', track_visibility='onchange')
    billed_amount = fields.Float("Billed Amount", compute="get_total_amount", store=True)
    cgst_total = fields.Float('CGST', compute="compute_total", store=True)
    sgst_total = fields.Float('SGST', compute="compute_total", store=True)
    igst_total = fields.Float('IGST', compute="compute_total", store=True)
    requested_id = fields.Many2one('res.users', 'Requested To')
    approved_id = fields.Many2one('res.users', 'Approved By')


    @api.onchange('order_line.sale_id','sale_id')
    def _onchange_sale_id(self):
        if not self.sale_id:
            return
        sale = self.sale_id
        self.company_id = sale.company_id.id
        self.origin = sale.name
        self.date_order = fields.Datetime.now()
        self.purchase_type = 'normal'
        order_lines = []
        for line in sale.order_line:
            name = line.name
            taxes_ids = line.product_id.supplier_taxes_id.filtered(
                lambda tax: tax.company_id == sale.company_id).ids

            product_qty = line.product_uom_qty
            price_unit = line.price_unit
            order_line_values = line._prepare_purchase_order_line_packing(
                name=name, product_qty=product_qty, price_unit=price_unit,
                taxes_ids=taxes_ids)
            order_lines.append((0, 0, order_line_values))
        self.order_line = order_lines

    @api.depends('order_line.taxes_id')
    def compute_total(self):
        cgst = sgst = igst = 0.0
        for rec in self:
            for tax in rec.order_line:
                cgst = cgst + tax.cgst
                sgst = sgst + tax.sgst
                igst = igst + tax.igst
            rec.cgst_total = cgst
            rec.sgst_total = sgst
            rec.igst_total = igst
            cgst = sgst = igst = 0.0

    @api.depends('invoice_ids')
    def get_total_amount(self):
        total_amount = 0
        for data in self:
            for i in data.invoice_ids:
                if i.state != 'cancel':
                    total_amount += i.amount_total_signed
            data.billed_amount = total_amount

    # @api.multi
    # def approve(self):
    #     template = self.env.ref('gts_qms_purchase.approved_packaging_mail')
    #     action_id = self.env.ref('purchase.purchase_form_action').id
    #     params = "/web#id=%s&view_type=form&model=purchase.order&action=%s" % (
    #         self.id, action_id)
    #     current_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
    #     po_url = str(current_url) + str(params)
    #     template.email_from = self.env.user.login
    #     template.email_to = self.create_uid.partner_id.email or ''
    #     template.body_html = template.body_html.replace('po_url', po_url)
    #     template.send_mail(self.id, force_send=True)
    #     template.body_html = template.body_html.replace(po_url, 'po_url')
    #     self.write({'approved_id': self.env.user.id})
    #     self.button_confirm()

    # @api.multi
    # def reject(self):
    #     template = self.env.ref('gts_qms_purchase.rejected_packaging_mail')
    #     action_id = self.env.ref('purchase.purchase_form_action').id
    #     params = "/web#id=%s&view_type=form&model=purchase.order&action=%s" % (
    #         self.id, action_id)
    #     current_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
    #     po_url = str(current_url) + str(params)
    #     template.email_from = self.env.user.login
    #     template.email_to = self.create_uid.partner_id.email or ''
    #     template.body_html = template.body_html.replace('po_url', po_url)
    #     template.send_mail(self.id, force_send=True)
    #     template.body_html = template.body_html.replace(po_url, 'po_url')
    #     self.write({'state': 'reject'})
    #     # self.button_cancel()

    # Update : cancel Extra shipment/picking

    def button_cancel(self):
        res = super(PurchaseOrder, self).button_cancel()
        # entra picking search  cacnel
        picking = self.env['stock.picking'].search([('name','=',self.name), ('state', '=', 'draft')], limit=1)
        picking.action_cancel()
        return res


    def button_confirm(self):
        for order in self:
            rec = {
                'partner_id': order.partner_id.id,
                'company_id': order.company_id.id,
                'location_id': order.picking_type_id.base_stock_picking_type.default_location_src_id.id,
                'location_dest_id': order.picking_type_id.base_stock_picking_type.default_location_dest_id.id,
                # 'name': order.name,
                'picking_type_id': order.picking_type_id.base_stock_picking_type.id,
                'origin': order.name,
                'po_id': order.id,
            }
            picking_create_id_ = self.env['stock.picking'].create(rec)
            for line in order.order_line:
                dict_ = {
                    'product_id': line.product_id.id,
                    'product_uom_qty': line.product_qty,
                    'product_uom': line.product_uom.id,
                    'picking_id': picking_create_id_.id,
                    'name': line.name,
                    'location_id': order.picking_type_id.base_stock_picking_type.default_location_src_id.id,
                    'location_dest_id': order.picking_type_id.base_stock_picking_type.default_location_dest_id.id,
                    # 'purchase_line_id': line.id,
                    'picking_type_id': order.picking_type_id.base_stock_picking_type.id
                }
                move_id = self.env['stock.move'].create(dict_)
            if order.state not in ['draft', 'sent','waiting_for_approval']:
                continue
            order._add_supplier_to_product()
            # Deal with double validation process
            if order.company_id.po_double_validation == 'one_step' \
                    or (order.company_id.po_double_validation == 'two_step' \
                        and order.amount_total < self.env.user.company_id.currency_id.compute(
                        order.company_id.po_double_validation_amount, order.currency_id)) \
                    or order.user_has_groups('purchase.group_purchase_manager'):
                order.button_approve()
            else:
                order.write({'state': 'to approve'})
        return True

    @api.model
    def create(self, values):
        res = super(PurchaseOrder, self).create(values)
        if 'sale_id' in values and values['sale_id'] is not False:
            res.sale_id.packaging_po_id = res.id
        return res


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    stock_code = fields.Char('Stock Code')
    lot_ids = fields.Many2many('stock.production.lot', 'purchase_lot_ref', 'purchase_line_id', 'lot_id', 'Lot')
    packaging_size = fields.Char(string="Size", required=False, )

    @api.onchange('product_id')
    def onchange_product_id(self):
        self.stock_code = self.product_id.product_tmpl_id.stock_code
        res = super(PurchaseOrderLine, self).onchange_product_id()
        return res


