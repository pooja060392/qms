from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError, AccessError, ValidationError


class HSNMaster(models.Model):
    _name = "hsn.master"

    name = fields.Char('Name/Code', required=True, default=' ')
    description = fields.Char('Description')
    product_category = fields.Many2one('product.category', "Category")
    cgst_sale = fields.Many2one('account.tax', "CGST Sale")
    sgst_sale = fields.Many2one('account.tax', "SGST Sale")
    igst_sale = fields.Many2one('account.tax', "IGST Sale")
    cgst_purchase = fields.Many2one('account.tax', "CGST Purchase")
    sgst_purchase = fields.Many2one('account.tax', "SGST Purchase")
    igst_purchase = fields.Many2one('account.tax', "IGST Purchase")
    company_id = fields.Many2one('res.company', string='Company', change_default=True,
                                 required=True)

    @api.onchange('name')
    def _compute_upper(self):
        for rec in self:
            rec.name = str(rec.name).title()


    @api.constrains('name', 'company_id')
    def _identify_same_name(self):
        for record in self:
            obj = self.search([
                ('name', '=ilike', record.name),
                ('company_id', '=', record.company_id.id),
                ('id', '!=', record.id)
            ])
            if obj:
                raise ValidationError(
                    "There is another HSN Code with the same name: %s" % record.name)

