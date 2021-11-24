# -*- coding: utf-8 -*-
##############################################################################
#
#    India-GST
#
#    Merlin Tecsol Pvt. Ltd.
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
from datetime import datetime
from odoo import api, fields, models, _
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
import odoo.addons.decimal_precision as dp
from odoo.exceptions import Warning


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    hsn_id = fields.Many2one('hsn.master', 'HSN/SAC')


    @api.depends(
        'price_unit',
        'product_qty',
        'taxes_id.tax_type',
        'taxes_id.type_tax_use'
    )
    def _compute_gst(self):
        cgst_rate = 0
        sgst_rate = 0
        igst_rate = 0
        for rec in self:
            cgst_total = 0
            sgst_total = 0
            igst_total = 0
            for line in rec.taxes_id:
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
            rec.cgst = (rec.price_unit * rec.product_qty) * cgst_rate
            rec.sgst = (rec.price_unit * rec.product_qty) * sgst_rate
            rec.igst = (rec.price_unit * rec.product_qty) * igst_rate
            rec.amount = (rec.price_unit * rec.product_qty) + rec.cgst + rec.sgst + rec.igst

    cgst = fields.Float(string='CGST', compute='_compute_gst', digits=dp.get_precision('Product Price'))
    sgst = fields.Float(string='SGST', compute='_compute_gst', digits=dp.get_precision('Product Price'),)
    igst = fields.Float(string='IGST', compute='_compute_gst', digits=dp.get_precision('Product Price'),)
    amount = fields.Float(string='Amt. with Taxes', readonly=True, compute='_compute_gst', digits=dp.get_precision('Product Price'))

    @api.onchange('product_id')
    def onchange_product_id(self):
        result = {}
        if not self.product_id:
            return result
        # Reset date, price and quantity since _onchange_quantity will provide default values
        self.date_planned = datetime.today().strftime(
            DEFAULT_SERVER_DATETIME_FORMAT
        )
        self.price_unit = self.product_qty = 0.0
        self.product_uom = self.product_id.uom_po_id or self.product_id.uom_id
        result['domain'] = {'product_uom': [
            ('category_id', '=', self.product_id.uom_id.category_id.id)
        ]}
        product_lang = self.product_id.with_context({
            'lang': self.partner_id.lang,
            'partner_id': self.partner_id.id,
        })
        if self.order_id.partner_id.country_id.name == 'India':
            if self.order_id.partner_id:
                self.name = product_lang.display_name
                if product_lang.description_purchase:
                    self.name += '\n' + product_lang.description_purchase
                branch_state = self.order_id.company_id.state_id
                partner_state = self.order_id.partner_id.state_id
                if self.product_id.hsn_code:
                    tax = []
                    tax2 = []
                    hsn_code = self.product_id.hsn_code
                    tax2.append(hsn_code.igst_purchase.id)
                    self.taxes_id = tax2
                    self.hsn_id = self.product_id.hsn_code and self.product_id.hsn_code.id
                    if branch_state and partner_state:
                        if branch_state == partner_state:
                            tax.append(hsn_code.cgst_purchase.id)
                            tax.append(hsn_code.sgst_purchase.id)
                            self.taxes_id = tax
            if not self.product_id.hsn_code:
                if not self.product_id:
                    return result
                self.date_planned = datetime.today().strftime(
                    DEFAULT_SERVER_DATETIME_FORMAT
                )
                self.price_unit = self.product_qty = 0.0
                self.product_uom = self.product_id.uom_po_id or self.product_id.uom_id
                result['domain'] = {'product_uom': [
                    ('category_id', '=', self.product_id.uom_id.category_id.id)
                ]}
                product_lang = self.product_id.with_context({
                    'lang': self.partner_id.lang,
                    'partner_id': self.partner_id.id,
                })
                return {
                    'warning': {'title': _('Warning'), 'message': _('Please select HSN Code in \
                                            Product for GST calculation.'), },
                }
        self._suggest_quantity()
        self._onchange_quantity()
        return result


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'


    # @api.onchange('branch_id')
    # def onchange_branch_id(self):
    #     for line in self.order_line:
    #         if self.partner_id:
    #             branch_state = self.branch_id.state_id
    #             partner_state = self.partner_id.state_id
    #             if line.product_id.hsn_code:
    #                 tax = []
    #                 tax2 = []
    #                 hsn_code = line.product_id.hsn_code
    #                 tax2.append(hsn_code.igst_purchase.id)
    #                 line.taxes_id = tax2
    #                 line.hsn_id = line.product_id.hsn_code and line.product_id.hsn_code.id
    #                 if branch_state and partner_state:
    #                     if branch_state == partner_state:
    #                         tax.append(hsn_code.cgst_purchase.id)
    #                         tax.append(hsn_code.sgst_purchase.id)
    #                         line.taxes_id = tax


    def write(self, values):
        purchase_lines = self.env['purchase.order.line'].search(
            [('order_id', '=', self.id)]
        )
        if self.partner_id.country_id.name == 'India':
            if self.partner_id:
                branch_state = self.company_id.state_id
                # branch_state = self.branch_id.state_id
                partner_state = self.partner_id.state_id
                if purchase_lines:
                    for line in purchase_lines:
                        if line.product_id.hsn_code:
                            tax = []
                            tax2 = []
                            hsn_code = line.product_id.hsn_code
                            line.hsn_id = line.product_id.hsn_code and line.product_id.hsn_code.id
                            if branch_state and partner_state:
                                if branch_state == partner_state:
                                    tax.append(hsn_code.cgst_purchase.id)
                                    tax.append(hsn_code.sgst_purchase.id)
                                    line.taxes_id = tax
                                else:
                                    tax2.append(hsn_code.igst_purchase.id)
                                    line.taxes_id = tax2
        return super(PurchaseOrder, self).write(values)
