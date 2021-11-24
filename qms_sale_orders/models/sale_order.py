from odoo.exceptions import UserError, AccessError, ValidationError
from odoo.tools import float_is_zero, float_compare, DEFAULT_SERVER_DATETIME_FORMAT
from collections import defaultdict
from datetime import *
from datetime import date
from datetime import datetime
from dateutil.relativedelta import relativedelta
from odoo.tools.misc import split_every
from psycopg2 import OperationalError
from odoo import api, fields, models, registry, _
from odoo.osv import expression
from datetime import timedelta
import odoo.addons.decimal_precision as dp
from num2words import num2words
from datetime import datetime, timedelta, date
import calendar
from lxml import etree


class SaleOrder(models.Model):
    _inherit = 'sale.order'
    _order = "date_order desc"



    def _default_validity_date(self):
        if self.env['ir.config_parameter'].sudo().get_param('sale.use_quotation_validity_days'):
            days = self.env.company.quotation_validity_days
            if days > 0:
                return fields.Date.to_string(datetime.now() + timedelta(days))
        return False



    @api.depends('amount_total', 'kit_rate_grandtotal', 'amount_customization_total')
    def _amount_in_words(self):
        for orderamt in self:
            if orderamt.is_kit:
                orderamt.amount_to_text = num2words(orderamt.kit_rate_grandtotal, lang='en_IN')
            if orderamt.customisation and not orderamt.is_kit:
                orderamt.amount_to_text = num2words(orderamt.amount_customization_total, lang='en_IN')
            if not orderamt.is_kit and not orderamt.customisation:
                orderamt.amount_to_text = num2words(orderamt.amount_total, lang='en_IN')

    amount_to_text = fields.Text(string='In Words',
                                 store=True, readonly=True, compute='_amount_in_words')

    @api.model
    def send_get_mail_cc(self):
        # set the email field with all the recipients
        for mail_id in self.ids:
            mail = self.browse(mail_id)
            email_cc = []
            for partner in mail.recipient_ids:
                email_cc.append(partner.email)
        return email_cc
    #

    # def force_quotation_send(self):
    #     for order in self:
    #         email_act = order.action_quotation_send()
    #         if email_act and email_act.get('context'):
    #             email_ctx = email_act['context']
    #             email_ctx.update(default_email_from=order.company_id.email)
    #             order.with_context(email_ctx).message_post_with_template(email_ctx.get('default_template_id'))
    #     return True

    # @api.model
    # def _default_approval_amount(self):
    #     # return True
    #     return self.env.user.company_id.gift_approval_amount



    @api.onchange('amount_total')
    def onchange_total_amount(self):
        if any(data.price_unit < data.msp for data in self.order_line):
            self.is_msp_approval = True
            if self.state == 'approved':
                self.is_quotation_sent = False
        else:
            self.is_msp_approval = False


        # price_change_small = []
        # price_change_greater = []
        # line_total = 0.0
        # if self.sale_type == 'sample_gift':
        #     if self.user_id.is_salesperson:
        #         for line in self.order_line:
        #             if line.type == 'sample':
        #                 line_total = line_total + line.price_subtotal
        #             if line_total > self.remaining_sale_amtount:
        #                 self.need_approval = True
        # if self.sale_type == 'sale':
        #     for rec in self.order_line:
        #         if rec.price_unit:
        #             if rec.product_id:
        #                 if rec.product_id.list_price > rec.price_unit:
        #                     price_change_small.append(rec.id)
        #                 else:
        #                     price_change_greater.append(rec.id)
        #     if price_change_greater and not price_change_small:
        #         self.need_approval = False
        #         self.is_msp_approval = False
        #     if price_change_small:
        #         self.need_approval = True
        #         self.is_msp_approval = True

    @api.depends('delivery_date', 'po_date')
    def _compute_remaining_days(self):
        for sale in self:
            print('INSIDE REM COM')
            if sale.delivery_date and sale.po_date:
                print('INSIDE REM COM1', (
                            datetime.strptime(str(sale.delivery_date), '%Y-%m-%d') - datetime.strptime(str(sale.po_date), '%Y-%m-%d')))
                sale.remaining_days = (datetime.strptime(str(sale.delivery_date), '%Y-%m-%d') - datetime.strptime(str(sale.po_date), '%Y-%m-%d')).days
            else:
                sale.remaining_days = False


    # Pooja : merge this conditon with : onchange_packing_days
    # @api.onchange('remaining_days')
    # def get_so_approval(self):
    #     for data in self:
    #         print('data.remaining_days', data.remaining_days)
    #         if data.remaining_days < 0 or data.delivery_lead > data.remaining_days:
    #             data.is_so_approval = True
    #         else: # Pooja: add conditon if dates changes
    #             data.is_so_approval = False

    # NEHA : merge this conditon with : onchange_packing_days
    # @api.onchange('delivery_date', 'po_date')
    # def date_check_for_po_amendment(self):
    #     if self.po_date and self.delivery_date:
    #         delivery_date = datetime.strptime(self.delivery_date, "%Y-%m-%d")
    #         po_date = datetime.strptime(self.po_date, "%Y-%m-%d")
    #         if delivery_date < po_date:
    #             self.need_po_amendment = True
    #             # NEHA : correct warning
    #             raise UserError(_('Client%ss PO Need Amendment' %("'")))
    #             # self.need_approval = True
    #             # return {
    #             #     'warning': {'title': _('Warning'), 'message': _("Client%ss PO Need Amendment") % "'", },
    #             # }
    #         else:
    #             self.need_po_amendment = False

    # NEHA: Add Fields &


    # @api.onchange('po_date', 'delivery_date')
    # def onchange_packing_days(self):
    #     if self.sale_type == 'sale':
    #         delivery_date = po_date = ''
    #         deli_ld_time = 0
    #         if (self.po_date and self.delivery_date):
    #             delivery_date = datetime.strptime(str(self.delivery_date, "%Y-%m-%d"))
    #             po_date = datetime.strptime(str(self.po_date, "%Y-%m-%d"))
    #
    #
    #             if self.purchase_lead or self.packing_lead or self.shipping_lead: # update condition, use OR, in place of AND
    #                 deli_ld_time = self.purchase_lead + self.packing_lead + self.shipping_lead
    #             if delivery_date < po_date or deli_ld_time > self.remaining_days :
    #                 self.need_po_amendment = True
    #                 self.penalty = 'yes'
    #                 return {
    #                     'warning': {'title': _('Warning'), 'message': _("Client%ss PO Need Amendment") % "'", },
    #                 }
    #             else:
    #                 self.need_po_amendment = False
    #                 self.date_need_approval = False
    #                 self.penalty = 'no'
    #         else:
    #             self.need_po_amendment = False
    #             self.date_need_approval = False
    #             self.penalty = 'no'

    @api.onchange('customisation')
    def onchange_customasition(self):
        if self.customisation:
            pack_list = []
            customaztion_default = self.env['package.config'].search([])
            if customaztion_default:
                for line in customaztion_default.config_pack_line:
                    pack_list.append((0, 0, {
                        'product_id': line.product_id.id,
                        'customize_name': line.product_id.name,
                        'quantity': 0,
                    }))
                self.packing_line = pack_list
        if not self.customisation:
            self.artwork_need = False
            # self.write({'send_mail_to_mo': False})

    @api.model
    def is_sale_user(self):
        ''' Function to check user if it is Sales: See own Documents'''
        if self.env.user.has_group('sales_team.group_sale_salesman'):
            return True
        else:
            return False

    @api.model
    def is_sale_manager(self):
        ''' Function to check user if it is Team Leader'''
        if self.env.user.has_group('sales_team.group_sale_manager'):
            return True
        else:
            return False

    @api.model
    def is_see_all_leads(self):
        ''' Function to check user if it is See All Leads'''
        if self.env.user.has_group('sales_team.group_sale_salesman_all_leads'):
            return True
        else:
            return False

    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
        res = super(SaleOrder, self).fields_view_get(view_id=view_id, view_type=view_type,
                                                   toolbar=toolbar, submenu=submenu)
        user = self.env.user.id
        team_obj = self.env['crm.team']
        user_ids = []
        doc = etree.XML(res['arch'])
        for node in doc.xpath("//field[@name='user_id']"):
            if self.is_sale_user() == True:
                domain = [('id', 'in', [self.env.user.id])]
                node.set('domain', str(domain))
            if self.is_sale_manager() == True or self.is_see_all_leads == True:
                team_recs = team_obj.sudo().search([(('user_id', '=', self._uid))])
                if team_recs:
                    for team in team_recs:
                        user_ids += team.member_ids.ids
                user_ids.append(self._uid)
                domain = [('id', 'in', user_ids)]
                node.set('domain', str(domain))
        # for node in doc.xpath("//button[@name='action_quotation_send'][1]"):
        #     if self.customisation is True or self.is_msp_approval is True:
        #         node.set('invisible' True)
        res['arch'] = etree.tostring(doc, encoding='unicode')
        return res

    @api.onchange('user_id')
    def onchange_sale_amount_saleperson(self):
        if self.user_id:
            if self.sale_type == 'sale':
                if self.user_id.is_salesperson == True:
                    self.target_amount = self.user_id.sale_target
            if self.sale_type == 'sample_gift':
                if self.user_id.sale_amount :
                    self.sale_amt = self.user_id.sale_amount
                    self.remaining_sale_amtount = self.user_id.remaining_sale_amt
                    self.consume_sample_amt = self.user_id.used_sale_amt
                    if self.user_id.remaining_sale_amt == 0.0:
                        self.remaining_sale_amtount = self.user_id.sale_amount


    # @api.depends('delivery_order_line.state')
    def _compute_delivery_status(self):
        wait_list = []
        return_list = []
        noting_lst = []
        gift_list = []
        sample_list = []
        for rec in self:
            if not rec.order_line:
                rec.delivery_status = 'nothing_delivery'
            else:
                for val in rec.order_line:
                    if val.return_status == 'waiting_return':
                        wait_list.append(val.id)
                    if val.return_status == 'return':
                        return_list.append(val.id)
                    if val.return_status == 'nothing':
                        noting_lst.append(val.id)
                    if val.return_status in ('new','waiting_delivery','cancel'):
                        rec.delivery_status = val.return_status
                if wait_list:
                    rec.delivery_status = 'waiting_return'
                print('noting_lst', noting_lst)
                print('return_list', return_list)
                print('wait_list', wait_list)
                if return_list and noting_lst and not wait_list:
                    rec.delivery_status = 'return'
                if return_list and not noting_lst and not wait_list:
                    rec.delivery_status = 'return'
                if noting_lst and not wait_list and not return_list:
                    rec.delivery_status = 'nothing'


    @api.depends('user_id', 'state')
    def compute_order_amount(self):
        current_date = datetime.now().date()
        range = calendar.monthrange(current_date.year, current_date.month)
        start_date = date(current_date.year, current_date.month, 1)
        end_date = date(current_date.year, current_date.month, range[1])
        for order in self:
            self.env.cr.execute("""
                SELECT sum(amount_untaxed) from sale_order where
                date_order >= %s
                and date_order <= %s
                and sale_type = 'sale'
                and state in ('sale','done')
                and user_id = %s
            """, (start_date, end_date, order.user_id.id))
            result = self._cr.fetchall()
            if result:
                order.achieved_amt = result[0][0]

    @api.depends('order_line.price_total',
                 'kit_rate_total', 'kit_igst',
                 'kit_cgst', 'kit_sgst', 'amount_untaxed_customization', 'customization_igst',
                 'customization_cgst', 'customization_sgst')
    def _amount_all(self):
        for order in self:
            amount_untaxed = amount_tax = 0.0
            amount_untaxed_ = amount_tax_ = amount_total_ = 0.0
            for line in order.order_line:
                amount_untaxed += line.price_subtotal
                amount_tax += line.price_tax
                amount_untaxed_ = order.pricelist_id.currency_id.round(amount_untaxed)
                amount_tax_ = order.pricelist_id.currency_id.round(amount_tax)
                amount_total_ = amount_untaxed + amount_tax
            if order.is_kit is True:
                amount_total_ = order.kit_rate_total + order.kit_igst + order.kit_cgst + order.kit_sgst
            if order.is_kit is False and order.customisation is True:
                amount_total_ = order.amount_untaxed_customization + order.customization_igst + \
                                order.customization_cgst + order.customization_sgst
            order.update({
                'amount_untaxed': amount_untaxed_,
                'amount_tax': amount_tax_,
                'amount_total': amount_total_
            })

    @api.depends('order_line.price_total')
    def _amount_all_kit(self):
        for order in self:
            if order.is_kit is True:
                amount_untaxed = 0.0
                for line in order.order_line:
                    amount_untaxed += line.price_subtotal
                order.update({
                    'kit_rate': order.pricelist_id.currency_id.round(amount_untaxed),
                })

    @api.depends('kit_rate')
    def _amount_kit(self):
        for order in self:
            order.update({
                'kit_rate_total': order.kit_rate * order.kit_quantity,
            })

    @api.depends('order_line.price_total')
    def _amount_all_customization(self):
        for order in self:
            if order.customisation is True and order.is_kit is False:
                amount_untaxed = 0.0
                for line in order.order_line:

                    amount_untaxed += line.price_subtotal
                order.update({
                    'amount_untaxed_customization': order.pricelist_id.currency_id.round(amount_untaxed),
                })

    @api.depends('amount_untaxed_customization', 'customization_igst', 'customization_cgst', 'customization_sgst')
    def _amount_customization_total(self):
        for order in self:
            total_ = 0.0
            if order.customisation is True and order.is_kit is False:
                total_ = order.amount_untaxed_customization + order.customization_igst + \
                         order.customization_cgst + order.customization_sgst
                order.update({
                    'amount_customization_total': total_
                })

    @api.depends('kit_rate_total', 'kit_igst', 'kit_cgst', 'kit_sgst')
    def _amount_kit_total(self):
        for order in self:
            total_ = 0.0
            if order.is_kit is True:
                total_ = order.kit_rate_total + order.kit_igst + order.kit_cgst + order.kit_sgst
                order.update({
                    'kit_rate_grandtotal': total_
                })
            else:
                total_ = 0.0


    def _count_requisition(self):
        for res in self:
            number = self.env['purchase.requisition'].search([('sale_order_id', '=', res.id)])
            count = 0
            for length in number:
                count += 1
            res.requisition_count = count


    def _count_purchase_order(self):
        for res in self:
            number = self.env['purchase.order'].search([
                ('sale_id', '=', res.id)])
            count = 0
            for length in number:
                count += 1
            res.count_purchase_order = count


    def _get_user(self):
        self.logged_in_user = self.env.user.id

    state = fields.Selection([
        ('draft', 'Quotation'),
        ('sent', 'Quotation Sent'),
        ('sale', 'Sales Order'),
        ('done', 'Locked'),
        ('cancel', 'Cancelled'),
    ], string='Status', readonly=True, copy=False, index=True, track_visibility='onchange', default='draft')
    sample_state = fields.Selection([
        ('draft', 'Quotation'),
        ('waiting_for_sample_approval', 'Waiting For Sample Approval'),
        ('sample_approved', 'Sample Approved'),
        ('sample_rejected', 'Sample Rejected'),
        ('sent', 'Quotation Sent'),
        ('sale', 'Sample Order'),
        ('waiting_for_gift_approval', 'Waiting For Gift Approval'),
        ('approved', 'Gift Approved'),
        ('done', 'Locked'),
        ('cancel', 'Cancelled'),
        ('rejected', 'Rejected'),
        ('rejected_so', 'Rejected SO')
    ], string='Status', readonly=True, copy=False, index=True, tracking=3, default='draft')

    order_line = fields.One2many('sale.order.line', 'order_id', string='Order Lines', states={'cancel': [('readonly', True)], 'done': [('readonly', True)]}, copy=True, auto_join=True)
    delivery_order_line = fields.One2many('stock.picking', 'sale_id', 'Delivery Order Status')
    delivery_status = fields.Selection(
        [('new', 'New'), ('nothing_delivery', 'Nothing For Delivery'),('waiting_delivery', 'Waiting For Delivery'), ('return', 'Returned'),
         ('waiting_return', 'Waiting For Return'), ('nothing', 'Nothing To Return'),('cancel', 'Cancelled')],
        compute='_compute_delivery_status', string="Status", default='new')



    # @api.depends('delivery_order_line.state')
    def _compute_deliver_status(self):
        for rec in self:
            if not rec.order_line:
                rec.deliver_status = 'nothing_delivery'
            else:
                wait_del = rec.order_line.filtered(lambda x : x.product_uom_qty != x.qty_delivered)
                partially_del = rec.order_line.filtered(lambda x : x.qty_delivered > 0 and not x.product_uom_qty == x.qty_delivered)
                fully_del = rec.order_line.filtered(lambda x : x.product_uom_qty == x.qty_delivered)

                if wait_del and not partially_del:
                    rec.deliver_status = 'waiting_delivery'
                if partially_del and not fully_del:
                    rec.deliver_status = 'partially_delivered'
                if fully_del :
                    rec.deliver_status = 'fully_delivered'


    # @api.depends('delivery_order_line.state')
    def _compute_return_status(self):
        for rec in self:
            if not rec.order_line:
                rec.return_status = 'nothing_return'
            else:
                wait_del = rec.order_line.filtered(lambda x : x.qty_delivered > 0 and x.return_qty == 0)
                partially_del = rec.order_line.filtered(lambda x :  x.pending_qty > 0.0 and x.return_qty > 0)
                fully_del = rec.order_line.filtered(lambda x : x.return_qty == x.product_uom_qty and x.pending_qty == 0.0)
                if not wait_del and not partially_del and not wait_del:
                    rec.return_status = 'nothing_return'
                if wait_del and not partially_del:
                    rec.return_status = 'waiting_return'
                if partially_del and not fully_del:
                    rec.return_status = 'partially_returned'
                if fully_del :
                    rec.return_status = 'fully_returned'

    deliver_status = fields.Selection(
        [('nothing_delivery', 'Nothing For Delivery'),
         ('waiting_delivery', 'Waiting For Delivery'),
         ('partially_delivered', 'Partially Delivered'),
         ('fully_delivered', 'Fully Delivered'),('cancel', 'Cancelled')],
        compute='_compute_deliver_status', string="Delivery Status", default='nothing_delivery')
    return_status = fields.Selection(
        [('nothing_return', 'Nothing For Return'),
         ('waiting_return', 'Waiting For Return'),
         ('partially_returned', 'Partially Returned'),
         ('fully_returned', 'Fully Returned'),('cancel', 'Cancelled')],
      compute='_compute_return_status', string="Return Status", default='nothing_return')

    sale_amt = fields.Float(string='Total Sample Amount')
    sale_type = fields.Selection([
        ('sale','Sale'),
        ('sample_gift','Sample'),
        ('gift', 'Gift'),
        ('gcrm', 'GCRM')
    ],string='Type')
    customisation = fields.Boolean('Customization Required')
    po_date = fields.Date('PO Received Date', track_visibility='onchange')
    po_number = fields.Char('PO Number',track_visibility='onchange')
    delivery_date = fields.Date('Delivery Date',track_visibility='onchange')
    penalty = fields.Selection([('yes','Yes'),('no','No')],string='Penalty',track_visibility='onchange')
    po_attachment = fields.Binary('PO Attachment',track_visibility='onchange')
    # lead_id = fields.Many2one('crm.lead','Lead')
    need_approval = fields.Boolean(string='Need Approval')
    attachment_ids = fields.Many2many('ir.attachment', 'attachment_order_rel', 'sale_id', 'attachment_id',
                                      string='PO Attachment', track_visibility='onchange')
    gift_amt = fields.Float('Gift/Sample Amt.')
    # gift_amt = fields.Float('Gift/Sample Amt.', default=_default_approval_amount)
    remaining_sale_amtount = fields.Float(copy=False,string='Remaining Sample Amount',track_visibility='onchange')
    packing_line = fields.One2many('packing.line', 'pack_order_id', copy=True)
    need_po_amendment = fields.Boolean('PO Attachment',track_visibility='onchange')
    division_ids = fields.Many2many(related="order_id.partner_id.division_ids")
    purchase_lead = fields.Integer('Purchase Lead Time', track_visibility='onchange')
    packing_lead = fields.Integer('Packing Lead Time', track_visibility='onchange')
    shipping_lead = fields.Integer('Shipping Lead Time', track_visibility='onchange')
    delivery_lead = fields.Integer(compute='_compute_delivery_lead', string='Delivery Lead Time')
    remaining_days = fields.Integer(
        compute='_compute_remaining_days',
        string='Remaining Days to Delivery',
        store=True,
        copy=False
    )
    convert_to_gift = fields.Boolean('Converted')
    gift_convert_approved = fields.Boolean('Approved')
    gift_rejected = fields.Boolean('Rejected')
    packing_done_days = fields.Float('Packing Confirmation Days',readonly=True,track_visibility='onchange')
    shiping_day = fields.Integer('Shipping Day',track_visibility='onchange')
    send_mail_to_mo = fields.Boolean('Mail Sent To Packaging Dept.')
    consume_sample_amt = fields.Float(copy=False,string='Consumed Sample Amount', store=True,
                                      compute='_compute_user_id_amt')
    kit_product_line = fields.One2many('order.pack.product','order_kit_id',compute="_product_packing_order",readonly=False,store=True)
    pack_design_id = fields.Many2one('package.design',string="Designing Reference",track_visibility='onchange')
    sent_for_design = fields.Boolean('Sent For Design',track_visibility='onchange')
    design_states = fields.Selection([('new','New'),
                              ('design_submit','Design Submitted'),
                              ('customer_approve','Customer Approved'),
                              ('done','Done'),
                              ('cancel','Cancel')],compute="_design_states")
    date_need_approval = fields.Boolean()
    email_attachment_ids = fields.Many2many('ir.attachment', 'order_attachment_rel', 'sale_id', 'attachment_id',
                                      string='Email Attachment', track_visibility='onchange')
    packaging_total = fields.Float(compute="total_packaging_amount", string="Total Amount", store=True)
    # sample_amount_total = fields.Float(compute="_sample_amtount",store=True)
    sap_code = fields.Char('Sap Code')
    rm_name = fields.Char('RM Name')
    region = fields.Char('Region')
    gcrm_no = fields.Char('GCRM No.')
    requisition_from = fields.Char('Requisition From')
    requisition_date = fields.Date('Requisition Date')
    division_id = fields.Many2one('division','Division')
    # punch_by = fields.Char('Punch By')
    dr_name = fields.Char('Dr Name')
    delivery_address = fields.Char('Delivery Address')
    courier_no = fields.Char('Courier No.')
    courier_name = fields.Char('Courier Name')
    inv_date = fields.Date('Invoice Date')
    inv_number = fields.Char('Invoice Number')
    is_msp_approval = fields.Boolean()
    packaging_po_id = fields.Many2one('purchase.order')
    target_amount = fields.Float(related='user_id.sale_target', string='Target Amount',
                                    readonly=True)
    brand_ids = fields.Many2many('brand', 'brand_sale_rel', 'sale_id', 'brand_id', 'Brand',track_visibility='onchange')



    @api.depends('user_id')
    def _compute_user_id_amt(self):
        """
        @api.depends() should contain all fields that will be used in the calculations.
        """
        for sampleamt in self:
            if sampleamt.user_id:
                sampleamt.consume_sample_amt = sampleamt.user_id.used_sale_amt


    packaging_state = fields.Selection([
        ('draft', 'RFQ'),
        ('sent', 'RFQ Sent'),
        ('to approve', 'To Approve'),
        ('purchase', 'Purchase Order'),
        ('done', 'Locked'),
        ('cancel', 'Cancelled')
    ], string='Packaging Status', readonly=True, index=True, copy=False, compute="packaging_po", store=True)
    achieved_amt = fields.Float('Achieved Amount', compute="compute_order_amount")
    exporters_ref = fields.Char("Exporters Ref")
    buyer_order_no = fields.Char("Buyers Order No.")
    pre_carriage_by = fields.Char("Pre Carriage By")
    place_of_receipt = fields.Char("Place Of Receipt By Pr-Carrier")
    vessel_flight_no = fields.Char("Vessel/Flight NO.")
    port_of_loading = fields.Char("Port Of Loading")
    port_of_dise = fields.Char("Port Of Dise")
    final_destn = fields.Char("Final Dest.")
    terms_of_payments = fields.Char("Terms Of Delivery Of Payments")
    marks_no = fields.Char("Marks & No.")
    kind_of_pkgs = fields.Char("No & Kind Of Pkgs.")
    des_of_goods = fields.Char("Des.Of Goods")
    container_no = fields.Char("Container No.")
    origin = fields.Char("Origin")
    destination = fields.Char("Destination")
    book_no = fields.Char('Book Number')
    po_receipt_date = fields.Date('PO Receipt Date')
    submitted_date = fields.Date('Submitted Date')
    submitted_to = fields.Char('Submitted To')
    artwork_need = fields.Boolean('Artwork Required')
    division_ids = fields.Many2many('division', 'division_sale_relation', 'sale_id', 'division_id', 'Division')
    # artwork_need = fields.Selection([('yes', 'Yes'),('no', 'No')],default='no')
    # division_ids = fields.Many2many('division', 'division_sale_relation','sale_id', 'division_id', 'Division')
    product_amt_total = fields.Float('Total', compute="compute_total_product_cost", store=True)
    cgst_total = fields.Float('Output CGST',compute="compute_total", store=True)
    sgst_total = fields.Float('Output SGST', compute="compute_total", store=True)
    igst_total = fields.Float('Output IGST', compute="compute_total", store=True)
    design_attchment_ids = fields.Many2many('ir.attachment', 'attachment_sal_design_rel', 'sale_id', 'attachment_id',
                                      string='Design Attachment', track_visibility='onchange')
    segment_id = fields.Many2one('segment','Segment')
    approved_id = fields.Many2one('res.users', 'Approved by')
    # requested_id = fields.Many2one('res.users', 'Requested for Approval')
    design_requested_id = fields.Many2one('res.users', 'Design Requested To')
    packaging_req_id = fields.Many2one('res.users', 'Packaging Requested To')
    convert_to_gift = fields.Boolean('Converted')
    gift_convert_approved = fields.Boolean('Approved')
    gift_rejected = fields.Boolean('Rejected')
    is_kit = fields.Boolean('Is Kit?')
    is_existing_kit = fields.Boolean('Is Existing Kit?')
    kit_id = fields.Many2one('product.product', 'Kit')
    kit_name = fields.Char('Kit Name')
    kit_quantity = fields.Integer('Kit Quantity', default=0)
    delivery_schedule = fields.Selection([
        ('immidiate', 'Immediate'),
        ('7days', '7 Days'),
        ('15days', '15 Days'),
        ('4-6', '4 to 6 Weeks'),
        ('6-8', '6 to 8 Weeks'),
        ('8-10', '8 to 10 Weeks'),
        ('10-Above', '10 Weeks & Above')
    ], string='Delivery Schedule', copy=False, index=True)
    kit_rate = fields.Monetary(string='Kit Rate (Per Qty)', store=True, readonly=True, compute='_amount_all_kit',
                                     track_visibility='onchange')
    kit_rate_total = fields.Monetary(string='Total Kit Rate', store=True, readonly=True, compute='_amount_kit',
                               track_visibility='onchange')
    kit_rate_grandtotal = fields.Monetary(string='Total', store=True, readonly=True, compute='_amount_kit_total',
                                     track_visibility='onchange')
    kit_product = fields.Many2one('product.product', 'Kit Product', copy=False, index=True)
    picking_type_mo = fields.Many2one(
        'stock.picking.type',
        string='Kit Manufacturing Location',
        copy=False,
        index=True
    )
    internal_transfer_mo = fields.Many2one(
        'stock.picking',
        string='Transfer to Process',
        copy=False,
        index=True
    )
    partner_ids = fields.Many2many(
        'res.partner',
        'rel_sale_partner_invoice',
        'sale_id',
        'partner_id',
        string='Associated Addresses',
    )

    parent_ids = fields.Many2many(
        'res.partner',
        'rel_sale_parent',
        'sale_order_id',
        'parent_id',
        string='Associated Parent Addresses',
    )
    count_purchase_order = fields.Integer(compute='_count_purchase_order', string='Purchase Count')
    requisition_count = fields.Integer(compute='_count_requisition', string='Requisition Count')
    logged_in_user = fields.Many2one('res.users', compute='_get_user', string='Logged in User')
    is_packaging_team = fields.Boolean(
        string='Is Packaging Team', copy=False,
        index=True)
    is_sales_team = fields.Boolean(
        string='Is Sales Team', copy=False,
        index=True)
    sent_to_customer = fields.Boolean(
        string='Sent to Customer', copy=False,
        index=True, default=False)
    bom_id = fields.Many2one('mrp.bom', string='Kit BOM', copy=False, index=True, readonly=True)
    manufacturing_id = fields.Many2one('mrp.production', string='MO Reference', copy=False, index=True, readonly=True)
    salesperson_name = fields.Char(
        related='user_id.name', string='Salesperson',
        copy=False, index=True, readonly=True, store=True
    )
    minimum_tax_kit = fields.Many2one(
        'account.tax',
        string='Taxes',
        copy=False, index=True, readonly=True, store=True
    )
    tax_kit = fields.Char(
        string='Taxes', compute='_get_max_tax',
        copy=False, index=True
    )
    user_id = fields.Many2one('res.users', string='Salesperson', index=True, track_visibility='onchange')
    kit_igst = fields.Monetary(string='Output IGST', compute='_get_max_tax')
    kit_sgst = fields.Monetary(string='Output SGST', compute='_get_max_tax')
    kit_cgst = fields.Monetary(string='Output CGST', compute='_get_max_tax')
    is_msp_custom_combo = fields.Boolean(compute='_get_combo_value',
        string='Both True', copy=False,
        index=True, default=False, store=True)
    is_quotation_sent = fields.Boolean(
        string='Quotation Sent for Approval', copy=False,
        index=True, default=False)
    is_so_sent = fields.Boolean(
        string='SO Sent for Approval', copy=False,
        index=True, default=False)
    is_sample_approval = fields.Boolean(
        string='Sample Approval', copy=False,
        index=True, default=False)
    is_sample_sent = fields.Boolean(
        string='Sample Sent for Approval', copy=False,
        index=True, default=False)
    is_sample_rejected = fields.Boolean(
        string='Sample Rejected', copy=False,
        index=True, default=False)
    is_sample_approved = fields.Boolean(
        string='Sample Approved', copy=False,
        index=True, default=False)
    sample_approved_by = fields.Many2one(
        'res.users',
        string='Sample Approved By', copy=False,
        index=True, default=False, readonly=True, track_visibility='onchange')
    related_sale_ids = fields.Many2many('sale.order', 'related_sale_order_rel', 'sale_id',
                                        'sale_id2', string='Related Orders',
                                        help='Used for reports in case of confirmed in bulk')
    customization_igst = fields.Monetary(string='Output IGST', compute='_get_customization_tax', store=True)
    # customization_igst = fields.Monetary(string='Output IGST', store=True)
    customization_sgst = fields.Monetary(string='Output SGST', compute='_get_customization_tax', store=True)
    # customization_sgst = fields.Monetary(string='Output SGST', store=True)
    customization_cgst = fields.Monetary(string='Output CGST', compute='_get_customization_tax')
    # customization_cgst = fields.Monetary(string='Output CGST')
    tax_customisation = fields.Char(
        string='HSN Code', compute='_get_customization_tax',
        copy=False, index=True
    )
    # tax_customisation = fields.Char(
    #     string='HSN Code',
    #     copy=False, index=True
    # )
    cutomisation_taxes = fields.Char(
        string='Taxes', compute='_get_customization_tax',
        copy=False, index=True
    )
    amount_untaxed_customization = fields.Monetary(
        string='Untaxed Amount', store=True, readonly=True, compute='_amount_all_customization',
                                     track_visibility='onchange')
    amount_customization_total = fields.Monetary(
        string='Total Amount', store=True, readonly=True, compute='_amount_customization_total',
                                     track_visibility='onchange')
    is_old_order = fields.Boolean(
        string='Old Order', copy=False, default=False,
    )

    @api.onchange('is_old_order')
    def chnage_old_order(self):
        for data in self:
            if data.is_old_order:
                data.customisation = False
                # data.action_open_warning_wizard()


    def action_open_warning_wizard(self):
        view = self.env.ref('qms_sale_orders.view_from_old_order_warning')
        view_id = self.env['old.order.warning']
        vals = {
            'sale_order_id': self.id
        }
        new = view_id.create(vals)
        print(new)
        return {
            'name': _("Mark as Old Order"),
            'view_mode': 'form',
            'view_id': view.id,
            'res_id': new.id,
            'view_type': 'form',
            'res_model': 'old.order.warning',
            'type': 'ir.actions.act_window',
            'target': 'new',
        }

    # function : CREATE design record & mail trigger

    def action_send_design_with_mail(self):
        pack_lst = []
        # create design record
        design = self.env['package.design']
        for line in self.packing_line:
            pack_lst.append((0, 0, {
                'product_id': line.product_id.id,
                'description': line.description,
                'quantity': line.quantity,
                'type': line.type,
                'size': line.size,
                'price': line.price,
                'total': line.total
            }))
        design_id = design.create({'sale_id': self.id,
                                   'design_packing_line': pack_lst})
        self.write({'pack_design_id': design_id.id, 'sent_for_design': True,
                    'design_requested_id': self.env.user.id})
        template = self.env.ref('qms_sale_orders.send_for_design_mail_template')
        action_id = self.env.ref('qms_sale_orders.action_design').id
        params = "web#id=%s&view_type=form&model=package.design&action=%s" % (
            self.pack_design_id.id, action_id
        )
        current_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        design_url = str(current_url) + str(params)

        # get users
        get_group = self.env.ref('qms_sale_orders.group_sale_design')
        users_ids = get_group.users.filtered(lambda x: x.email)
        for user in users_ids:
            if template:
                values = template.generate_email(self.id)
                values['email_to'] = user.partner_id.email
                values['email_from'] = self.user_id.partner_id.email
                values['body_html'] = values['body_html'].replace('design_url', design_url)
                mail = self.env['mail.mail'].create(values)

                try:
                    mail.send()
                    values['body_html'] = values['body_html'].replace(design_url, 'design_url')
                except Exception:
                    pass
        return True


    def approve_sample(self):
        action_id = self.env.ref('sale.action_quotations').id
        params = "/web#id=%s&view_type=form&model=sale.order&action=%s" % (
            self.id, action_id
        )
        template = self.env.ref('qms_sale_order.approved_mail_template')
        current_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        sale_url = str(current_url) + str(params)
        template.email_from = self.env.user.login
        template.email_to = self.user_id.partner_id.email or ''
        template.body_html = template.body_html.replace('_sale_url', sale_url)
        template.send_mail(self.id, force_send=True)
        template.body_html = template.body_html.replace(sale_url, '_sale_url')
        self.write({
            'sample_state': 'sample_approved',
            'sample_approved_by': self.env.user.id,
            'is_sample_approved': True,
            'is_sample_approval': False,
        })
        self.action_confirm()


    def print_quotation(self):
        self.filtered(lambda s: s.state in ('draft', 'approved')).write({'state': 'sent'})
        return self.env.ref('sale.action_report_saleorder').report_action(self)




    @api.depends('is_msp_approval', 'customisation')
    def _get_combo_value(self):
        for data in self:
            if data.is_msp_approval is True and data.customisation is True:
                data.is_msp_custom_combo = True

            else:
                data.is_msp_custom_combo = False

    @api.onchange('is_kit')
    def change_is_kit(self):
        for data in self:
            warehouse_id = self.env['stock.warehouse'].search([('company_id', '=', self.company_id.id)])
            data.picking_type_mo = warehouse_id.stock_manu_picking_type.id


    @api.onchange('partner_id')
    def partner_id_change(self):
        for rec in self:
            division_ids = rec.division_ids


    def _get_max_tax(self):
        for order in self:
            hsn = {}
            list_ = []
            if order.sale_type == 'sale':
                for line in order.order_line:
                    hsn.update({line.hsn_id.id: line.hsn_id.igst_sale.amount})
                if hsn:
                    maximum = max(hsn, key=hsn.get)
                    hsn_ = self.env['hsn.master'].browse(maximum)
                    if order.igst_total > 0.0:
                        order.kit_igst = (order.kit_rate_total * hsn_.igst_sale.amount) / 100
                        list_.append(hsn_.igst_sale.name)
                    else:
                        order.kit_igst = 0.0
                    if order.cgst_total > 0.0:
                        order.kit_cgst = (order.kit_rate_total * hsn_.cgst_sale.amount) / 100
                        list_.append(hsn_.cgst_sale.name)
                    else:
                        order.kit_cgst
                    if order.sgst_total > 0.0:
                        order.kit_sgst = (order.kit_rate_total * hsn_.sgst_sale.amount) / 100
                        list_.append(hsn_.sgst_sale.name)
                    else:
                        order.kit_sgst = 0.0
                    l = '\n'.join(map(str, list_))
                    order.tax_kit = l
            else:
                order.tax_kit = False
                order.kit_sgst = 0.0
                order.kit_cgst = 0.0
                order.kit_igst = 0.0


    @api.depends('order_line')
    def _get_customization_tax(self):
        for order in self:
            if order.customisation is True and order.is_kit is False:
                hsn = {}
                list_ = []
                for line in order.order_line:
                    hsn.update({line.hsn_id.id: line.hsn_id.igst_sale.amount})
                if hsn:
                    maximum = max(hsn, key=hsn.get)
                    hsn_ = self.env['hsn.master'].browse(maximum)
                    if order.igst_total > 0.0:
                        order.customization_igst = (order.amount_untaxed_customization * hsn_.igst_sale.amount) / 100
                        list_.append(hsn_.igst_sale.name)
                    else:
                        order.customization_igst = False
                    if order.cgst_total > 0.0:
                        order.customization_cgst = (order.amount_untaxed_customization * hsn_.cgst_sale.amount) / 100
                        list_.append(hsn_.cgst_sale.name)
                    else:
                        order.customization_cgst = False
                    if order.sgst_total > 0.0:
                        order.customization_sgst = (order.amount_untaxed_customization * hsn_.sgst_sale.amount) / 100
                        list_.append(hsn_.sgst_sale.name)
                    else:
                        order.customization_sgst = False
                    order.tax_customisation = hsn_.name
                    l = '\n'.join(map(str, list_))
                    order.cutomisation_taxes = l
                else:
                    order.cutomisation_taxes = False
            else:
                order.cutomisation_taxes = False
                order.customization_sgst = 0.0
                order.customization_cgst = 0.0
                order.customization_igst = 0.0
                order.tax_customisation = False




    def send_to_customer(self):
        for data in self:
            product_search = self.env['product.product'].search([('name', '=', 'Customization')])
            dict_ = {
                'product_id': product_search.id,
                'name': product_search.name,
                'product_uom_qty': 1,
                'price_unit': self.packaging_total,
                'order_id': self.id,
                'tax_id': False
            }
            if data.is_kit:
                dict_['qty_per_kit'] = 1
            data.order_line.create(dict_)
            if all(rec.price <= 0.0 for rec in data.packing_line):
                raise UserError(
                    _('Please fill Cost at least in one line before processing!'))
            action_id = self.env.ref('sale.action_quotations').id
            params = "web#id=%s&view_type=form&model=sale.order&action=%s" % (
                data.id, action_id
            )
            sale_url = str(params)
            template = self.env.ref('qms_sale_orders.email_template_customization_to_sales')
            if template:
                values = template.generate_email(data.id)
                values['email_to'] = data.user_id.partner_id.email
                values['email_from'] = self.env.user.partner_id.email
                values['email_cc'] = self.env.user.email or self.env.user.partner_id.email
                values['body_html'] = values['body_html'].replace('_sale_url', sale_url)
                mail = self.env['mail.mail'].create(values)
                try:
                    mail.send()
                except Exception:
                    pass
                data.sent_to_customer = True


    def create_purchase_order(self):
        action = {}
        for data in self:
            user = self.env.user
            user_id = data.user_id.id
            sale_id = data.id
            opportunity_id = data.opportunity_id.id
            # ticket_id = data.ticket_id.id
            action = {
                'name': _('Purchase Order'),
                'view_type': 'form',
                'view_mode': 'form',
                'view_id': self.env.ref('purchase.purchase_order_form').id,
                'res_model': 'purchase.order',
                'domain': [('sale_id', '=', sale_id)],
                'type': 'ir.actions.act_window',
                'target': 'current',
            }
            action['context'] = {
                'default_opportunity_id': opportunity_id,
                'default_sale_id': sale_id,
                'default_user_id': user_id,
                'default_company_id': data.company_id.id,
                # 'default_name': data.name,
            }
        return action


    def purchase_order_action_sale(self):
        opportunity_id = self.opportunity_id.id
        result = {
            "type": "ir.actions.act_window",
            "res_model": "purchase.order",
            "views": [[False, "tree"], [False, "form"], [False, "kanban"], [False, "pivot"], [False, "graph"],
                      [False, "calendar"]],
            "domain": [["sale_id", "=", self.id]],
            "context": {
                'default_lead_id': opportunity_id,
                'default_sale_id': self.id,
                'create': True,
                'edit': True
            },
            "name": "Purchase",
        }
        return result


    def requisition_order_action_sale(self):
        result = {
            "type": "ir.actions.act_window",
            "res_model": "purchase.requisition",
            "views": [[False, "tree"], [False, "form"]],
            "domain": [("sale_order_id", "=", self.id)],
            "context": {
                # 'default_sale_order_id': self.id,
                # 'default_opportunity_id': self.opportunity_id.id,
                'create': True,
                'edit': True
            },
            "name": "Requisition",
        }
        return result

    @api.constrains('kit_quantity', 'is_kit')
    def _check_kit_quantity(self):
        for order in self:
            if order.is_kit and order.kit_quantity <= 0:
                raise UserError(_('Validation Error !\nKit quantity should be greater than 0 !'))
        return True



    @api.depends('purchase_lead', 'packing_lead', 'shipping_lead')
    def _compute_delivery_lead(self):
        for sale in self:
            sale.delivery_lead = sale.purchase_lead + sale.packing_lead + sale.shipping_lead

    @api.onchange('is_kit', 'kit_id', 'is_existing_kit')
    def _onchange_kit_id(self):
        if not self.is_kit:
            for line in self.order_line:
                line.qty_per_kit = 0
            self.is_existing_kit = False
            self.kit_id = False
            self.order_line = []
            return {}

        if self.is_existing_kit and self.kit_id:
            order_lines = []
            bom = self.env['mrp.bom']._bom_find(product=self.kit_id)
            if bom:
                for bom_comp in bom.bom_line_ids:
                    product = bom_comp.product_id
                    name = product.name_get()[0][1]
                    if product.description_sale:
                        name += '\n' + product.description_sale
                    fpos = self.fiscal_position_id or self.partner_id.property_account_position_id
                    # If company_id is set, always filter taxes by the company
                    taxes = product.taxes_id.filtered(
                        lambda r: not self.company_id or r.company_id == self.company_id)
                    taxes = fpos.map_tax(taxes, product, self.partner_shipping_id) if fpos \
                        else taxes
                    order_lines.append((0, 0, {
                        'name': product.name,
                        'product_id': product.id,
                        'kit_product_id': self.kit_id.id,
                        'product_uom_qty': bom_comp.product_qty,
                        'qty_per_kit': bom_comp.product_qty,
                        'product_uom': product.uom_id.id,
                        'hsn_id': product.hsn_code.id,
                        'sale_price': product.product_tmpl_id.list_price,
                        'price_unit': product.product_tmpl_id.list_price,
                        'forecost_qty': product.virtual_available,
                        'msp': product.list_price,
                        'mrp': product.mrp,
                        'tax_id': taxes
                    }))
                self.order_line = order_lines
                for line in self.order_line:
                    line.product_id_change()
                    line.product_uom_change()

    @api.onchange('is_kit', 'is_existing_kit')
    def _onchange_existing_kit(self):
        if self.is_kit and not self.is_existing_kit:
            self.kit_id = False
            self.order_line = []

    @api.onchange('kit_quantity')
    def _onchange_kit_quantity(self):
        if self.is_kit and self.order_line:
            for line in self.order_line:
                line.product_uom_qty = line.qty_per_kit

    @api.depends('order_line.tax_id')
    def compute_total(self):
        for rec in self:
            cgst = sgst = igst = 0.0
            for tax in rec.order_line:
                cgst = cgst + tax.cgst
                sgst = sgst + tax.sgst
                igst = igst + tax.igst
            rec.cgst_total = cgst
            rec.sgst_total = sgst
            rec.igst_total = igst

    @api.depends('order_line.product_id')
    def compute_total_product_cost(self):
        total = 0.0
        for rec in self:
            for line in rec.order_line:
                if line.product_id:
                    total = total + (line.product_id.standard_price * line.product_uom_qty)
            rec.product_amt_total = total
            total = 0.0


    @api.onchange('partner_id')
    def onchange_partner_id(self):
        """
        Update the following fields when the partner is changed:
        - Pricelist
        - Payment terms
        - Invoice address
        - Delivery address
        """
        # NEHA: Update existing lines, when Partner change
        if self.partner_id and self.order_line:
            for line in self.order_line:
                if line.product_id.hsn_code:
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
        if not self.partner_id:
            self.update({
                'partner_invoice_id': False,
                'partner_shipping_id': False,
                'payment_term_id': False,
                'fiscal_position_id': False,
            })
            return

        addr = self.partner_id.address_get(['delivery', 'invoice'])
        values = {
            'pricelist_id': self.partner_id.property_product_pricelist and self.partner_id.property_product_pricelist.id or False,
            'payment_term_id': self.partner_id.property_payment_term_id and self.partner_id.property_payment_term_id.id or False,
            'division_ids': [(6, 0, self.partner_id.division_ids.ids)],
            'partner_invoice_id': False,
            'partner_shipping_id': False,
            'user_id': self.partner_id.user_id.id or self.env.uid
        }
        if self.env['ir.config_parameter'].sudo().get_param(
                'sale.use_sale_note') and self.env.user.company_id.sale_note:
            values['note'] = self.with_context(lang=self.partner_id.lang).env.user.company_id.sale_note

        if self.partner_id.team_id:
            values['team_id'] = self.partner_id.team_id.id
        list_ = []
        li_ = []
        if self.partner_id.child_ids:
            for data in self.partner_id.child_ids:
                list_.append(data.id)
                partner_data = self.env['res.partner'].search([
                    ('id', 'in', list_)
                ])
                if partner_data:
                    self.update({'partner_ids': partner_data})
        if not self.partner_id.child_ids:
            if self.partner_id.parent_id:
                li_.append(self.partner_id.parent_id.id)
                print(li_)
            for data in self.partner_id.parent_id.child_ids:
                list_.append(data.id)
                li_.append(self.partner_id.parent_id.id)
                partner_data = self.env['res.partner'].search([
                    ('id', 'in', list_)
                ])
                parent_data = self.env['res.partner'].search([
                    ('id', 'in', li_)
                ])
                if parent_data:
                    self.update({'parent_ids': parent_data})
                if partner_data:
                    self.update({'partner_ids': partner_data})
        self.update(values)



    @api.depends('packing_line.price')
    def total_packaging_amount(self):
        total = 0.0
        for rec in self:
            for line in rec.packing_line:
                total = total + line.total
            rec.packaging_total = total

    @api.depends('pack_design_id.state')
    def _design_states(self):
        for line in self:
            if line.pack_design_id:
                line.design_states = line.pack_design_id.state
            else:
                pass;



    @api.depends('packaging_po_id.state')
    def packaging_po(self):
        for rec in self:
            if rec.packaging_po_id:
                rec.packaging_state = rec.packaging_po_id.state
            else:
                pass;


    def approve_convert_to_gift(self):
        template = self.env.ref('qms_sale_orders.convert_line_sample_to_gift')
        action_id = self.env.ref('qms_sale_orders.action_sample_sale_order').id
        params = "/web#id=%s&view_type=form&model=sale.order&action=%s" % (
            self.id, action_id)
        current_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        convert_line = str(current_url) + str(params)
        template.email_from = self.env.user.login
        template.email_to = self.user_id.partner_id.email or ''
        template.body_html = template.body_html.replace('convert_line', convert_line)
        template.send_mail(self.id, force_send=True)
        template.body_html = template.body_html.replace(convert_line, 'convert_line')
        for line in self.order_line:
            line.return_status = 'nothing'
            line.order_id.sudo().user_id.write({
                'used_sale_amt': line.order_id.user_id.used_sale_amt - (line.gift_qty * line.price_unit)})
            if line.type == 'pending':
                line.type = 'gift'
                line.return_status = 'nothing'
                line.order_id.sudo().user_id.write({
                    'used_sale_amt': line.order_id.user_id.used_sale_amt - (line.gift_qty * line.price_unit)})
        self.convert_to_gift = False
        self.gift_convert_approved = True
        self.sample_state = 'approved'


    # def create_kit_lot(self):
    #     lot = self.env['stock.production.lot'].create(
    #         {'name': self.kit_name + '/',
    #         # {'name': self.kit_name + '/' + str(datetime.strftime('%Y')),
    #          'product_id': self.kit_product.id,
    #          # 'removal_date': ml.remove_date,
    #          # 'manufacture_date': ml.manufacture_date,
    #          # 'life_date': ml.remove_date,
    #          # 'import_date': ml.import_date,
    #          # 'mrp': ml.mrp,
    #          }
    #     )
    #     print('KIT LOT', lot)


    def create_kit(self):
        # Neha : search kit pro
        exist_kit = self.env['product.product'].sudo().search([('name', '=', self.kit_name)])
        if exist_kit:
            raise UserError(_('Warning! \n \n Kit name %s%s%s already exist. \n Please use different name for Kit!' %("'", self.kit_name, "'")))
        kit = self.env['product.product'].sudo().create({
            'name': self.kit_name or '',
            'standard_price': self.kit_rate,
            'type': 'product',
            'tracking': 'lot',
            'invoice_policy': 'delivery',
            'uom_id': self.env.ref('uom.product_uom_unit').id,
            'uom_po_id': self.env.ref('uom.product_uom_unit').id,
            'categ_id': self.env.ref('product.product_category_1').id,
            'service_type': 'manual',
            'taxes_id': False,
            'is_kit': True,
        })
        self.kit_product = kit.id
        self.create_bom(kit)
        # self.create_kit_lot()


    def create_bom(self, kit):
        bom_dict = {
            'product_id': kit.id,
            'product_tmpl_id': kit.product_tmpl_id.id,
            'product_qty': 1,
            'product_uom_id': kit.uom_id.id,
            'type': 'normal',
        }
        bom_line_dict = []
        for line in self.order_line:
            bom_line_dict.append((0, 0, {
                'product_id': line.product_id.id,
                'product_qty': line.qty_per_kit,
            }))
        bom_dict['bom_line_ids'] = bom_line_dict
        bom = self.env['mrp.bom'].sudo().create(bom_dict)
        self.bom_id = bom.id
        # self.create_mo(kit, bom)


    # def create_mo(self, kit, bom):
    #     mo_dict = {
    #         'origin': self.name,
    #         'product_id': kit.id,
    #         'product_qty': self.kit_quantity,
    #         'product_uom_id': kit.uom_id.id,
    #         'location_src_id': self.picking_type_mo.default_location_dest_id.id,
    #         'location_dest_id': self.picking_type_mo.default_location_dest_id.id,
    #         'bom_id': bom.id,
    #         'date_planned_start': fields.Date.context_today(self),
    #         'date_planned_finished': fields.Date.context_today(self),
    #         'procurement_group_id': self.procurement_group_id.id,
    #         # 'propagate': self.propagate,
    #         'picking_type_id': self.warehouse_id.manu_type_id.id,
    #         'company_id': self.company_id.id,
    #         'internal_transfer_mo': self.internal_transfer_mo.id,
    #         'sale_id': self.id
    #     }
    #     self.env['mrp.production'].sudo().create(mo_dict)
    #     return kit


    def view_kit(self):
        '''
        This function returns an action that display related kit of current sales order.'''
        action = self.env.ref('product.product_template_action_all').read()[0]
        if self.kit_id:
            action['views'] = [(self.env.ref('product.product_template_only_form_view').id, 'form')]
            action['res_id'] = self.kit_id.product_tmpl_id.id
        return action


    def approve_quotation(self):
        action_id = self.env.ref('sale.action_quotations').id
        params = "/web#id=%s&view_type=form&model=sale.order&action=%s" % (
            self.id, action_id
        )
        template = self.env.ref('qms_sale_orders.approved_mail_template')
        current_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        sale_url = str(current_url) + str(params)
        template.email_from = self.env.user.login
        template.email_to = self.user_id.partner_id.email or ''
        template.body_html = template.body_html.replace('_sale_url', sale_url)
        template.send_mail(self.id, force_send=True)
        template.body_html = template.body_html.replace(sale_url, '_sale_url')
        self.write({
            'state': 'approved',
            'approved_id': self.env.user.id,
            'is_quotation_approved': True,
            'is_msp_approval': False,
        })



    def approved_all(self):
        for rec in self.order_line:
            if rec.line_status == 'need_approval' or rec.line_status == 'approved':
                rec.write({'line_status': 'approved','sample_confirm_date': fields.Datetime.now()})
        template = self.env.ref('qms_sale_orders.approved_mail_template')
        if self.sale_type == 'sale':
            action_id = self.env.ref('sale.action_orders').id
        if self.sale_type == 'sample_gift':
            action_id = self.env.ref('qms_sale_orders.action_sample_sale_order').id
        if self.sale_type == 'gift':
            action_id = self.env.ref('qms_sale_orders.action_gift_sale_order').id
        params = "/web#id=%s&view_type=form&model=sale.order&action=%s" % (
            self.id, action_id
        )
        current_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        sale_url = str(current_url) + str(params)
        template.email_from = self.env.user.login
        template.email_to = self.user_id.partner_id.email or ''
        template.body_html = template.body_html.replace('_sale_url', sale_url)
        template.send_mail(self.id, force_send=True)
        template.body_html = template.body_html.replace(sale_url, '_sale_url')
        self.write({'state': 'approved' ,'approved_id': self.env.user.id})
        if self.sale_type == 'sample_gift':
            self.write({'sample_state': 'sale'})
            self.action_confirm()
        if self.is_msp_approval != True:
            self.action_confirm()
        # self.is_msp_approval = False
        self.action_confirm()


    def conv(self, val):
        return num2words(val)

    @api.model
    def default_get(self, default_fields):
        data = super(SaleOrder, self).default_get(default_fields)
        context = dict(self._context or {})
        active_ids = context.get('active_ids', []) or []
        # self.is_packaging_team = self.env.user.is_packaging_team
        # self.is_sales_team = self.env.user.is_sales_team
        product_lst = []
        if self.env.context.get('active_model') == 'product.template':
            products = self.env['product.template'].browse(active_ids)
            if products:
                for record in products:
                    product_lst.append((0, 0, {
                        'product_id': record.id,
                        'product_uom_qty': 1,
                        'price_unit': record.list_price,
                        'name': record.name,
                        'product_uom': record.uom_id.id,
                        'return_status': 'new'
                    }))
                data['order_line'] = product_lst
        return data



    def action_order_confirmation_mail(self):
        template = self.env.ref('qms_sale_orders.template_for_order_confirmation')
        # get users
        get_group = self.env.ref('qms_sale_orders.group_order_confirmation_user')
        users_ids = get_group.users.filtered(lambda x: x.email)
        for user in users_ids:
            if template:
                values = template.generate_email(self.id)
                values['email_to'] = user.partner_id.email
                values['email_from'] = self.user_id.partner_id.email
                values['email_cc'] = self.env.user.email or self.env.user.partner_id.email
                mail = self.env['mail.mail'].create(values)
                try:
                    mail.send()
                except Exception:
                    pass


    def action_confirm(self):
        if not self.order_line:
            raise UserError(_('Please Add Order Lines !!!'))

        if self.sale_type == 'gcrm' and not self.inv_number:
            raise UserError(_('Please enter action_confirmce number first !'))
        if self.sale_type == 'sale':
            design_group = self.env.ref('qms_sale_orders.group_design_packing')
            email_to = ' '
            for user in design_group.sudo().users:
                email_to = email_to + user.partner_id.email + ','

            msg = ''
            if not self.po_date:
                msg += 'PO Received Date, '
            if not self.po_receipt_date:
                msg += 'PO Date, '
            if not self.po_number:
                msg += 'PO Number, '
            if not self.delivery_date:
                msg += 'PO Delivery Date, '
            if not self.attachment_ids:
                msg += 'PO Attachment'
            if not self.po_date or not self.delivery_date or not self.po_number or not self.attachment_ids:
                raise UserError(_('Please Fill PO Details : %s' %(msg)))

            number = ''


        if self.user_id:
            if self.user_id.is_salesperson:
                if self.sale_type == 'sample_gift':
                   self.sudo().user_id.used_sale_amt = self.sudo().user_id.used_sale_amt + self.sudo().amount_untaxed

        if self.sale_type == 'sample_gift':
            self.write({'sample_state': 'sale'})
         # notification mail to purchase against SO
        if self.sale_type == 'sale':
            line_lst = []
            kit_lst = []
            # NEHA: Update user group
            # purchase_group = self.env.ref('purchase.group_purchase_manager')
            purchase_group = self.env.ref('qms_sale_orders.group_product_procurement_team')
            email_to = ' '
            # NEHA: Update to send mail one at a time
            # for user in purchase_group.sudo().users:
            #     email_to = email_to + user.partner_id.email + ','
            for line in self.order_line:
                if line.is_kit is False:
                    if line.virtual_available < line.product_uom_qty or line.virtual_available < 0.0:
                        line_lst.append(line.id)
            if self.kit_product_line:
                for kit in self.kit_product_line:
                    if kit.product_available_qty < 0.0 or kit.product_available_qty < kit.qty:
                        kit_lst.append(kit.id)
            if kit_lst or line_lst:
                template = self.env.ref('qms_sale_orders.notification_mail_send_purchase')
                action_id = self.env.ref('sale.action_orders').id
                params = "/web#id=%s&view_type=form&model=package.design&action=%s" % (
                    self.id, action_id)
                current_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
                sale_notification_url = str(current_url) + str(params)
                for user in purchase_group.sudo().users:
                    template.email_from = self.env.user.login
                    template.email_to = user.partner_id.email
                    template.send_mail(self.id, force_send=True)
        # if self.sale_type == 'sale':
        if self.is_kit:
            kit_ = self.create_kit()
        res = super(SaleOrder, self).action_confirm()
        # For sending confirmation email to Order Confirmation GROUP
        if self.sale_type == 'sale':
            if self.is_kit:
                mo_search_id = self.env['mrp.production'].search([('origin', '=', self.name)])

                self.manufacturing_id = mo_search_id.id
        return res


    @api.constrains('po_number')
    def _identify_same_po_number(self):
        for record in self:
            obj = self.search([
                ('po_number', '=ilike', record.po_number),
                ('id', '!=', record.id)
            ])
            if obj:
                raise ValidationError(
                    "PO Number already exist")


    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            if vals.get('sale_type') == 'sale':
                if 'company_id' in vals:
                    vals['name'] = self.env['ir.sequence'].with_context(force_company=vals['company_id']).next_by_code(
                        'sale.order') or _('New')
                else:
                    vals['name'] = self.env['ir.sequence'].next_by_code('sale.order') or _('New')
            if vals.get('sale_type') == 'sample_gift':
                sequence = self.env.ref('qms_sale_orders.sample_gift_sequence')
                seq = sequence.next_by_id()
                vals['name'] = seq or '/'
            if vals.get('sale_type') == 'gcrm':
                sequence = self.env.ref('qms_sale_orders.gcrm_sequence')
                seq = sequence.next_by_id()
                vals['name'] = seq or '/'
            if vals.get('sale_type') == 'gift':
                sequence = self.env.ref('qms_sale_orders.gift_sequence')
                seq = sequence.next_by_id()
                vals['name'] = seq or '/'

        if vals.get('is_kit') and vals.get('kit_quantity') <= 0:
            raise ValidationError(_('Kit quantity should be greater than 0 !'))
        # Makes sure partner_invoice_id', 'partner_shipping_id' and 'pricelist_id' are defined
        if any(f not in vals for f in ['partner_invoice_id', 'partner_shipping_id', 'pricelist_id']):
            partner = self.env['res.partner'].browse(vals.get('partner_id'))
            addr = partner.address_get(['delivery', 'invoice'])
            vals['partner_invoice_id'] = vals.setdefault('partner_invoice_id', addr['invoice'])
            vals['partner_shipping_id'] = vals.setdefault('partner_shipping_id', addr['delivery'])
            vals['pricelist_id'] = vals.setdefault('pricelist_id',
                                                   partner.property_product_pricelist and partner.property_product_pricelist.id)
        result = super(SaleOrder, self).create(vals)
        # NEHA : for products logs
        if 'order_line' in vals:
            pro_list = []
            for line in vals.get('order_line'):
                pro_list.append(line[2].get('name'))
            print('pro_list', pro_list)
            message = "Products : %s" % (",  ".join(pro_list))
            result.message_post(body=message)
        return result


    def write(self, vals):
        res = super(SaleOrder, self).write(vals)
        if self.is_kit and self.kit_quantity <= 0:
            raise ValidationError(_('Kit quantity should be greater than 0 !'))
        pro_list = []
        # NEHA : for products logs
        if 'order_line' in vals:
            for line in vals.get('order_line'):
                if not line[2] == False and line[2].get('name'):
                    pro_list.append(line[2].get('name'))
            if pro_list:
                message = " Products : %s" % (", ".join(pro_list))
                self.message_post(body=message)
        return res



    def _prepare_invoice(self):
        """
        Prepare the dict of values to create the new invoice for a sales order. This method may be
        overridden to implement custom invoice generation (making sure to call super() to establish
        a clean extension chain).
        """
        self.ensure_one()
        journal_id = self.env['account.move'].default_get(['journal_id'])['journal_id']
        if not journal_id:
            raise UserError(_('Please define an accounting sales journal for this company.'))
        invoice_vals = {
            'name': self.client_order_ref or '',
            'origin': self.name,
            'type': 'out_invoice',
            'account_id': self.partner_invoice_id.property_account_receivable_id.id,
            'partner_id': self.partner_invoice_id.id,
            'partner_shipping_id': self.partner_shipping_id.id,
            'journal_id': journal_id,
            'currency_id': self.pricelist_id.currency_id.id,
            'comment': self.note,
            'payment_term_id': self.payment_term_id.id,
            'fiscal_position_id': self.fiscal_position_id.id or self.partner_invoice_id.property_account_position_id.id,
            'company_id': self.company_id.id,
            'user_id': self.user_id and self.user_id.id,
            'team_id': self.team_id.id,
            # 'sale_id': self.id,
            'sale_type': self.sale_type
        }
        return invoice_vals


    def get_taxes(self, product):
        sale_tax = []
        if product.hsn_code:
            hsn_code = product.hsn_code
            branch_state = self.company_id.state_id
            partner_state = self.partner_id.state_id
            invoice_addres_id = self.partner_invoice_id.state_id
            if invoice_addres_id:
                if branch_state == invoice_addres_id:
                    sale_tax.append(hsn_code.cgst_sale.id)
                    sale_tax.append(hsn_code.sgst_sale.id)
                else:
                    sale_tax.append(hsn_code.igst_sale.id)
            if not invoice_addres_id:
                if branch_state == partner_state:
                    sale_tax.append(hsn_code.cgst_sale.id)
                    sale_tax.append(hsn_code.sgst_sale.id)
                else:
                    sale_tax.append(hsn_code.igst_sale.id)
        return sale_tax


    def _prepare_invoice_line_kit(self, product, qty):
        """
        method inherit for send hsn form order line to invoice line
        Prepare the dict of values to create the new invoice line for a sales order line.

        :param qty: float quantity to invoice
        """
        self.ensure_one()
        res = {}
        account = product.property_account_income_id or \
                  product.categ_id.property_account_income_categ_id
        if not account:
            raise UserError(
                _('Please define income account for this product: "%s" (id:%d) - or '
                  'for its category: "%s".') %
                (product.name, product.id, product.categ_id.name))

        fpos = self.fiscal_position_id or self.partner_id.property_account_position_id
        if fpos:
            account = fpos.map_account(account)

        res = {
            'name': product.name,
            'sequence': 1,
            'origin': self.name,
            'account_id': account.id,
            'price_unit': self.kit_rate,
            'quantity': qty,
            'hsn_id': product.hsn_code.id or False,
            # 'lot_ids': [(6, 0, self.lot_ids.ids)],
            # 'discount': self.discount,
            'uom_id': product.uom_id.id,
            'product_id': product.id or False,
            # 'layout_category_id': self.layout_category_id and self.layout_category_id.id or False,
            'invoice_line_tax_ids': [(6, 0, self.get_taxes(product))],
            # 'account_analytic_id': self.analytic_account_id.id,
            # 'analytic_tag_ids': [(6, 0, self.analytic_tag_ids.ids)],
        }
        return res


    def action_invoice_create(self, grouped=False, final=False):
        """
        Create the invoice associated to the SO.
        :param grouped: if True, invoices are grouped by SO id. If False, invoices are grouped by
                        (partner_invoice_id, currency)
        :param final: if True, refunds will be generated if necessary
        :returns: list of created invoices
        """
        inv_obj = self.env['account.move']
        precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')
        invoices = {}
        references = {}
        for order in self:
            group_key = order.id if grouped else (order.partner_invoice_id.id, order.currency_id.id)
            if order.is_kit:
                if group_key not in invoices:
                    inv_data = order._prepare_invoice()
                    invoice = inv_obj.create(inv_data)
                    references[invoice] = order
                    invoices[group_key] = invoice
                vals = {}
                if order.name not in invoices[group_key].origin.split(', '):
                    vals['origin'] = invoices[group_key].origin + ', ' + order.name
                if order.client_order_ref and order.client_order_ref not in invoices[group_key].name.split(
                        ', ') and order.client_order_ref != invoices[group_key].name:
                    vals['name'] = invoices[group_key].name + ', ' + order.client_order_ref
                invoices[group_key].write(vals)
                if order.kit_quantity > 0:
                    invoice_lines = self.env['account.move.line']
                    if order.is_existing_kit:
                        product = order.kit_id
                    else:
                        product = order.kit_product
                    vals = order._prepare_invoice_line_kit(product, qty=order.kit_quantity)
                    vals.update({'invoice_id': invoices[group_key].id})
                    invoice_lines |= self.env['account.move.line'].create(vals)
            else:
                for line in order.order_line.sorted(key=lambda l: l.qty_to_invoice < 0):
                    if float_is_zero(line.qty_to_invoice, precision_digits=precision):
                        continue
                    if group_key not in invoices:
                        inv_data = order._prepare_invoice()
                        invoice = inv_obj.create(inv_data)
                        references[invoice] = order
                        invoices[group_key] = invoice
                    elif group_key in invoices:
                        vals = {}
                        if order.name not in invoices[group_key].origin.split(', '):
                            vals['origin'] = invoices[group_key].origin + ', ' + order.name
                        if order.client_order_ref and order.client_order_ref not in invoices[group_key].name.split(
                                ', ') and order.client_order_ref != invoices[group_key].name:
                            vals['name'] = invoices[group_key].name + ', ' + order.client_order_ref
                        invoices[group_key].write(vals)
                    if line.qty_to_invoice > 0:
                        line.invoice_line_create(invoices[group_key].id, line.qty_to_invoice)
                    elif line.qty_to_invoice < 0 and final:
                        line.invoice_line_create(invoices[group_key].id, line.qty_to_invoice)

            if references.get(invoices.get(group_key)):
                if order not in references[invoices[group_key]]:
                    references[invoice] = references[invoice] | order

        if not invoices:
            raise UserError(_('There is no invoicable line.'))

        for invoice in invoices.values():
            if not invoice.invoice_line_ids:
                raise UserError(_('There is no invoicable line.'))
            # If invoice is negative, do a refund invoice instead
            if invoice.amount_untaxed < 0:
                invoice.type = 'out_refund'
                for line in invoice.invoice_line_ids:
                    line.quantity = -line.quantity
            # Use additional field helper function (for account extensions)
            for line in invoice.invoice_line_ids:
                line._set_additional_fields(invoice)
            # Necessary to force computation of taxes. In account_invoice, they are triggered
            # by onchanges, which are not triggered when doing a create.
            invoice.compute_taxes()
            invoice.message_post_with_view('mail.message_origin_link',
                                           values={'self': invoice, 'origin': references[invoice]},
                                           subtype_id=self.env.ref('mail.mt_note').id)
        # NEHA: need to check in sale lines also
        # if self.invoice_count > 0:
        #     self.invoice_status = 'invoiced'
        return [inv.id for inv in invoices.values()]


    def action_draft(self):
        res = super(SaleOrder, self).action_draft()
        self.sent_to_customer = False
        if self.sale_type == 'sample_gift':
            self.write({'sample_state': 'draft'})


    def action_cancel(self):
        res = super(SaleOrder, self).action_cancel()
        if self.amount_untaxed > self.user_id.sale_amount:
            self.write({'is_sample_approval': True, 'is_sample_approved': False, 'is_sample_sent': False})
        if any(data.price_unit < data.msp for data in self.order_line):
            self.write({'is_msp_approval': True, 'is_quotation_approved': False, 'is_quotation_sent': False})
        if self.remaining_days < 0 or self.delivery_lead > self.remaining_days:
            self.write({
                'is_so_approval': False,
                'is_so_approved': False,
                'is_so_sent': False,
                'po_receipt_date': False,
                'delivery_date': False,
                'po_date': False,
        })
        update_amt = 0.0
        if self.sale_type == 'sample_gift':
            self.write({'sample_state': 'cancel'})
            self.write({'delivery_status': 'cancel', 'deliver_status': 'cancel'})
            for line in self.order_line:
                line.return_status = 'cancel'
        if self.delivery_order_line and self.sale_type == 'sample_gift':
            if self.sudo().user_id:
                for line in self.order_line:
                    if line.type == 'sample':
                        update_amt = line.sudo().order_id.user_id.used_sale_amt - line.price_subtotal
                        self.sudo().user_id.write({'used_sale_amt': update_amt})
                        update_amt =0.0
        return res


    def action_unlock(self):
        res = super(SaleOrder, self).action_unlock()
        if self.sale_type == 'sample_gift':
            self.write({'sample_state': 'sale'})
        return res


    def action_done(self):
        res = super(SaleOrder, self).action_done()
        if self.sale_type == 'sample_gift':
            self.write({'sample_state': 'done'})
        return res

    @api.depends('order_line')
    def _product_packing_order(self):
        if self.order_line:
            package_list = []
            kit_obj = self.env['order.pack.product']
            for line in self.order_line:
                bom = self.env['mrp.bom'].search([('product_tmpl_id', '=', line.product_id.product_tmpl_id.id)])
                if bom:
                    for bom_comp in bom.bom_line_ids:
                        package_list.append((0, 0, {
                            'order_kit_id': self.id,
                            'product_id': bom_comp.product_id.id,
                            'kit_product_id': line.product_id.id,
                            'qty': line.product_uom_qty * bom_comp.product_qty,
                            'kit_qty': bom_comp.product_qty,
                            # 'tax_id': [(6,0, line.tax_id.ids)],
                            'hsn_id': bom_comp.product_id.hsn_code,
                            'sale_price': bom_comp.product_id.product_tmpl_id.list_price,
                            'unit_price': bom_comp.product_id.product_tmpl_id.standard_price,
                            'forecost_qty': bom_comp.product_id.virtual_available
                        }))
                    self.kit_product_line = package_list
                    line.is_kit = True





