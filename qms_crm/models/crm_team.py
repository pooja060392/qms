from odoo import api, fields, models
from lxml import etree

class CrmTeam(models.Model):
    _inherit = 'crm.team'

    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
        res = super(CrmTeam, self).fields_view_get(view_id=view_id, view_type=view_type,
                                                   toolbar=toolbar, submenu=submenu)
        user = self.env.user.id
        sale_manager = self.env.ref('sales_team.group_sale_manager')
        users = []
        for user in sale_manager.sudo().users:
            users.append(user.id)
        doc = etree.XML(res['arch'])
        for node in doc.xpath("//field[@name='user_id']"):
            if users:
                domain = [('id','in',users)]
                node.set('domain', str(domain))
        res['arch'] = etree.tostring(doc, encoding='unicode')
        return res
