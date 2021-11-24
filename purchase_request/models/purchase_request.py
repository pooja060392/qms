# -*- coding: utf-8 -*-
# Copyright 2016 Eficent Business and IT Consulting Services S.L.
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl-3.0).

from odoo import api, fields, models, _
from odoo.exceptions import UserError, Warning
import odoo.addons.decimal_precision as dp
from datetime import datetime


_STATES = [
    ('draft', 'Draft'),
    ('to_approve', 'To be approved'),
    ('approved', 'Approved'),
    ('rejected', 'Rejected'),
    ('rfq', 'RFQ'),
    ('done', 'PO Confirmed')
]


class PurchaseRequest(models.Model):

    _name = 'purchase.request'
    _description = 'Purchase Request'
    _inherit = ['mail.thread']

    @api.model
    def _company_get(self):
        company_id = self.env['res.company']._company_default_get(self._name)
        return self.env['res.company'].browse(company_id.id)

    @api.model
    def _get_default_requested_by(self):
        return self.env['res.users'].browse(self.env.uid)

    @api.model
    def _get_default_name(self):
        return self.env['ir.sequence'].next_by_code('purchase.request')

    @api.model
    def _default_picking_type(self):
        type_obj = self.env['stock.picking.type']
        company_id = self.env.context.get('company_id') or \
            self.env.user.company_id.id
        types = type_obj.search([('code', '=', 'incoming'),
                                 ('warehouse_id.company_id', '=', company_id)])
        if not types:
            types = type_obj.search([('code', '=', 'incoming'),
                                     ('warehouse_id', '=', False)])
        return types[:1]


    @api.depends('state')
    def _compute_is_editable(self):
        for rec in self:
            if rec.state in ('to_approve', 'approved', 'rejected', 'rfq','done'):
                rec.is_editable = False
            else:
                rec.is_editable = True


    def _track_subtype(self, init_values):
        for rec in self:
            if 'state' in init_values and rec.state == 'to_approve':
                return 'purchase_request.mt_request_to_approve'
            elif 'state' in init_values and rec.state == 'approved':
                return 'purchase_request.mt_request_approved'
            elif 'state' in init_values and rec.state == 'rejected':
                return 'purchase_request.mt_request_rejected'
            elif 'state' in init_values and rec.state == 'done':
                return 'purchase_request.mt_request_done'
        return super(PurchaseRequest, self)._track_subtype(init_values)

    project_id = fields.Many2one('project.category', 'Project', index=True)
    sector_id = fields.Many2one('project.project', 'Sector', index=True)
    name = fields.Char('Request Reference', size=32, required=True,
                       default=_get_default_name,
                       track_visibility='onchange')
    origin = fields.Char('Source Document', size=32)
    date_start = fields.Date('Creation date',
                             help="Date when the user initiated the "
                                  "request.",
                             default=fields.Date.context_today,
                             track_visibility='onchange')
    requested_by = fields.Many2one('res.users',
                                   'Requested by',
                                   required=True,
                                   track_visibility='onchange',
                                   default=_get_default_requested_by)
    assigned_to = fields.Many2one('res.users', 'Approver', required=1)
    description = fields.Text('Description', required=1)
    company_id = fields.Many2one('res.company', 'Company',
                                 required=True,
                                 default=_company_get,
                                 track_visibility='onchange')
    line_ids = fields.One2many('purchase.request.line', 'request_id',
                               'Products to Purchase',
                               readonly=False,
                               copy=True,
                               track_visibility='onchange')
    state = fields.Selection(selection=_STATES,
                             string='Status',
                             index=True,
                             track_visibility='onchange',
                             required=True,
                             copy=False,
                             default='draft')
    is_editable = fields.Boolean(string="Is editable",
                                 compute="_compute_is_editable",
                                 readonly=True)
    to_approve_allowed = fields.Boolean(
        compute='_compute_to_approve_allowed')
    picking_type_id = fields.Many2one('stock.picking.type',
                                      'Picking Type', required=True,
                                      default=_default_picking_type)
    reason_reject = fields.Char('Reason to Reject')

    line_count = fields.Integer(
        string='Purchase Request Line count',
        compute='_compute_line_count',
        readonly=True
    )
    supplier_id = fields.Many2many('res.partner','pr_supplier_rel','pr_id', 'supplier_id', domain=[('supplier', '=', True)])

    # to create purchase order
    @api.model
    def default_get(self, fields):
        res = super(PurchaseRequest, self).default_get(fields)
        active_id = self.env.context.get('active_id', False)
        stock_picking = self.env['stock.picking'].browse(active_id)
        if stock_picking:
            line = []
            for stock in stock_picking.move_lines:
                if stock.pr_requested == True:
                    raise UserError(_('There are no item to create PR'))
                if stock.available_quant <= stock.product_uom_qty and stock.pr_requested == False:
                    stock.pr_requested = True
                    line.append((0, 0, {'product_id': stock.product_id.id,
                                        'name': stock.product_id.name,
                                        'product_qty': stock.product_qty - (stock.available_quant),
                                        'product_uom_id': stock.product_id.uom_id.id,
                                        'date_required': datetime.today()
                                        }))
            res['requested_by'] = self.env.user.id
            res['line_ids'] = line
        return res

    @api.constrains('line_ids', 'assigned_to')
    def line_ids_validation(self):
        if not self.line_ids:
            raise UserError(_('Product Line can not be empty'))

    @api.onchange('assigned_to')
    def get_user(self):
        purchase_request_manager_group = self.env.ref('purchase_request.group_purchase_request_manager')
        return {'domain': {'assigned_to': [('id', 'in', purchase_request_manager_group.users.ids)]}}


    def create_rfq(self):
        rfq_env = self.env['purchase.order']
        for pur_request in self:
            if not pur_request.supplier_id:
                raise Warning(_('Please select supplier before generate RFQ'))
            for supplier in pur_request.supplier_id:
                line = []
                for pr_line in pur_request.line_ids:
                    line.append((0, 0, {'name': pr_line.name,
                                        'product_id':  pr_line.product_id.id,
                                        'product_uom': pr_line.product_id.uom_id.id,
                                        'price_unit': 0.0,
                                        'product_qty': pr_line.product_qty,
                                        'date_planned': fields.datetime.now()
                                        }))
                rfq_env.create({
                    'partner_id': supplier.id,
                    'order_line': line,
                    'purchase_request_id': pur_request.id,
                    'project_id': self.project_id.id,
                    'sector_id': self.sector_id.id,
                    'picking_type_id': self.picking_type_id.id
                })
            pur_request.state = 'rfq'


    @api.depends('line_ids')
    def _compute_line_count(self):
        self.line_count = len(self.mapped('line_ids'))


    def action_view_purchase_request_line(self):
        action = self.env.ref(
            'purchase_request.purchase_request_line_form_action').read()[0]
        lines = self.mapped('line_ids')
        if len(lines) > 1:
            action['domain'] = [('id', 'in', lines.ids)]
        elif lines:
            action['views'] = [(self.env.ref(
                'purchase_request.purchase_request_line_form').id, 'form')]
            action['res_id'] = lines.id
        return action


    @api.depends(
        'state',
        'line_ids.product_qty',
        'line_ids.cancelled',
    )
    def _compute_to_approve_allowed(self):
        for rec in self:
            rec.to_approve_allowed = (
                rec.state == 'draft' and
                any([
                    not line.cancelled and line.product_qty
                    for line in rec.line_ids
                ])
            )


    def copy(self, default=None):
        default = dict(default or {})
        self.ensure_one()
        default.update({
            'state': 'draft',
            'name': self.env['ir.sequence'].next_by_code('purchase.request'),
        })
        return super(PurchaseRequest, self).copy(default)

    @api.model
    def create(self, vals):
        request = super(PurchaseRequest, self).create(vals)
        if vals.get('assigned_to'):
            request.message_subscribe_users(user_ids=[request.assigned_to.id])
        return request


    def write(self, vals):
        res = super(PurchaseRequest, self).write(vals)
        for request in self:
            if vals.get('assigned_to'):
                self.message_subscribe_users(user_ids=[request.assigned_to.id])
        return res


    def button_draft(self):
        self.mapped('line_ids').do_uncancel()
        return self.write({'state': 'draft'})


    def button_to_approve(self):
        self.to_approve_allowed_check()
        return self.write({'state': 'to_approve'})


    def button_approved(self):
        return self.write({'state': 'approved'})


    def button_rejected(self):
        self.mapped('line_ids').do_cancel()
        return self.write({'state': 'rejected'})


    def button_done(self):
        return self.write({'state': 'done'})


    def check_auto_reject(self):
        """When all lines are cancelled the purchase request should be
        auto-rejected."""
        for pr in self:
            if not pr.line_ids.filtered(lambda l: l.cancelled is False):
                pr.write({'state': 'rejected'})


    def to_approve_allowed_check(self):
        for rec in self:
            if not rec.to_approve_allowed:
                raise UserError(
                    _("You can't request an approval for a purchase request "
                      "which is empty. (%s)") % rec.name)


