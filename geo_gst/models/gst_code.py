from odoo import api, fields, models, _
import odoo.addons.decimal_precision as dp
import re


class AccountTax(models.Model):
    _inherit = 'account.tax'

    tax_type = fields.Selection([
        ('cgst', 'CGST'),
        ('sgst', 'SGST'),
        ('igst', 'IGST'),
        ('frieght', 'Freight')
    ], string="Tax Type")



class PortCode(models.Model):
    _name = 'port.code'

    name = fields.Char('Port Name')
    code = fields.Char('Port Code')


class Partner(models.Model):
    _inherit = 'res.partner'

    def _default_country(self):
        return self.env['res.country'].search([('name', '=', 'India')], limit=1)

    cin_no = fields.Char('CIN', help='Customer Identification Number')
    pan_no = fields.Char('PAN', help='PAN Number')
    country_id = fields.Many2one('res.country', default=_default_country)
    gstin_registered = fields.Boolean('GSTIN-Registered')
    gstin = fields.Char('GSTIN')
    numbers = fields.Char('G Number')
    e_commerce = fields.Boolean('E-Commerce')
    e_commerce_tin = fields.Char('E-Commerce GSTIN')

    @api.onchange('state_id')
    def onchange_state_id(self):
        obj1 = self.env['account.fiscal.position'].search([('name', '=', 'Intra State')], limit=1)
        obj2 = self.env['account.fiscal.position'].search([('name', '=', 'Inter State')], limit=1)
        for data in self:
            if data.state_id:
                if data.env.user.company_id.state_id.id == data.state_id.id:
                    data.property_account_position_id = obj1.id
                else:
                    data.property_account_position_id = obj2.id

    @api.onchange('country_id')
    def onchange_country_id(self):
        obj = self.env['account.fiscal.position'].search([('name', '=', 'Export')], limit=1)
        for data in self:
            for rec in obj:
                if data.country_id:
                    if data.country_id.name != 'India':
                        data.property_account_position_id = rec.id
                    else:
                        data.property_account_position_id = ""


class Product(models.Model):
    _inherit = 'product.template'

    hsn_code = fields.Many2one('hsn.master','HSN Code', company_dependent=True, track_visibility='onchange')
    hsn_code_new = fields.Many2one('hsn.master', 'HSN Code', track_visibility='onchange')
    image_url = fields.Char('Image', readonly=True, track_visibility='onchange')
    cgst_sale = fields.Many2one('account.tax', "CGST", related='hsn_code.cgst_sale', readonly=True)
    sgst_sale = fields.Many2one('account.tax', "SGST", related='hsn_code.sgst_sale', readonly=True)
    cgst_purchase = fields.Many2one('account.tax', "CGST", related='hsn_code.cgst_purchase', readonly=True)
    sgst_purchase = fields.Many2one('account.tax', "SGST", related='hsn_code.sgst_purchase', readonly=True)
    igst_sale = fields.Many2one('account.tax', "IGST", related='hsn_code.igst_sale', readonly=True)
    igst_purchase = fields.Many2one('account.tax', "IGST", related='hsn_code.igst_purchase', readonly=True)

class CountryState(models.Model):
    _description = "Country state"
    _inherit = 'res.country.state'

    state_code = fields.Char('Code', help='Numeric State Code ')


