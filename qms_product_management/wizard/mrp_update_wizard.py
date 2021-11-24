from odoo import models, fields, api, _


class MrpUpdate(models.TransientModel):
  _name = 'mrp.update.wizard'

  mrp_update = fields.Float('MRP')
  product_id = fields.Many2one('product.template')

  @api.model
  def default_get(self, fields):
      res = super(MrpUpdate, self).default_get(fields)
      product_template_id = self.env['product.template'].browse(self.env.context.get('active_id'))
      if product_template_id:
          res['product_id'] = product_template_id.id
      return res


  def update_product_mrp(self):
      for rec in self.product_id:
          rec.mrp = self.mrp_update