class KitProductLine(models.Model):
    _name = 'order.pack.product'

    @api.depends('qty','unit_price')
    def _price_subtotal(self):
        for line in self:
            line.subtotal = line.qty * line.sale_price

    order_kit_id = fields.Many2one('sale.order')
    product_uom = fields.Many2one('product.uom', string='Unit of Measure')
    kit_qty = fields.Float('Qty/Kit')
    product_id = fields.Many2one('product.product','Product')
    kit_product_id = fields.Many2one('product.product','Kit Name')
    qty = fields.Float('Quantity')
    unit_price = fields.Float('MRP')
    hsn_id = fields.Many2one('hsn.master','HSN Code', compute="product_change")
    tax_id = fields.Many2many('account.tax','pack_tax_rel','pack_id','tax_id', 'Tax',compute="product_change")
    cgst = fields.Float(string='CGST', compute='_compute_gst', store=True, digits=dp.get_precision('Product Price'))
    sgst = fields.Float(string='SGST', compute='_compute_gst', digits=dp.get_precision('Product Price'))
    igst = fields.Float(string='IGST', compute='_compute_gst', digits=dp.get_precision('Product Price'))
    amount = fields.Float(string='Amt. with Taxes', readonly=True, compute='_compute_gst',
                          digits=dp.get_precision('Product Price'))
    sale_price = fields.Float('Offer Price/Product')
    discount = fields.Float('Discount')
    forecost_qty = fields.Float('Forecasted Qty')
    product_available_qty = fields.Float(compute="_available_qty",string='Available Qty',store=True)
    subtotal = fields.Float('Subtotal',compute="_price_subtotal", store=True)
    company_id = fields.Many2one('res.company', 'Company',
                                 default=lambda self: self.env['res.company']._company_default_get('package.design'))
    qty_available = fields.Float(compute="_available_qty",string='Available quantity')

    def product_change(self):
        for line in self:
            if not line.product_id:
                return True
            if line.product_id.hsn_code:
                branch_state = line.order_kit_id.company_id.state_id
                partner_state = line.order_kit_id.partner_id.state_id
                invoice_addres_id = line.order_kit_id.partner_invoice_id.state_id
                sale_tax = []
                sale_tax2 = []
                line.hsn_id = line.product_id.hsn_code and line.product_id.hsn_code.id
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

    api.depends('product_id')
    def _available_qty(self):
        stock_loc = self.env['stock.location'].search([('name', '=', 'Stock')], limit=1)
        for line in self:
            line.product_available_qty = line.product_id.with_context(location=stock_loc.id).virtual_available or 0.0
            line.qty_available = line.product_id.with_context(location=stock_loc.id).qty_available or 0.0

    @api.depends('sale_price', 'qty', 'tax_id.tax_type', 'tax_id.type_tax_use', 'discount')
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
                cgst_rate = cgst_total / 100
                sgst_rate = sgst_total / 100
                igst_rate = igst_total / 100
            base = rec.sale_price * (1 - (rec.discount or 0.0) / 100.0)
            rec.cgst = (base * rec.qty) * cgst_rate
            rec.sgst = (base * rec.qty) * sgst_rate
            rec.igst = (base * rec.qty) * igst_rate
            rec.amount = (base * rec.qty) + rec.cgst + rec.sgst + rec.igst


    def approve_sample(self):
        action_id = self.env.ref('sale.action_quotations').id
        params = "/web#id=%s&view_type=form&model=sale.order&action=%s" % (
            self.id, action_id
        )
        template = self.env.ref('qms_sale_orders.approved_mail_template')
        current_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        sale_url = str(current_url) + str(params)
        template.email_from = self.env.user.login
        template.email_to = self.user_id.partner_id.email or ''
        template.body_html = template.body_html.replace('_sale_url', sale_url)
        template.send_mail(self.id, force_send=True)
        template.body_html = template.body_html.replace(sale_url, '_sale_url')
        self.write({
            'sample_state': 'sample_approved',
            'sample_approved_by': self.env.user.id,
            'is_sample_approved': True,
            'is_sample_approval': False,
        })
        # POOJA: Add sample confirm at approve sample
        self.action_confirm()





    def _prepare_invoice_line(self, qty):
        """
        method inherit for send hsn form order line to invoice line
        Prepare the dict of values to create the new invoice line for a sales order line.

        :param qty: float quantity to invoice
        """
        self.ensure_one()
        res = {}
        account = self.product_id.property_account_income_id or self.product_id.categ_id.property_account_income_categ_id
        if not account:
            raise UserError(
                _('Please define income account for this product: "%s" (id:%d) - or for its category: "%s".') %
                (self.product_id.name, self.product_id.id, self.product_id.categ_id.name))

        fpos = self.order_id.fiscal_position_id or self.order_id.partner_id.property_account_position_id
        if fpos:
            account = fpos.map_account(account)

        res = {
            'name': self.name,
            'sequence': self.sequence,
            'origin': self.order_id.name,
            'account_id': account.id,
            'price_unit': self.price_unit,
            'quantity': qty,
            'hsn_id': self.hsn_id.id or False,
            'lot_ids': [(6, 0, self.lot_ids.ids)],
            'discount': self.discount,
            'uom_id': self.product_uom.id,
            'product_id': self.product_id.id or False,
            'layout_category_id': self.layout_category_id and self.layout_category_id.id or False,
            'invoice_line_tax_ids': [(6, 0, self.tax_id.ids)],
            'account_analytic_id': self.order_id.analytic_account_id.id,
            'analytic_tag_ids': [(6, 0, self.analytic_tag_ids.ids)],
        }
        return res


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    # NEHA: rewrite base gunction to remove unit price remove
    @api.onchange('product_uom', 'product_uom_qty')
    def product_uom_change(self):
        if not self.product_uom or not self.product_id:
            self.price_unit = 0.0
            return
        if self.order_id.pricelist_id and self.order_id.partner_id:
            product = self.product_id.with_context(
                lang=self.order_id.partner_id.lang,
                partner=self.order_id.partner_id.id,
                quantity=self.product_uom_qty,
                date=self.order_id.date_order,
                pricelist=self.order_id.pricelist_id.id,
                uom=self.product_uom.id,
                fiscal_position=self.env.context.get('fiscal_position')
            )
            # self.price_unit = self.env['account.tax']._fix_tax_included_price_company(self._get_display_price(product), product.taxes_id, self.tax_id, self.company_id)

    def _compute_return_amt(self):
        picking = self.env['stock.picking']
        for rec in self:
            if rec.order_id.sale_type == 'sample_gift':
                if rec.order_id.user_id.is_salesperson:
                    if rec.state == 'done' or rec.state == 'sale':
                        if rec.return_amount == 0.0:
                            picking_id = picking.search([('sale_id', '=', rec.order_id.id),
                                                         ('state', '=', 'done')])
                            if picking_id:
                                # NEHA: add loop for picking multiple values
                                for pic in picking_id:
                                    if pic.amount_returned == False:
                                        for line in pic.move_lines:
                                            if line.sale_line_id.type == 'sample':
                                                line.sale_line_id.return_amount = line.quantity_done * line.sale_line_id.price_unit
                                                line.sale_line_id.write({'return_status': 'return','returned_date': fields.Datetime.now()})
                                                rec.order_id.sudo().user_id.write({
                                                                                    'used_sale_amt': rec.order_id.user_id.used_sale_amt - rec.return_amount})
                                                picking_id.write({'amount_returned': True})
                                                return_amount = 0.0

    location_type = fields.Selection(string="Location Type",
                                     selection=[('from_sample', 'From Sample'),
                                                ('from_stock', 'From Stock'), ], required=False, )

    type = fields.Selection([('sample','Sample'),('gift','Gift'),('pending', 'Pending')],default="sample",string='Type')
    gift_qty = fields.Integer('Gift Quantity', default=0)
    line_status = fields.Selection([('need_approval','Need Approval'),('approved','Approved'),('rejected','Rejected')],default='approved',string='Status')
    return_amount = fields.Float(compute="_compute_return_amt",string='Return Amt')
    date_order = fields.Datetime(related='order_id.date_order',store=True,string="System Date")
    sample_confirm_date = fields.Date('Sample Date')
    partner_id = fields.Many2one(related='order_id.partner_id',store=True)
    partner_company_id = fields.Many2one('res.partner',compute="partner_company",store=True,string='Organization')
    # product_status = fields.Selection([('returnable','Returnable'),('non-')])
    return_status = fields.Selection([('new','New'),('waiting_delivery','Waiting For Delivery'),('return','Returned'),
                                      ('nothing', 'Nothing To Return'),
                                      ('waiting_return','Waiting For Return'),
                                      ('cancel','Cancelled')],string="Status",default='new')
    sample_punched_id = fields.Many2one('res.users',default=lambda self: self.env.user,string="Sample punched by")
    allotment_date = fields.Date(string='Allotment Date')
    returned_date = fields.Date('Returned Date')
    lot_ids = fields.Many2many('stock.production.lot', 'lot_line_ref', 'line_id', 'lot_id', string='Lot')
    remarks = fields.Char('Remarks')
    virtual_available = fields.Float(compute="_compute_qty_location",string='Forecasted quantity')
    qty_available = fields.Float(compute="_compute_qty_location",string='Available quantity')
    return_qty = fields.Float('Return Qty', default=0.0)
    cost_price = fields.Float(related='product_id.product_tmpl_id.standard_price',string='Purchase  value  pre GST')
    attach_slide = fields.Boolean('Attach Slide?')
    pending_qty = fields.Float('Pending Qty', compute="compute_pending_qty", store=True, default=0.0)
    is_kit = fields.Boolean(default=False)
    mrp = fields.Float('MRP')
    msp = fields.Float('MSP')
    product_id = fields.Many2one('product.product', string='Product', domain=[('sale_ok', '=', True)],
                                 change_default=True, ondelete='restrict', required=True, track_visibility='onchange')
    qty_per_kit = fields.Integer('Qty/Kit', default=0)
    converted_to_gift = fields.Boolean('Converted to Gift', copy=False, index=True)
    state = fields.Selection(selection_add=[('rejected', 'Rejected')])


    def _prepare_purchase_order_line_packing(self, name, product_qty=0.0, price_unit=0.0, taxes_ids=False):
        self.ensure_one()
        return {
            'name': name,
            'product_id': self.product_id.id,
            'product_uom': self.product_id.uom_po_id.id,
            'product_qty': product_qty,
            'price_unit': price_unit,
            'taxes_id': [(6, 0, taxes_ids)],
            'date_planned': fields.Date.today(),
            # 'account_analytic_id': self.account_analytic_id.id,
            # 'move_dest_ids': self.move_dest_id and [(4, self.move_dest_id.id)] or []
        }

    @api.depends('product_uom_qty', 'discount', 'price_unit', 'tax_id')
    def _compute_amount(self):
        """
        Compute the amounts of the SO line.
        """
        for line in self:
            price = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
            taxes = line.tax_id.compute_all(price, line.order_id.currency_id, line.product_uom_qty,
                                            product=line.product_id, partner=line.order_id.partner_shipping_id)
            line.update({
                'price_tax': sum(t.get('amount', 0.0) for t in taxes.get('taxes', [])),
                'price_total': taxes['total_included'],
                'price_subtotal': taxes['total_excluded'],
            })

    def _compute_qty_location(self):
        stock_loc = self.env['stock.location'].search([('name', 'ilike', 'Stock')])
        sample_loc = self.env['stock.location'].search([('name', '=', 'Sample Location')], limit=1)
        for line in self:
            if line.order_id.sale_type == 'sale':
                line.virtual_available = line.product_id.with_context(location=stock_loc.ids).virtual_available
                line.qty_available = line.product_id.with_context(location=stock_loc.ids).qty_available
            if line.order_id.sale_type == 'sample_gift':
                line.virtual_available = line.product_id.with_context(location=sample_loc.id).virtual_available
                line.qty_available = line.product_id.with_context(location=sample_loc.id).qty_available

    @api.onchange('qty_per_kit', 'order_id')
    def onchange_kit_per_qty(self):
        """method for multiply kit_per_qty into kit_qty """
        if self.order_id.is_kit:
            self.product_uom_qty = self.qty_per_kit

    @api.depends('return_qty', 'product_uom_qty', 'qty_delivered', 'order_id.gift_convert_approved')
    def compute_pending_qty(self):
        for line in self:
            if line.qty_delivered > 0.0:
                line.pending_qty = line.product_uom_qty - line.return_qty
                if line.order_id.gift_convert_approved is True:
                    line.pending_qty = line.product_uom_qty - line.return_qty - line.gift_qty

    @api.onchange('product_id')
    def product_onchange(self):
        for rec in self:
            if rec.product_id:
                rec.virtual_available = rec.product_id.virtual_available
                # rec.qty_available = rec.product_id.qty_available
                # rec.mrp = rec.product_id.mrp
                # rec.msp = rec.product_id.list_price
                rec.return_qty = 0.0
                rec.pending_qty = 0.0

    @api.depends('partner_id')
    def partner_company(self):
        for rec in self:
            if rec.partner_id.parent_id:
                rec.partner_company_id = rec.partner_id.parent_id.id
            else:
                rec.partner_company_id = rec.partner_id.id



    def convert_to_gift(self):
        template = self.env.ref('qms_sale_orders.convert_line_sample_to_gift')
        action_id = self.env.ref('qms_sale_orders.action_sample_sale_order').id
        params = "/web#id=%s&view_type=form&model=sale.order&action=%s" % (
            self.id, action_id)
        current_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        sale_approve_group = self.env.ref('qms_sale_orders.group_sample_approved')
        email_to = ' '
        for user in sale_approve_group.sudo().users:
            email_to = email_to + user.partner_id.email + ','
        convert_line = str(current_url) + str(params)
        template.email_from = self.env.user.login
        template.email_to = self.user_id.partner_id.email or ''
        template.body_html = template.body_html.replace('convert_line', convert_line)
        template.send_mail(self.id, force_send=True)
        template.body_html = template.body_html.replace(convert_line, 'convert_line')
        for line in self.order_line:
            line.type = 'gift'
            line.return_status = 'nothing'
            line.order_id.sudo().user_id.write({
                'used_sale_amt': line.order_id.user_id.used_sale_amt - line.price_subtotal})


    def _get_delivered_qty(self):
        ''' method inherit for update lot no in order line'''
        self.ensure_one()
        super(SaleOrderLine, self)._get_delivered_qty()
        qty = 0.0
        lot_lst = []
        for move in self.move_ids.filtered(lambda r: r.state == 'done' and not r.scrapped):
            if move.location_dest_id.usage == "customer":
                if not move.origin_returned_move_id:
                    qty += move.product_uom._compute_quantity(move.product_uom_qty, self.product_uom)
            elif move.location_dest_id.usage != "customer" and move.to_refund:
                qty -= move.product_uom._compute_quantity(move.product_uom_qty, self.product_uom)
            for line in move.move_line_ids:
                if line.lot_id:
                    lot_lst.append(line.lot_id.id)
                    self.allotment_date = fields.Datetime.now()
            self.lot_ids = [(6,0, lot_lst)]
        return qty

    @api.onchange('price_subtotal', 'type')
    def onchange_price(self):
        for rec in self:
            if rec.order_id.sale_type == 'sample_gift':
                if rec.price_subtotal:
                    if rec.type == 'gift':
                        if rec.price_subtotal > rec.order_id.gift_amt:
                            rec.line_status = 'need_approval'
                        if rec.price_subtotal <= rec.order_id.gift_amt:
                            rec.line_status = 'approved'
                    if rec.type == 'sample':
                        rec.line_status = 'approved'


    def approved(self):
        order_line = self.env['sale.order.line'].search([('order_id','=', self.order_id.id)])
        self.write({'line_status': 'approved', 'sample_confirm_date': fields.Datetime.now()})
        approve_lst = []
        reject_lst = []
        need_approved_lst = []
        for line in order_line:
            if line.line_status == 'approved':
                approve_lst.append(line.id)
            if line.line_status == 'rejected':
                reject_lst.append(line.id)
            if line.line_status == 'need_approval':
                need_approved_lst.append(line.id)
        if approve_lst and not need_approved_lst:
            self.order_id.approved_all()



    def reject(self):
        order_line = self.env['sale.order.line'].search([('order_id', '=', self.order_id.id),
                                                         ])
        lines = order_line.filtered(lambda s: s.line_status in ['approved'])
        self.write({'line_status': 'rejected', 'state': 'cancel'})
        approve_lst = []
        reject_lst = []
        need_approved_lst = []
        for line in order_line:
            if line.line_status == 'approved':
                approve_lst.append(line.id)
            if line.line_status == 'rejected':
                reject_lst.append(line.id)
            if line.line_status == 'need_approval':
                need_approved_lst.append(line.id)
        if approve_lst and not need_approved_lst:
            self.order_id.approved_all()
        if reject_lst and not approve_lst and not need_approved_lst:
            self.order_id.reject_all()


    def _prepare_invoice_line(self, qty):
        """
        method inherit for send hsn form order line to invoice line
        Prepare the dict of values to create the new invoice line for a sales order line.

        :param qty: float quantity to invoice
        """
        self.ensure_one()
        res = {}
        account = self.product_id.property_account_income_id or self.product_id.categ_id.property_account_income_categ_id
        if not account:
            raise UserError(
                _('Please define income account for this product: "%s" (id:%d) - or for its category: "%s".') %
                (self.product_id.name, self.product_id.id, self.product_id.categ_id.name))

        fpos = self.order_id.fiscal_position_id or self.order_id.partner_id.property_account_position_id
        if fpos:
            account = fpos.map_account(account)

        res = {
            'name': self.name,
            'sequence': self.sequence,
            'origin': self.order_id.name,
            'account_id': account.id,
            'price_unit': self.price_unit,
            'quantity': qty,
            'hsn_id': self.hsn_id.id or False,
            'lot_ids': [(6,0, self.lot_ids.ids)],
            'discount': self.discount,
            'uom_id': self.product_uom.id,
            'product_id': self.product_id.id or False,
            'layout_category_id': self.layout_category_id and self.layout_category_id.id or False,
            'invoice_line_tax_ids': [(6, 0, self.tax_id.ids)],
            'account_analytic_id': self.order_id.analytic_account_id.id,
            'analytic_tag_ids': [(6, 0, self.analytic_tag_ids.ids)],
        }
        return res


    def invoice_line_create(self, invoice_id, qty):
        ''' Method inherit for create SO line which is comfirmed'''
        invoice_lines = self.env['account.move.line']
        precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')
        for line in self:
            if not float_is_zero(qty, precision_digits=precision):
                if line.line_status != 'rejected':
                    vals = line._prepare_invoice_line(qty=qty)
                    vals.update({'invoice_id': invoice_id, 'sale_line_ids': [(6, 0, [line.id])]})
                    invoice_lines |= self.env['account.move.line'].create(vals)
        return invoice_lines

    def _prepare_invoice_line(self, qty):
        """
        method inherit for send hsn form order line to invoice line
        Prepare the dict of values to create the new invoice line for a sales order line.

        :param qty: float quantity to invoice
        """
        self.ensure_one()
        res = {}
        account = self.product_id.property_account_income_id or self.product_id.categ_id.property_account_income_categ_id
        if not account:
            raise UserError(
                _('Please define income account for this product: "%s" (id:%d) - or for its category: "%s".') %
                (self.product_id.name, self.product_id.id, self.product_id.categ_id.name))

        fpos = self.order_id.fiscal_position_id or self.order_id.partner_id.property_account_position_id
        if fpos:
            account = fpos.map_account(account)

        res = {
            'name': self.name,
            'sequence': self.sequence,
            'origin': self.order_id.name,
            'account_id': account.id,
            'price_unit': self.price_unit,
            'quantity': qty,
            'hsn_id': self.hsn_id.id or False,
            'lot_ids': [(6, 0, self.lot_ids.ids)],
            'discount': self.discount,
            'uom_id': self.product_uom.id,
            'product_id': self.product_id.id or False,
            'layout_category_id': self.layout_category_id and self.layout_category_id.id or False,
            'invoice_line_tax_ids': [(6, 0, self.tax_id.ids)],
            'account_analytic_id': self.order_id.analytic_account_id.id,
            'analytic_tag_ids': [(6, 0, self.analytic_tag_ids.ids)],
        }
        return res


    def _prepare_procurement_values_kit(self, group_id=False):
        """ Prepare specific key for moves or other components that will be created from a procurement rule
        comming from a sale order line. This method could be override in order to add other custom key that could
        be used in move/po creation.
        """
        values = {}
        self.ensure_one()
        date_planned = datetime.strptime(self.order_id.confirmation_date, DEFAULT_SERVER_DATETIME_FORMAT) \
                       + timedelta(days=self.customer_lead or 0.0) - timedelta(
            days=self.order_id.company_id.security_lead)
        values.update({
            'company_id': self.order_id.company_id,
            'group_id': group_id,
            # 'sale_line_id': self.id,
            'date_planned': date_planned.strftime(DEFAULT_SERVER_DATETIME_FORMAT),
            'route_ids': self.route_id,
            'warehouse_id': self.order_id.warehouse_id or False,
            'partner_dest_id': self.order_id.partner_shipping_id,
            'sale_id': self.order_id.id,
        })
        return values





