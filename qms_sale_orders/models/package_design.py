from odoo import api, fields, models
import datetime

class PackageDesign(models.Model):
    _inherit = ['mail.thread', 'mail.activity.mixin', 'portal.mixin']
    _name = 'package.design'
    _rec_name = 'sale_id'
    _order = 'artwork_deadline asc'

    state = fields.Selection([('new','New'),
                              ('design_submit','Design Submitted'),
                              ('customer_approve','Approved By Customer'),
                              ('done','Done'),
                              ('cancel','Cancel')],default='new',track_visibility='onchange')
    sale_id = fields.Many2one('sale.order','Sale Reference',track_visibility='onchange')
    design_packing_line = fields.One2many('design.packing.line','design_id',track_visibility='onchange')
    attachment_ids = fields.Many2many('ir.attachment', 'attachment_designing_rel', 'pack_design_id', 'attachment_id',
                                      string='Design Attachment', track_visibility='onchange')
    company_id = fields.Many2one('res.company', 'Company',
                                 default=lambda self: self.env['res.company']._company_default_get('package.design'))
    datetime = fields.Date('Create Date',default=lambda self: fields.Datetime.now())
    artwork_deadline = fields.Date('Artwork Deadline')


    def write(self, values):
        res = super(PackageDesign, self).write(values)
        if 'attachment_ids' in values:
            for attchment in self.attachment_ids:
                attchment.write({
                    'res_model': 'package.design',
                    'res_id': self.id
                })
        return res


    def send_to_customer(self):
        template = self.env.ref('qms_sale_orders.notify_salperson_mail_template')
        action_id = self.env.ref('sale.action_orders').id
        params = "/web#id=%s&view_type=form&model=package.design&action=%s" % (
            self.sale_id.id, action_id
        )
        if self.sale_id:
            current_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
            design_url = str(current_url) + str(params)
            template.email_from = self.env.user.login
            template.email_to = self.sale_id.partner_id.email or ''
            template.body_html = template.body_html.replace('design_url', design_url)
            template.attachment_ids = [attach.id for attach in self.attachment_ids]
            template.send_mail(self.id, force_send=True)
        self.write({'state': 'design_submit'})
        self.sale_id.design_attchment_ids = [(6, 0, self.attachment_ids.ids)]


    def customer_approve(self):
        self.write({'state': 'customer_approve'})
        self.sale_id.design_attchment_ids = [(6, 0, self.attachment_ids.ids)]


    def done(self):
        self.write({'state': 'done'})


    def cancel(self):
        self.write({'state': 'cancel'})

class DesignPackLine(models.Model):
    _name = 'design.packing.line'

    design_id = fields.Many2one('package.design')
    product_id = fields.Many2one('product.product','Customization Name')
    type = fields.Char('Type')
    size = fields.Char('Size')
    price = fields.Float('Cost To Us/Piece')
    description = fields.Char('Description')
    quantity = fields.Float('Quantity')
    total = fields.Float('Total',compute="_compute_total",store=True)
    company_id = fields.Many2one('res.company', 'Company',
                                 default=lambda self: self.env['res.company']._company_default_get('package.design'))

    @api.depends('quantity','price')
    def _compute_total(self):
        for line in self:
            line.total = line.quantity * line.price