from odoo import api, fields, models, _
from odoo.addons import decimal_precision as dp
from odoo.exceptions import ValidationError, RedirectWarning, except_orm, AccessError, UserError


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    # NEHA: Create MSP Property dependent
    @api.model
    def create_property_msp(self):
        prod_tmpl_ids = self.env['product.template'].search([])
        dict = {}
        field_id = self.env['ir.model.fields'].search([('name', '=', 'list_price'),
                                                       ('field_description', '=', 'MSP'),
                                                       ('model_id', '=', 146)])
        for data in prod_tmpl_ids:
            if data.list_price_new:
                dict_ = {
                    'name': 'list_price',
                    'fields_id': field_id.id,
                    'res_id': 'product.template' + ',' + str(data.id),
                    # 'company_id': 3,
                    'company_id': 1,
                    'type': 'float',
                    'value_float': data.list_price_new

                }
                print(data.list_price_new)
                create_id = self.env['ir.property'].create(dict_)
                print(create_id)

    def _get_default_category_id(self):
        if self._context.get('categ_id') or self._context.get('default_categ_id'):
            return self._context.get('categ_id') or self._context.get('default_categ_id')
        category = self.env.ref('product.product_category_all', raise_if_not_found=False)
        if not category:
            category = self.env['product.category'].search([], limit=1)
        if category:
            return category.id
        else:
            err_msg = _('You must define at least one product category in order to be able to create products.')
            redir_msg = _('Go to Internal Categories')
            raise RedirectWarning(err_msg, self.env.ref('product.product_category_action_form').id, redir_msg)


    # Pooja : Update fileds to track logs
    categ_id = fields.Many2one(
        'product.category', 'Internal Category',  track_visibility='onchange',
        change_default=True, default=_get_default_category_id,
        required=True, help="Select category for the current product")

    state = fields.Selection([('draft', 'Draft'),
                              ('waiting_approval', 'Waiting for Approval'),
                              ('confirm','Approved'),('reject', 'Rejected')], default='draft',
                             track_visibility='onchange')
    customer_id = fields.Many2one('res.partner','Customer', track_visibility='onchange')
    stock_code = fields.Char('Stock Code', track_visibility='onchange')
    sku_number = fields.Char('SKU Number', track_visibility='onchange')
    is_kit = fields.Boolean('Is Kit?', track_visibility='onchange')
    # product_type = fields.Selection([('kit', 'Kit'),
    #                                  ('individual', 'Individual')],string='Product type')
    packaging_product = fields.Boolean('Packaging Product', track_visibility='onchange')
    sample_qty = fields.Float(compute="_sample_product", string='On hand Qty', track_visibility='onchange')
    stock_qty = fields.Float(compute="_stock_product", string="On hand Qty", track_visibility='onchange')
    sample_stock = fields.Boolean(track_visibility='onchange')

    # NEHA : --------- Fun for max mrp Calculation---------
    # @api.multi
    def get_mrp_price(self):
        """
        @api.depends() should contain all fields that will be used in the calculations.
        """

        for data in self:
            product_id = self.env['product.product'].search([('product_tmpl_id', '=', data.id)])
            pro_lots_ids = self.env['stock.production.lot'].search([('product_id', '=', product_id.id)])
            mrp_max = 0.0
            if pro_lots_ids:
                mrp_max = max([dv.mrp if dv.product_qty > 0 else 0 for dv in pro_lots_ids])
            data.mrp = mrp_max

        # get product lots & get Max mrp , all at once
        # product_tmp_ids = self.env['product.template'].search([])
        # for pr in product_tmp_ids:
        #     product_id = self.env['product.product'].search([('product_tmpl_id', '=', pr.id)])
        #     pro_lots_ids = self.env['stock.production.lot'].search([('product_id', '=', product_id.id)])
        #     if pro_lots_ids:
        #         mrp_max = max([dv.mrp if dv.product_qty > 0 else 0 for dv in pro_lots_ids])
        #         pr.mrp = mrp_max

    # NEHA : --------- Fun for max mrp Calculation---------
    # pro_lot_ids = fields.One2many(comodel_name="stock.production.lot", inverse_name="pro_tmpl_id", string="Lots")
    #
    # @api.onchange('qty_available', 'pro_lot_ids', 'pro_lot_ids.product_qty', 'pro_lot_ids.mrp')
    # # @api.onchange('qty_available')
    # def _onchange_qty_available(self):
    # # get product lots & get Max mrp
    #     for data in self:
    #         print('PRO', data.name)
    #         product_id = self.env['product.product'].search([('product_tmpl_id', '=', data.id)])
    #         pro_lots_ids = self.env['stock.production.lot'].search([('product_id', '=', product_id.id)])
    #         mrp_max = 0.0
    #         print('PRO', product_id)
    #         print('PRO', pro_lots_ids)
    #         if pro_lots_ids:
    #             mrp_max = max([dv.mrp if dv.product_qty > 0 else 0 for dv in pro_lots_ids])
    #         print('mrp_max', mrp_max)
    #         data.mrp = mrp_max

    # @api.model_cr
    # def init(self):

    # NEHA: Update List Price
    list_price_new = fields.Float('MSP New', default=0.0)
    list_price = fields.Float('MSP', digits=dp.get_precision('Product Price'), default=0.0, company_dependent=True)

    mrp = fields.Float('MRP', copy=False, track_visibility='onchange',)
    approved_id = fields.Many2one('res.users', 'Approved by', track_visibility='onchange')
    requested_id = fields.Many2one('res.users', 'Requested To', track_visibility='onchange')
    # default_code = fields.Char('SKU Number', index=True)
    hsn_code = fields.Many2one('hsn.master', 'HSN Code', track_visibility='onchange')
    product_brand_id = fields.Many2one(
        'product.brand',
        string='Brand',
        track_visibility='onchange'
    )
    cost_dummy = fields.Float(
        string='Product Cost', track_visibility='onchange'
    )
    standard_price2 = fields.Float('Cost', digits=dp.get_precision('Product Price'),
                                   track_visibility='onchange',
                                   help="Cost used for inactive / unapproved products")


    def stock_head_location_product(self):
        form_view_id = self.env.ref('product.product_template_only_form_view').id
        tree_view_id = self.env.ref('qms_product_management.stock_product_tree').id
        locations = self.env['stock.location'].search([('name', 'ilike', 'Stock')])
        ctx = self.env.context.copy()
        ctx['location'] = locations.ids
        value = {
            'name': _('Stock Products'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'product.template',
            'view_id': False,
            'views': [[tree_view_id, 'list'], [form_view_id, 'form']],
            'type': 'ir.actions.act_window',
            'context': ctx
        }
        return value


    def product_template_sample_product_for_sale(self):
        form_view_id = self.env.ref('product.product_template_only_form_view').id
        tree_view_id = self.env.ref('qms_product_management.sample_stock_tree').id
        locations = self.env['stock.location'].search([('name', '=', 'Sample Location')])
        ctx = self.env.context.copy()
        ctx['location'] = locations.ids
        value = {
            'name': _('Sample location product'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'product.template',
            'view_id': False,
            'views': [[tree_view_id, 'list'], [form_view_id, 'form']],
            'type': 'ir.actions.act_window',
            'context': ctx
        }
        return value

    # NEHA: Update MRP COde for scheduler
    @api.model
    def update_mrp(self):
    # get product lots & get Max mrp , all at once
        product_tmp_ids = self.env['product.template'].search([('active', '=', True)])
        for pr in product_tmp_ids:
            product_id = self.env['product.product'].search([('product_tmpl_id', '=', pr.id)])
            pro_lots_ids = self.env['stock.production.lot'].search([('product_id', '=', product_id.id)])
            if pro_lots_ids:
                mrp_max = max([dv.mrp if dv.product_qty > 0 else 0 for dv in pro_lots_ids])
                pr.mrp = mrp_max
        # price_lst = []
        # product_template_id = self.env['product.template'].search([])
        # for data in product_template_id:
        #     self._cr.execute("""select sq.id from stock_quant sq
        #         join product_product pp on pp.id = sq.product_id
        #         and pp.product_tmpl_id = %s
        #         and sq.quantity > 0.0""" % data.id)
        #     quant_id = self._cr.fetchall()
        #     for res in quant_id:
        #         quants_ = self.env['stock.quant'].search([('id', '=', res[0])])
                # if quants_.lot_id and quants_.lot_id.mrp and quants_.lot_id.mrp > 0.0:
                #     # if quants_.lot_id.mrp > 0.0:
                #     price_ = min(price_lst.append(quants_.lot_id.mrp))
                #     data.mrp = price_

    def _sample_product(self):
        total = 0.0
        for rec in self:
            location = self.env['stock.location'].search([('sample_location', '=', True)], limit=1)
            quant = self.env['stock.quant'].search([('location_id', '=', location.id),('product_id', '=', rec.name)])
            for qnt in quant:
                total = total + qnt.quantity
            rec.sample_qty = total
            total = 0.0

    def _stock_product(self):
        total = 0.0
        for rec in self:
            location = self.env['stock.location'].search([('name', 'ilike', 'Stock')])
            quant = self.env['stock.quant'].search([('location_id', 'in', location.ids),('product_id', '=', rec.name)])
            for qnt in quant:
                total = total + qnt.quantity
            rec.stock_qty = total
            total = 0.0

    # def action_open_quants(self):
    #     products = self.mapped('product_variant_ids')
    #     action = self.env.ref('stock.product_open_quants').read()[0]
    #     if self._context.get('location'):
    #         location = self.env['stock.location'].search([('id', '=', self._context.get('location'))])
    #         action['domain'] = [('product_id', 'in', products.ids),('location_id', 'in', location.ids)]
    #     else:
    #         action['domain'] = [('product_id', 'in', products.ids)]
    #     action['context'] = {'search_default_internal_loc': 1}
    #     return action


    def create_display(self):
        context = dict(self._context or {})
        active_ids = context.get('active_ids', []) or []
        product_lst = []
        sale_order = self.env['sale.order']
        for record in self.env['product.template'].browse(active_ids):
            product_lst.append((0, 0, {
                'product_id': record.id,
                'product_uom_qty': 1,
                'price_unit': record.list_price,
                'name': record.name,
                'product_uom': record.uom_id.id,
                'return_status': 'new'
            }))
            # sale_order.create({'order_line': product_lst})
        res = {
            'name': "Display order",
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'view_id': self.env.ref('qms_sale_orders.display_sale_order_form_view').id,
            'res_model': 'sale.order',
            'context': {
                'default_sale_type': 'display',
                'default_order_line': product_lst}
        }
        return res

    @api.onchange('hsn_code')
    def onchange_hsn(self):
        if self.hsn_code:
            self.supplier_taxes_id = [(6,0, self.hsn_code.igst_purchase.ids)]
            self.taxes_id = [(6, 0, self.hsn_code.igst_sale.ids)]

    @api.model
    def create(self, values):
        mto_route = self.env['stock.location.route'].search([('name', '=', 'Replenish on Order (MTO)')])
        manufacture = self.env['stock.location.route'].search([('name', '=', 'Manufacture')])
        has_group_prod_create = self.env.user.has_group('qms_product_management.group_product_create')
        if has_group_prod_create == False:
            raise UserError(_('You have not access to create product !!!'))
        if values.get('is_kit') == False:
            if 'state' in values and values['state']:
                if values['state'] == 'draft':
                    values['active'] = False
        if values.get('type') == 'product':
            values['tracking'] = 'lot'
        if values.get('is_kit') == True:
            values['active'] = True
            values['state'] = 'confirm'
            values['route_ids'] = [(4, mto_route.id), (4, manufacture.id)]
        res = super(ProductTemplate, self).create(values)
        return res


    @api.onchange('standard_price', 'standard_price2', 'active', 'company_id')
    def onchange_stand_price(self):
        sale_price = 0.0
        # NEha: remove msp config
        msp = self.env['product.msp.master'].search([('active', '=', True)], limit=1)
        if not msp:
            raise UserError(_('MSP % not Configured!!! \n Please contact Administrator!'))
        if self.active:
            if self.standard_price > 0:
                sale_price = self.standard_price + (self.standard_price * msp.name / float(100))
        else:
            if self.standard_price2 > 0:
                sale_price = self.standard_price2 + (self.standard_price2 * msp.name / float(100))
        self.list_price = sale_price


    def send_for_approval(self):
        self.write({'state': 'waiting_approval'})


    def reject(self):
        self.write({'state': 'reject'})
        template = self.env.ref('qms_product_management.reject_product_mail_template')
        action_id = self.env.ref('qms_product_management.product_template_reject').id
        params = "/web#id=%s&view_type=form&model=product.template&action=%s" % (
            self.id, action_id)
        current_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        product_url = str(current_url) + str(params)
        template.email_from = self.env.user.login
        template.email_to = self.create_uid.partner_id.email or ''
        template.body_html = template.body_html.replace('product_url', product_url)
        template.send_mail(self.id, force_send=True)
        template.body_html = template.body_html.replace(product_url, 'product_url')


    def confirm(self):
        self.write({'active': True, 'state': 'confirm', 'approved_id': self.env.user.id})
        product = self.env['product.product'].search([('product_tmpl_id', '=', self.id)])
        if product:
            product.write({'active': True})
            product.write({'standard_price': self.standard_price2, 'standard_price2': 0.0})
        template = self.env.ref('qms_product_management.approved_product_mail_template')
        action_id = self.env.ref('stock.product_template_action_product').id
        params = "/web#id=%s&view_type=form&model=product.template&action=%s" % (
            self.id, action_id)
        current_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        product_url = str(current_url) + str(params)
        template.email_from = self.env.user.login
        template.email_to = self.create_uid.partner_id.email or ''
        template.body_html = template.body_html.replace('product_url', product_url)
        template.send_mail(self.id, force_send=True)
    #     template.body_html = template.body_html.replace(product_url, 'product_url')


class ProductProduct(models.Model):
    _inherit = 'product.product'

    # NEHA: update fileds for lgs creation
    default_code = fields.Char('Internal Reference', index=True, track_visibility='onchange')


    @api.model
    def create(self, values):
        res = super(ProductProduct, self).create(values)
        has_group_prod_create = self.env.user.has_group('qms_product_management.group_product_create')
        if has_group_prod_create is False:
            raise UserError(_('You have not access to create product!!!'))
        if 'product_tmpl_id' in values and values['product_tmpl_id']:
            product_tmp = self.env['product.template'].browse(values.get('product_tmpl_id'))
            if product_tmp.is_kit is True:
                res.active = True
            if product_tmp.is_kit is False:
                res.active = False
        return res


class ProductChangeQuantity(models.TransientModel):
    _inherit = 'stock.change.product.qty'

    is_lot_tracking = fields.Boolean('Is Lot Track', compute='_compute_lot', store=True)


    @api.depends('product_tmpl_id', 'product_id')
    def _compute_lot(self):
        if self.product_tmpl_id.tracking == 'lot':
            self.is_lot_tracking = True
        else:
            self.is_lot_tracking = False

class StockQuant(models.Model):
    _inherit = 'stock.quant'

    mrp = fields.Float('MRP')

