
from odoo import fields, models, api

# NEHA : add object, from qms account modulue
class HsnLine(models.Model):
    _name = 'hsn.line'

    sale_hsn_line_id = fields.Many2one()
    hsn_id = fields.Many2one('hsn.master', 'HSN Code')
    igst = fields.Float('IGST')
    cgst = fields.Float('CGST')
    sgst = fields.Float('SGST')
    tax_ids = fields.Many2many('account.tax','acount_tax_rel','line_id','tax_id','Tax')
    company_id = fields.Many2one('res.company', 'Company',
                                 default=lambda self: self.env['res.company']._company_default_get('hsn.line'))

# NEHA : inherit to add HSN lines
class SaleOrder(models.Model):
    _inherit = 'sale.order'

    hsn_line_ids = fields.One2many(comodel_name="hsn.line", inverse_name="sale_hsn_line_id",
                                    string="HSN Details", required=False, compute="_hsn_code",store=True)

    def get_tax_total(self, igst, cgst, sgst):
        return igst + cgst + sgst

    def get_taxable_value(self, hsn_id):
        total = 0
        for line in self.order_line:
            if line.hsn_id == hsn_id:
                total = total + line.price_subtotal
        return total

    @api.depends('order_line.hsn_id', 'tax_customisation')
    def _hsn_code(self):
        hsn_lst = []
        sgst = cgst = igst = 0.0
        hsn = {}
        for data in self:
            for line in data.order_line:
                hsn[line.hsn_id] = hsn.get(line.hsn_id, []) + [line]
            if data.customisation is True and data.is_kit is False:
                # NEHA: add Company search also
                hsn_id = self.env['hsn.master'].search([('name', '=', data.tax_customisation),('company_id', '=',data.company_id.id)])
                print('customisatio hsn', hsn_id.name)
                invoice_line_id = self.env['sale.order.line'].search([('hsn_id', '=', hsn_id.id), ('order_id', '=', data.id)])
                print(invoice_line_id)
                for rec in invoice_line_id:
                    hsn_lst.append((0, 0, {
                        'hsn_id': hsn_id.id,
                        'tax_ids': (6, 0, rec.tax_id.ids),
                        'igst': data.customization_igst,
                        'cgst': data.customization_cgst,
                        'sgst': data.customization_sgst,
                    }))
            else:
                for key, value in hsn.items():
                    for line in value:
                        sgst = sgst + line[0].sgst
                        cgst = cgst + line[0].cgst
                        igst = igst + line[0].igst
                    hsn_lst.append((0, 0, {
                        'hsn_id': key.id,
                        'tax_ids': [(6, 0, value[0].tax_id.ids)],
                        'igst': igst,
                        'cgst': cgst,
                        'sgst': sgst,
                    }))
                sgst = 0.0
                cgst = 0.0
                igst = 0.0
            # data.hsn_line_ids = hsn_lst
            res = {'value': {'hsn_line_ids': hsn_lst}}
            return res