class ReasonReject(models.Model):
    _name = 'reason.reject'

    reason_for_reject = fields.Char('Reason to Reject')
    purchase_request_id = fields.Many2one('purchase.request')


    def button_reject(self):
        # for rec in self.purchase_request_id:
            # rec.reason_reject = self.reason_for_reject
            # rec.state = 'rejected'
        return self.purchase_request_id.write({'state': 'rejected', 'reason_reject':self.reason_for_reject})


class PurchaseRequestLine(models.Model):

    _name = "purchase.request.line"
    _description = "Purchase Request Line"
    _inherit = ['mail.thread']


    @api.depends('product_id', 'name', 'product_uom_id', 'product_qty',
                 'analytic_account_id', 'date_required', 'specifications')
    def _compute_is_editable(self):
        for rec in self:
            if rec.request_id.state in ('to_approve', 'approved', 'rejected',
                                        'done'):
                rec.is_editable = False
            else:
                rec.is_editable = True


    def _compute_supplier_id(self):
        for rec in self:
            if rec.product_id:
                if rec.product_id.seller_ids:
                    rec.supplier_id = rec.product_id.seller_ids[0].name

    product_id = fields.Many2one(
        'product.product', 'Product',
        domain=[('purchase_ok', '=', True)],
        track_visibility='onchange')
    name = fields.Char('Description', size=256,
                       track_visibility='onchange')
    product_uom_id = fields.Many2one('product.uom', 'Product Unit of Measure',
                                     track_visibility='onchange')
    product_qty = fields.Float('Quantity', track_visibility='onchange',
                               digits=dp.get_precision(
                                   'Product Unit of Measure'))
    request_id = fields.Many2one('purchase.request',
                                 'Purchase Request',
                                 ondelete='cascade', readonly=True)
    company_id = fields.Many2one('res.company',
                                 related='request_id.company_id',
                                 string='Company',
                                 store=True, readonly=True)
    analytic_account_id = fields.Many2one('account.analytic.account',
                                          'Analytic Account',
                                          track_visibility='onchange')
    requested_by = fields.Many2one('res.users',
                                   related='request_id.requested_by',
                                   string='Requested by',
                                   store=True, readonly=True)
    assigned_to = fields.Many2one('res.users',
                                  related='request_id.assigned_to',
                                  string='Assigned to',
                                  store=True, readonly=True)
    date_start = fields.Date(related='request_id.date_start',
                             string='Request Date', readonly=True,
                             store=True)
    description = fields.Text(related='request_id.description',
                              string='Description', readonly=True,
                              store=True)
    origin = fields.Char(related='request_id.origin',
                         size=32, string='Source Document', readonly=True,
                         store=True)
    date_required = fields.Date(string='Request Date', required=True,
                                track_visibility='onchange',
                                default=fields.Date.context_today)
    is_editable = fields.Boolean(string='Is editable',
                                 compute="_compute_is_editable",
                                 readonly=True)
    specifications = fields.Text(string='Specifications')
    request_state = fields.Selection(string='Request state',
                                     readonly=True,
                                     related='request_id.state',
                                     selection=_STATES,
                                     store=True)
    supplier_id = fields.Many2one('res.partner',
                                  string='Preferred supplier',
                                  compute="_compute_supplier_id")

    cancelled = fields.Boolean(
        string="Cancelled", readonly=True, default=False, copy=False)

    @api.onchange('product_id')
    def onchange_product_id(self):
        if self.product_id:
            name = self.product_id.name
            if self.product_id.code:
                name = '[%s] %s' % (name, self.product_id.code)
            if self.product_id.description_purchase:
                name += '\n' + self.product_id.description_purchase
            self.product_uom_id = self.product_id.uom_id.id
            self.product_qty = 1
            self.name = name


    def do_cancel(self):
        """Actions to perform when cancelling a purchase request line."""
        self.write({'cancelled': True})


    def do_uncancel(self):
        """Actions to perform when uncancelling a purchase request line."""
        self.write({'cancelled': False})


    def write(self, vals):
        res = super(PurchaseRequestLine, self).write(vals)
        if vals.get('cancelled'):
            requests = self.mapped('request_id')
            requests.check_auto_reject()
        return res


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    purchase_request_id = fields.Many2one('purchase.request')
    project_id = fields.Many2one('project.category', 'Project', index=True)
    sector_id = fields.Many2one('project.project', 'Sector', index=True)
    approved_by = fields.Char('Approved By')
    status_po = fields.Char('status')
    date_approve = fields.Date('Date Approved')
    created_by = fields.Many2one('res.users')
    to_approve = fields.Boolean('To Approve')
    # finance_approval = fields.Many2one('res.users', string="Finance User")

    # @api.multi
    # def finance(self):
    #     self.to_approve = True
    #     self.finance_approval = self.env.user.id



    def button_confirm(self):
        res = super(PurchaseOrder, self).button_confirm()
        for po in self:
            if po.purchase_request_id:
                po.purchase_request_id.state = 'done'
            po.created_by = self.env.user.id
        return res


    def button_approve(self):
        res = super(PurchaseOrder, self).button_approve()
        self.approved_by = self.env.user.name
        self.status_po = 'Approved'
        self.date_approve = datetime.today()
        return res