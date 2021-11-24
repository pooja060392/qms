##############################################################################
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
{
    'name': 'Partner State',
    'version': '11.0.0.1',
    'category': 'Custom',
    'license': 'AGPL-3',
    'depends': [
        'contacts', 'mail', 'base', 'purchase', 'account'
    ],
    'data': [
        'security/partner_state_security.xml',
        'security/ir.model.access.csv',
        'data/res_company_data.xml',
        'data/res_users_data.xml',
        # 'data/template_data_view.xml',
        'views/res_partner_state_field_views.xml',
        'views/company_views.xml',
        'views/partner_views.xml',
        # 'views/purchase_views.xml',
        # 'views/account_invoice_view.xml',
    ],
    'demo': [
        'demo/res.partner.state_field.csv'
    ],
    'installable': True,
    'application': True
}
