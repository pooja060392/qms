from odoo import api, fields, models, _
from datetime import datetime
from odoo.exceptions import UserError, AccessError
from lxml import etree


class CRMLead(models.Model):
    _inherit = 'crm.lead'

    lead_type = fields.Selection([('sale','Sale'),('sample_gift','Sample/Gift')], default='sale',string='Type')
    create_date = fields.Date('Creation Date',default=lambda self: fields.Datetime.now())
    sample_number = fields.Integer(compute="_compute_sample", string="Number of Quotations")
    meeting_id = fields.Many2one('calendar.event', string='Related Meeting')
    opportunity_customer_id = fields.Many2one('res.partner')
    brand_ids = fields.Many2many('brand', 'brand_crm_rel', 'crm_id', 'brand_id', 'Brand')
    division_ids = fields.Many2many('division', 'division_crm_rel','crm_id', 'div_id', 'Division')
    segment_id = fields.Many2one('segment', 'Segment')
    quotation = fields.Boolean('Quotation', default=True)
    sample = fields.Boolean('Sample')
    gift_type = fields.Boolean('Gift')
    gift_number = fields.Integer(compute="_compute_gift")
    salesperson_name = fields.Char(
        related='user_id.name', string='Salesperson',
        copy=False, index=True, readonly=True, store=True
    )
    # calender_id = fields.Many2one('calendar.event', 'Opportunity', index=True, copy=False)

    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        values = self._onchange_partner_id_values(self.partner_id.id if self.partner_id else False)
        self.update(values)
        self.update({'brand_ids': [(6,0, self.partner_id.brand_ids.ids)],
                     'division_ids': [(6,0, self.partner_id.division_ids.ids)],
                     'segment_id': self.partner_id.segment_id.id})

    @api.depends('order_ids')
    def _compute_sample(self):
        for lead in self:
            total = 0.0
            nbr = 0
            for order in lead.order_ids:
                if order.sale_type == 'sample_gift':
                    nbr += 1
            lead.sample_number = nbr

    @api.depends('order_ids')
    def _compute_gift(self):
        for lead in self:
            total = 0.0
            nbr = 0
            for order in lead.order_ids:
                if order.sale_type == 'gift':
                    nbr += 1
            lead.gift_number = nbr


    @api.depends('order_ids')
    def _compute_sale_amount_total(self):
        for lead in self:
            total = 0.0
            nbr = 0
            company_currency = lead.company_currency or self.env.user.company_id.currency_id
            for order in lead.order_ids:
                if order.state in ('draft', 'sent', 'sale'):
                    if order.sale_type == 'sale':
                        nbr += 1
                if order.sale_type == 'sale':
                    if order.state not in ('draft', 'sent', 'cancel'):
                        total += order.currency_id.compute(order.amount_untaxed, company_currency)
            lead.sale_amount_total = total
            lead.sale_number = nbr

    @api.multi
    def gift(self):
        res = {
            'name': "Gift",
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': self.env.ref('qms_sale_orders.gift_sale_order_form_view').id,
            'res_model': 'sale.order',
            'context': {'default_opportunity_id': self.id,
                        'default_partner_id': self.partner_id.id,
                        'default_sale_type': 'gift'
                        }
        }
        return res

    @api.multi
    def request_sample(self):
        res = {
            'name': "Quotation",
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': self.env.ref('qms_sale_orders.sample_sale_order_form_view').id,
            'res_model': 'sale.order',
            'context': {'default_opportunity_id': self.id,
                        'default_partner_id': self.partner_id.id,
                        'default_sale_type': 'sample_gift'}
        }
        return res


    @api.multi
    def sample_view(self):
        self.ensure_one()
        sale_order = self.env['sale.order']
        sale_data = sale_order.search([('opportunity_id', 'in', self.ids),
                                       ('sale_type', '=', 'sample_gift')])
        action = self.env.ref('qms_sale_orders.action_sample_sale_order').read()[0]
        if len(sale_data) > 1:
            action['domain'] = [('id', 'in', sale_data.ids)]
        elif sale_data:
            action['views'] = [(self.env.ref('qms_sale_orders.sample_sale_order_form_view').id, 'form')]
            action['res_id'] = sale_data.id
        return action

    @api.multi
    def gift_view(self):
        self.ensure_one()
        sale_order = self.env['sale.order']
        sale_data = sale_order.search([('opportunity_id', 'in', self.ids),
                                       ('sale_type', '=', 'gift')])
        action = self.env.ref('qms_sale_orders.action_gift').read()[0]
        if len(sale_data) > 1:
            action['domain'] = [('id', 'in', sale_data.ids)]
        elif sale_data:
            action['views'] = [(self.env.ref('qms_sale_orders.gift_sale_order_form_view').id, 'form')]
            action['res_id'] = sale_data.id
        return action


    @api.model
    def create(self, values):
        res = super(CRMLead, self).create(values)
        ctx = self.env.context
        if 'default_meeting_id' in ctx:
            meeting_id = self.env['calendar.event'].search([('id', '=', ctx['default_meeting_id'])])
            meeting_id.opportunity_id = res.id
        if values.get('planned_revenue') <= 0.0:
            raise UserError(_('Expected Revenue should be greater than 0 !!!'))
        return res

    @api.multi
    def write(self, values):
        res = super(CRMLead, self).write(values)
        if self.planned_revenue <= 0.0:
            raise UserError(_('Expected Revenue should be greater than 0 !!!'))
        return res

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
        res = super(CRMLead, self).fields_view_get(view_id=view_id, view_type=view_type,
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
        res['arch'] = etree.tostring(doc, encoding='unicode')
        return res