class PackingLine(models.Model):
    _name = 'packing.line'

    pack_order_id = fields.Many2one('sale.order')
    product_id = fields.Many2one('product.product','Customization Name')
    customize_name = fields.Char('Customization Name')
    type = fields.Char('Type')
    size = fields.Char('Size')
    price = fields.Float('Cost To Us/Piece')
    description = fields.Char('Description')
    quantity = fields.Integer('Quantity', default=0)
    total = fields.Float(compute="_compute_total",string='Total',store=True)
    company_id = fields.Many2one('res.company', 'Company',
                                 default=lambda self: self.env['res.company']._company_default_get('package.design'))




    def _prepare_purchase_order_line_packing(self, name, product_qty=0.0, price_unit=0.0, taxes_ids=False):
        self.ensure_one()
        sale = self.pack_order_id
        return {
            'name': name,
            'product_id': self.product_id.id,
            'product_uom': self.product_id.uom_po_id.id,
            'product_qty': product_qty,
            'price_unit': price_unit,
            'taxes_id': [(6, 0, taxes_ids)],
            'date_planned': fields.Date.today(),
            # 'account_analytic_id': self.account_analytic_id.id,
            # 'move_dest_ids': self.move_dest_id and [(4, self.move_dest_id.id)] or []
        }

    @api.depends('quantity', 'price')
    def _compute_total(self):
        for line in self:
            line.total = line.quantity * line.price

    @api.onchange('product_id')
    def product_id_change(self):
        for line in self:
            line.description = line.product_id.name