class AccountMove(models.Model):
    _inherit = 'account.move'

    elec_ref = fields.Char('Electronic Reference')
    gstin=fields.Char(related='partner_id.gstin',store=True)
    invoice_type=fields.Selection([
        ('Regular', 'Regular'),
        ('SEZ supplies with payment', 'SEZ supplies with payment'),
        ('SEZ supplies without payment', 'SEZ supplies without payment'),
        ('Deemed Export','Deemed Export')
    ],string="Invoice Type", default='Regular', required=True)
    e_commerce_operator = fields.Many2one('res.partner','E-Commerce Operator')
    ship_bill_date = fields.Date('Shipping Bill Date')
    ship_bill_no = fields.Char('Shipping Bill No.')
    port_code = fields.Many2one('port.code')
    export_invoice = fields.Boolean('Export Invoice')
    export_type = fields.Selection([
        ('WPAY', 'WPAY'),
        ('WOPAY', 'WOPAY')
    ])
    flag_field = fields.Boolean('Flag')


    @api.onchange('partner_id')
    def partner_id_flag(self):
        if self.partner_id.gstin_registered is True:
            self.flag_field = True
        else:
            False


    @api.onchange('branch_id')
    def onchange_branch_id(self):
        for line in self.invoice_line_ids:
            if self.partner_id:
                branch_state = self.branch_id.state_id
                partner_state = self.partner_id.state_id
                if line.product_id.hsn_code:
                    tax = []
                    tax2 = []
                    hsn_code = line.product_id.hsn_code
                    if self.type in ['in_invoice', 'in_refund']:
                        tax2.append(hsn_code.igst_purchase.id)
                        line.invoice_line_tax_ids = tax2
                        line.hsn_id = line.product_id.hsn_code and line.product_id.hsn_code.id
                        if branch_state and partner_state:
                            if branch_state == partner_state:
                                tax.append(hsn_code.cgst_purchase.id)
                                tax.append(hsn_code.sgst_purchase.id)
                                line.invoice_line_tax_ids = tax
                    if self.type in ['out_invoice', 'out_refund']:
                        tax2.append(hsn_code.igst_sale.id)
                        line.invoice_line_tax_ids = tax2
                        line.hsn_id = line.product_id.hsn_code and line.product_id.hsn_code.id
                        if branch_state and partner_state:
                            if branch_state == partner_state:
                                tax.append(hsn_code.cgst_sale.id)
                                tax.append(hsn_code.sgst_sale.id)
                                line.invoice_line_tax_ids = tax


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'


    def _get_hsn_integer(self):
        res ={}
        a= re.findall(r'\d+', self.hsn_id.name)
        res = [(
            a[0])]
        return res


    # @api.depends('price_unit','discount','quantity','invoice_line_tax_ids.tax_type','invoice_line_tax_ids.type_tax_use')
    # def _compute_gst(self):
    #     cgst_rate = 0
    #     sgst_rate = 0
    #     igst_rate = 0
    #     for rec in self:
    #         cgst_total = 0
    #         sgst_total = 0
    #         igst_total = 0
    #         gst_amt = 0
    #         if rec.invoice_id.type in ['out_invoice', 'out_refund']:
    #             if not rec.invoice_line_tax_ids:
    #                 rec.tax_desc = 'none'
    #                 gst_amt = 0
    #             for line in rec.invoice_line_tax_ids:
    #                 if line.tax_type == 'cgst' and line.type_tax_use == 'sale':
    #                     cgst_total = cgst_total + line.amount
    #                     gst_amt += line.amount
    #                 if line.tax_type == 'sgst' and line.type_tax_use == 'sale':
    #                     sgst_total = sgst_total + line.amount
    #                     gst_amt += line.amount
    #                 if line.tax_type == 'igst' and line.type_tax_use == 'sale':
    #                     igst_total = igst_total + line.amount
    #                     rec.tax_desc = 'igst'
    #                     gst_amt = line.amount
    #                 if (line.tax_type == 'cgst' or line.tax_type == 'sgst') and line.type_tax_use == 'sale':
    #                     rec.tax_desc = 'gst'
    #                 cgst_rate = cgst_total / 100
    #                 sgst_rate = sgst_total / 100
    #                 igst_rate = igst_total / 100
    #         if rec.invoice_id.type in ['in_invoice', 'in_refund']:
    #             for line in rec.invoice_line_tax_ids:
    #                 if line.tax_type == 'cgst' and line.type_tax_use == 'purchase':
    #                     cgst_total = cgst_total + line.amount
    #                 if line.tax_type == 'sgst' and line.type_tax_use == 'purchase':
    #                     sgst_total = sgst_total + line.amount
    #                 if line.tax_type == 'igst' and line.type_tax_use == 'purchase':
    #                     igst_total = igst_total + line.amount
    #                     rec.tax_desc = 'igst'
    #                     gst_amt = line.amount
    #                 if (line.tax_type == 'cgst' or line.tax_type == 'sgst') and line.type_tax_use == 'purchase':
    #                     rec.tax_desc = 'gst'
    #                 cgst_rate = cgst_total / 100
    #                 sgst_rate = sgst_total / 100
    #                 igst_rate = igst_total / 100
    #         base = rec.price_unit * (1 - (rec.discount or 0.0) / 100.0)
    #         rec.cgst = (base * rec.quantity) * cgst_rate
    #         rec.sgst = (base * rec.quantity) * sgst_rate
    #         rec.igst = (base * rec.quantity) * igst_rate
    #         rec.amount = (base * rec.quantity) + rec.cgst + rec.sgst + rec.igst
    #         rec.gst_amount = gst_amt
    #         rec.gst_rate = rec.cgst + rec.sgst + rec.igst

    # cgst = fields.Float(
    #     string='CGST',
    #     compute='_compute_gst',
    #     digits=dp.get_precision('Product Price'),
    #     store=True
    # )
    # sgst = fields.Float(
    #     string='SGST',
    #     compute='_compute_gst',
    #     digits=dp.get_precision('Product Price'),
    #     store=True
    # )
    # igst = fields.Float(
    #     string='IGST',
    #     compute='_compute_gst',
    #     digits=dp.get_precision('Product Price'),
    #     store=True
    # )
    # gst_amount = fields.Float(
    #     'GST Amt.',
    #     compute='_compute_gst',
    #     store=True
    # )
    # tax_desc = fields.Char(
    #     'Tax Desc.',
    #     compute='_compute_gst',
    #     store=True
    # )
    # gst_rate = fields.Float(
    #     string='GST RATE',
    #     compute='_compute_gst',
    #     store=True
    # )
    # amount = fields.Float(
    #     string='Amt. with Taxes',
    #     readonly=True,
    #     compute='_compute_gst',
    #     store=True
    # )
    # # type_sale = fields.Many2one('invoice.type')
    hsn_id = fields.Many2one('hsn.master', 'HSN/SAC')

    @api.onchange('product_id')
    def _onchange_product_id(self):
        domain = {}
        if not self.invoice_id:
            return

        part = self.invoice_id.partner_id
        fpos = self.invoice_id.fiscal_position_id
        company = self.invoice_id.company_id
        currency = self.invoice_id.currency_id
        # type = self.invoice_id.type

        if not part:
            warning = {
                'title': _('Warning!'),
                'message': _('You must first select a partner!'),
            }
            return {'warning': warning}

        if not self.product_id:
            if type not in ('in_invoice', 'in_refund'):
                self.price_unit = 0.0
            domain['uom_id'] = []
        else:
            if part.lang:
                product = self.product_id.with_context(lang=part.lang)
            else:
                product = self.product_id

            self.name = product.partner_ref
            account = self.get_invoice_line_account(type, product, fpos, company)
            if account:
                self.account_id = account.id
            if self.invoice_id.partner_id.country_id.name == 'India':
                self._set_taxes()

            if type in ('in_invoice', 'in_refund'):
                if product.description_purchase:
                    self.name += '\n' + product.description_purchase
            else:
                if product.description_sale:
                    self.name += '\n' + product.description_sale

            if not self.uom_id or product.uom_id.category_id.id != self.uom_id.category_id.id:
                self.uom_id = product.uom_id.id
            domain['uom_id'] = [('category_id', '=', product.uom_id.category_id.id)]

            if company and currency:
                if company.currency_id != currency:
                    self.price_unit = self.price_unit * currency.with_context(
                        dict(self._context or {}, date=self.invoice_id.date_invoice)).rate

                if self.uom_id and self.uom_id.id != product.uom_id.id:
                    self.price_unit = product.uom_id._compute_price(self.price_unit, self.uom_id)

        if self.invoice_id.partner_id and self.invoice_id.partner_id.country_id.name == 'India':
            # branch_state = self.invoice_id.branch_id.state_id
            partner_state = self.invoice_id.partner_id.state_id
            if self.product_id.hsn_code:
                tax = []
                tax2 = []
                hsn_code = self.product_id.hsn_code
                if self.invoice_id.type == 'in_invoice':
                    tax2.append(hsn_code.igst_purchase.id)
                    self.invoice_line_tax_ids = tax2
                    self.hsn_id = self.product_id.hsn_code and self.product_id.hsn_code.id
                    # if branch_state and partner_state:
                    #     if branch_state == partner_state:
                    #         tax.append(hsn_code.cgst_purchase.id)
                    #         tax.append(hsn_code.sgst_purchase.id)
                    #         self.invoice_line_tax_ids = tax
                if self.invoice_id.type == 'out_invoice':
                    tax2.append(hsn_code.igst_sale.id)
                    self.invoice_line_tax_ids = tax2
                    self.hsn_id = self.product_id.hsn_code and self.product_id.hsn_code.id
                    # if branch_state and partner_state:
                    #     if branch_state == partner_state:
                    #         tax.append(hsn_code.cgst_sale.id)
                    #         tax.append(hsn_code.sgst_sale.id)
                    #         self.invoice_line_tax_ids = tax
            if not self.product_id.hsn_code:
                # raise Warning(_('Please select HSN Code in Product for GST calculation.'))
                self.product_id = self.product_id
                # self.account_id = self.account.id
                if not self.product_id:
                    if type not in ('in_invoice', 'in_refund'):
                        self.price_unit = 0.0
                    domain['uom_id'] = []
                else:
                    if part.lang:
                        product = self.product_id.with_context(lang=part.lang)
                    else:
                        product = self.product_id

                    self.name = product.partner_ref
                    account = self.get_invoice_line_account(type, product, fpos, company)
                    if account:
                        self.account_id = account.id
                    if self.invoice_id.partner_id.country_id.name == 'India':
                        self._set_taxes()

                    if type in ('in_invoice', 'in_refund'):
                        if product.description_purchase:
                            self.name += '\n' + product.description_purchase
                    else:
                        if product.description_sale:
                            self.name += '\n' + product.description_sale

                    if not self.uom_id or product.uom_id.category_id.id != self.uom_id.category_id.id:
                        self.uom_id = product.uom_id.id
                    domain['uom_id'] = [('category_id', '=', product.uom_id.category_id.id)]

                    if company and currency:
                        if company.currency_id != currency:
                            self.price_unit = self.price_unit * currency.with_context(
                                dict(self._context or {}, date=self.invoice_id.date_invoice)).rate

                        if self.uom_id and self.uom_id.id != product.uom_id.id:
                            self.price_unit = product.uom_id._compute_price(self.price_unit, self.uom_id)
                    return {
                        'warning': {'title': _('Warning'), 'message': _('Please select HSN Code in \
                            Product for GST calculation.'), },
                    }
        return {'domain': domain}