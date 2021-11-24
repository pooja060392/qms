# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _

class ResPartner(models.Model):
    _inherit = 'res.partner'

    text = fields.Char('text')
    dob = fields.Date('Date of Birth')
    contact_count = fields.Integer(compute='compute_contact_count')
    user_id = fields.Many2one('res.users', string='Salesperson')
    fax_no = fields.Char("Fax Number")
    brand_ids = fields.Many2many('brand', 'brand_partner_rel', 'brand_id', 'part_id', 'Brand')
    related_brand = fields.Char(compute="_compute_brand", string='Brand', store=True)
    related_division = fields.Char(compute="_compute_division", string='Division', store=True)
    division_ids = fields.Many2one('division','Division')
    new_brand_ids = fields.Many2many('brand', 'new_brand_partner_rel', 'brands_id', 'partner_id', 'Brand')
    new_division_ids = fields.Many2many('division', 'new_partner_div_rel', 'partners_id', 'division_id', 'Division')
    collect_brand_ids = fields.Many2many(
        'brand',
        'rel_col_brand_part',
        'col_brand_id',
        'col_partner_id',
        string='Associated Brands',
    )
    collect_division_ids = fields.Many2many(
        'division',
        'rel_col_div_part',
        'col_div_id',
        'col_partner_div_id',
        string='Associated Division',
    )
    customer = fields.Boolean(string='Is a Customer', default=True,
                              help="Check this box if this contact is a customer.")
    supplier = fields.Boolean(string='Is a Principal',
                              help="Check this box if this contact is a vendor. "
                                   "If it's not checked, purchase people will not see it when encoding a purchase order.")



    @api.onchange('parent_id')
    def _onchange_parent_id(self):
        if self.parent_id:
            list_ = []
            for data in self.parent_id.new_division_ids:
                list_.append(data.id)
            for data in self.parent_id.new_brand_ids:
                list_.append(data.id)
            self.new_division_ids = [(6, 0, self.parent_id.new_division_ids.ids)]
            self.new_brand_ids = [(6, 0, self.parent_id.new_brand_ids.ids)]

    @api.model
    def default_get(self, default_fields):
        res = super(ResPartner, self).default_get(default_fields)
        if 'parent_id' in res:
            search_id = self.env['res.partner'].browse(res['parent_id'])
            list_ = []
            for data in search_id.new_brand_ids:
                list_.append(data.id)
            res['new_brand_ids'] = [(6, 0, search_id.new_brand_ids.ids)]
            for data in search_id.new_division_ids:
                list_.append(data.id)
            res['new_division_ids'] = [(6, 0, search_id.new_division_ids.ids)]
        return res

    @api.onchange('company_type')
    def onchnage_company_type(self):
        if self.company_type:
            if self.company_type == 'company':
                if self.brand_ids or self.category_id:
                    self.brand_ids = [(6, 0, [])]
                    self.category_id = [(6, 0, [])]

    @api.depends('brand_ids')
    def _compute_brand(self):
        append_name = ''
        for record in self:
            if record.brand_ids:
                for res in record.brand_ids:
                    append_name = append_name + res.name + ','
                record.related_brand = append_name.rstrip(',')

    @api.depends('division_ids')
    def _compute_division(self):
        append_name = ''
        for record in self:
            if record.division_ids:
                for res in record.division_ids:
                    append_name = append_name + res.name + ','
                record.related_division = append_name.rstrip(',')

    @api.depends('contact_count')
    def compute_contact_count(self):
        for res in self:
            count = self.env['res.partner'].search_count([('parent_id', '=', res.id)])
            res.contact_count = count


    def childs_contact(self):
        self.ensure_one()
        partner = self.env['res.partner']
        partner_data = partner.search([('parent_id', 'in', self.ids)])
        action = self.env.ref('qms_contact.action_for_individual_contact').read()[0]
        action['domain'] = [('id', 'in', partner_data.ids)]
        return action

    @api.depends('contact_count')
    def compute_contact_count(self):
        for res in self:
            count = self.env['res.partner'].search_count([('parent_id', '=', res.id)])
            res.contact_count = count



    def childs_contact(self):
        self.ensure_one()
        partner = self.env['res.partner']
        partner_data = partner.search([('parent_id', 'in', self.ids)])
        action = self.env.ref('qms_contact.action_for_individual_contact').read()[0]
        action['domain'] = [('id', 'in', partner_data.ids)]
        return action


    def name_get(self):
        res = []
        for partner in self:
            name = partner.name or ''
            if partner.company_name or partner.parent_id:
                if not name and partner.type in ['invoice', 'delivery', 'other']:
                    name = dict(self.fields_get(['type'])['type']['selection'])[partner.type]
                if not partner.is_company:
                    name = "%s [%s]" % (partner.commercial_company_name or partner.parent_id.name, name)
            if self._context.get('show_address_only'):
                name = partner._display_address(without_company=True)
            if self._context.get('show_address'):
                name = name + "\n" + partner._display_address(without_company=True)
            name = name.replace('\n\n', '\n')
            name = name.replace('\n\n', '\n')
            if self._context.get('show_email') and partner.email:
                name = "%s <%s>" % (name, partner.email)
            if self._context.get('html_format'):
                name = name.replace('\n', '<br/>')
            res.append((partner.id, name))

        return res


class ResUser(models.Model):
    _inherit = 'res.users'

    @api.depends('used_sale_amt','sale_amount')
    def _remaning_sale_amt(self):
        for rec in self:
            if rec.used_sale_amt or rec.sale_amount:
                rec.remaining_sale_amt = rec.sale_amount - rec.used_sale_amt

    is_salesperson = fields.Boolean('Salesperson')
    sale_amount = fields.Float('Maximum Sample Amount')
    used_sale_amt = fields.Float('Consumed Sample Amount')
    remaining_sale_amt = fields.Float(compute="_remaning_sale_amt",string='Remaining Sample Amount',store=True)
    sale_target = fields.Float('Monthly Sales Target')