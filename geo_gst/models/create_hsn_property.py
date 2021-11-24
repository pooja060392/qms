from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError, AccessError, ValidationError


class ProductTemplate(models.Model):
    _inherit = "product.template"

    @api.model
    def create_property_hsn(self):
        prod_tmpl_ids = self.env['product.template'].search([])
        dict = {}
        field_id = self.env['ir.model.fields'].search([('name', '=', 'hsn_code'),
                                                       ('field_description', '=', 'HSN Code'),
                                                       ('model_id', '=', 146)])
        for data in prod_tmpl_ids:
            hsn_id = self.env['hsn.master'].search([('name', '=', data.hsn_code_new.name),
                                                    ('company_id', '=', 3)])
            if data.hsn_code_new:
                dict_ = {
                    'name': 'hsn_code',
                    'fields_id': field_id.id,
                    'res_id': 'product.template' + ',' + str(data.id),
                    'company_id': 3,
                    'type': 'many2one',
                    'value_reference': 'hsn.master' + ',' + str(hsn_id.id)

                }
                create_id = self.env['ir.property'].create(dict_)
                print(create_id)
