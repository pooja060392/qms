from odoo import api, fields, models, _


class Users(models.Model):
    _inherit = "res.users"


    @api.depends('groups_id')
    def _check_default(self):
        for users in self:
            if users.has_group('qms_sale_orders.group_purchase_team_packaging'):
                users.is_packaging_team = True
            if users.has_group('qms_sale_orders.group_sales_team_packaging'):
                users.is_sales_team = True
            if users.has_group('qms_sale_orders.group_gift_approval'):
                users.is_gift_approval_team = True
            if users.has_group('qms_sale_orders.group_sample_approval'):
                users.is_sample_approval_team = True


    is_packaging_team = fields.Boolean(
        string='Is Packaging Team', copy=False,
        index=True, default=False, compute='_check_default', store=True)
    is_sales_team = fields.Boolean(
        string='Is Sales Team', copy=False,
        index=True, default=False, compute='_check_default', store=True)
    is_gift_approval_team = fields.Boolean(
        string='Is Gift Approval Team', copy=False,
        index=True, default=False, compute='_check_default', store=True)
    is_sample_approval_team = fields.Boolean(
        string='Is Sample Approval Team', copy=False,
        index=True, default=False, compute='_check_default', store=True)


