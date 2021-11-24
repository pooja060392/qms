from odoo import api, fields, models, _
import odoo.addons.decimal_precision as dp


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    hsn_id = fields.Many2one('hsn.master','HSN No')

    @api.depends('price_unit', 'product_uom_qty', 'tax_id.tax_type', 'tax_id.type_tax_use','discount')
    def _compute_gst(self):
        cgst_rate = 0
        sgst_rate = 0
        igst_rate = 0

        for rec in self:
            cgst_total = 0
            sgst_total = 0
            igst_total = 0
            for line in rec.tax_id:
                if line.tax_type == 'cgst' and line.type_tax_use == 'sale':
                    cgst_total = cgst_total + line.amount
                if line.tax_type == 'sgst' and line.type_tax_use == 'sale':
                    sgst_total = sgst_total + line.amount
                if line.tax_type == 'igst' and line.type_tax_use == 'sale':
                    igst_total = igst_total + line.amount
                if line.tax_type == 'cgst' and line.type_tax_use == 'purchase':
                    cgst_total = cgst_total + line.amount
                if line.tax_type == 'sgst' and line.type_tax_use == 'purchase':
                    sgst_total = sgst_total + line.amount
                if line.tax_type == 'igst' and line.type_tax_use == 'purchase':
                    igst_total = igst_total + line.amount
                cgst_rate = cgst_total/100
                sgst_rate = sgst_total/100
                igst_rate = igst_total/100

            base = rec.price_unit * (1 - (rec.discount or 0.0) / 100.0)
            rec.cgst = (base * rec.product_uom_qty) * cgst_rate
            rec.sgst = (base * rec.product_uom_qty) * sgst_rate
            rec.igst = (base * rec.product_uom_qty) * igst_rate
            rec.amount = (base * rec.product_uom_qty) + rec.cgst + rec.sgst + rec.igst

    cgst = fields.Float(string='CGST', compute='_compute_gst', store=True, digits=dp.get_precision('Product Price'))
    sgst = fields.Float(string='SGST', compute='_compute_gst', digits=dp.get_precision('Product Price'))
    igst = fields.Float(string='IGST', compute='_compute_gst', digits=dp.get_precision('Product Price'))
    amount = fields.Float(string='Amt. with Taxes', readonly=True, compute='_compute_gst', digits=dp.get_precision('Product Price'))


    @api.onchange('product_id')
    def product_id_change(self):
        if not self.product_id:
            return {'domain': {'product_uom': []}}

        vals = {}
        domain = {'product_uom': [('category_id', '=', self.product_id.uom_id.category_id.id)]}
        if not self.product_uom or (self.product_id.uom_id.id != self.product_uom.id):
            vals['product_uom'] = self.product_id.uom_id
            vals['product_uom_qty'] = 1.0

        product = self.product_id.with_context(
            lang=self.order_id.partner_id.lang,
            partner=self.order_id.partner_id.id,
            quantity=vals.get('product_uom_qty') or self.product_uom_qty,
            date=self.order_id.date_order,
            pricelist=self.order_id.pricelist_id.id,
            uom=self.product_uom.id
        )

        result = {'domain': domain}

        title = False
        message = False
        warning = {}
        if product.sale_line_warn != 'no-message':
            title = _("Warning for %s") % product.name
            message = product.sale_line_warn_msg
            warning['title'] = title
            warning['message'] = message
            result = {'warning': warning}
            if product.sale_line_warn == 'block':
                self.product_id = False
                return result

        name = product.name_get()[0][1]
        if product.description_sale:
            name += '\n' + product.description_sale
        vals['name'] = name

        if self.order_id.partner_id.country_id.name == 'India':
            self._compute_tax_id()

        if self.order_id.pricelist_id and self.order_id.partner_id:
            vals['price_unit'] = self.env['account.tax']._fix_tax_included_price_company(
                self._get_display_price(product), product.taxes_id, self.tax_id, self.company_id)
        self.update(vals)

        if self.product_id.hsn_code:
            for line in self:
                # NEHA: update hsn no.. before customer selection
                line.hsn_id = line.product_id.hsn_code and line.product_id.hsn_code.id
                if line.order_id.partner_id.country_id.name == 'India':
                    branch_state = line.order_id.company_id.state_id
                    partner_state = line.order_id.partner_id.state_id
                    invoice_addres_id = line.order_id.partner_invoice_id.state_id
                    sale_tax = []
                    sale_tax2 = []
                    # line.hsn_id = line.product_id.hsn_code and line.product_id.hsn_code.id
                    if line.product_id.hsn_code:
                        hsn_code = line.product_id.hsn_code
                        if invoice_addres_id:
                            if branch_state == invoice_addres_id:
                                sale_tax.append(hsn_code.cgst_sale.id)
                                sale_tax.append(hsn_code.sgst_sale.id)
                                line.tax_id = sale_tax
                            else:
                                sale_tax2.append(hsn_code.igst_sale.id)
                                line.tax_id = sale_tax2
                        if not invoice_addres_id:
                            if branch_state == partner_state:
                                sale_tax.append(hsn_code.cgst_sale.id)
                                sale_tax.append(hsn_code.sgst_sale.id)
                                line.tax_id = sale_tax
                            else:
                                sale_tax2.append(hsn_code.igst_sale.id)
                                line.tax_id = sale_tax2

        if self.order_id.partner_id.country_id.name == 'India':
            if not self.product_id.hsn_code:
                return {
                    'warning': {
                        'title': _('Warning'),
                        'message': _('Please select HSN Code in \
                                    Product for GST calculation.'), }
                }
        return result


class SaleOrder(models.Model):
    _inherit = 'sale.order'


    def write(self, values):
        purchase_lines = self.env['sale.order.line'].search(
            [('order_id', '=', self.id)]
        )
        if self.partner_id.country_id.name == 'India':
            if self.partner_id:
                branch_state = self.company_id.state_id
                partner_state = self.partner_id.state_id
                invoice_addres_id = self.partner_invoice_id.state_id
                if purchase_lines:
                    for line in purchase_lines:
                        if line.product_id.hsn_code:
                            tax = []
                            tax2 = []
                            hsn_code = line.product_id.hsn_code
                            line.hsn_id = line.product_id.hsn_code and line.product_id.hsn_code.id
                            if invoice_addres_id:
                                if branch_state == invoice_addres_id:
                                    tax.append(hsn_code.cgst_sale.id)
                                    tax.append(hsn_code.sgst_sale.id)
                                    line.tax_id = tax
                                else:
                                    tax2.append(hsn_code.igst_sale.id)
                                    line.tax_id = tax2
                            if not invoice_addres_id:
                                if branch_state == partner_state:
                                    tax.append(hsn_code.cgst_sale.id)
                                    tax.append(hsn_code.sgst_sale.id)
                                    line.tax_id = tax
                                else:
                                    tax2.append(hsn_code.igst_sale.id)
                                    line.tax_id = tax2
        return super(SaleOrder, self).write(values)
