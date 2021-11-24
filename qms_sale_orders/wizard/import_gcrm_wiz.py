from odoo import api, models, fields, _
from odoo.exceptions import UserError
import xlrd
import math
import base64
import logging
from io import BytesIO
from odoo.tools import pycompat
import string
from xlrd import open_workbook
from datetime import datetime
logger = logging.getLogger('Import')


class ImportGcrm(models.TransientModel):
    _name = 'import.gcrm'

    excel_file = fields.Binary('Import File')


    def import_excel(self):
        ''''''
        user_obj = self.env['res.users']
        sale_obj = self.env['sale.order']
        division_obj = self.env['division']
        product = self.env['product.product']
        partner_obj = self.env['res.partner']
        order_line = self.env['sale.order.line']
        system_date = 0
        organization = 0
        division = 0
        req_from = 0
        req_date = 0
        sales_exe = 0
        # punch_by = 0
        dr_name = 0
        sap_code = 0
        rm_name = 0
        region = 0
        gcrm_no = 0
        # products = 0
        qty = 0
        price = 0
        delivery = 0
        update_list, order_list = [], []
        if not self.excel_file:
            raise UserError(_('Please add file'))
        val = base64.decodestring(self.excel_file)
        fp = BytesIO()
        fp.write(val)
        book = xlrd.open_workbook(file_contents=fp.getvalue())
        sh = book.sheet_by_index(0)
        if sh.ncols != 15:
            raise UserError(_('Required column is missing please check sheet you are importing!!!'))
        logger.info('row count : %d', sh.nrows)
        for line in range(0, sh.nrows):  # sh.nrows
            row = sh.row_values(line)
            update_list.append(row[0].lower().rstrip(' '))
            update_list.append(row[1].lower().rstrip(' '))
            update_list.append(row[2].lower().rstrip(' '))
            update_list.append(row[3].lower().rstrip(' '))
            update_list.append(row[4].lower().rstrip(' '))
            update_list.append(row[5].lower().rstrip(' '))
            update_list.append(row[6].lower().rstrip(' '))
            update_list.append(row[7].lower().rstrip(' '))
            update_list.append(row[8].lower().rstrip(' '))
            update_list.append(row[9].lower().rstrip(' '))
            update_list.append(row[10].lower().rstrip(' '))
            update_list.append(row[11].lower().rstrip(' '))
            update_list.append(row[12].lower().rstrip(' '))
            update_list.append(row[13].lower().rstrip(' '))
            update_list.append(row[14].lower().rstrip(' '))
            # update_list.append(row[14].lower().rstrip(' '))
            if 'system date (punch date)' not in update_list:
                raise UserError(_('Column header name does not match please replace with [system date (punch date)] !!'))
            system_date = update_list.index('system date (punch date)')
            if 'organization' not in update_list:
                raise UserError(_('Column header name does not match please replace with [organization] !!'))
            organization = update_list.index('organization')
            if 'division' not in update_list:
                raise UserError(_('Column header name does not match please replace with [division] !!'))
            division = update_list.index('division')
            if 'requisition from' not in update_list:
                raise UserError(_('Column header name does not match please replace with [requisition from] !!'))
            req_from = update_list.index('requisition from')
            if 'requisition date' not in update_list:
                raise UserError(_('Column header name does not match please replace with [requisition date] !!'))
            req_date = update_list.index('requisition date')
            if 'sales executive' not in update_list:
                raise UserError(_('Column header name does not match please replace with [sales executive] !!'))
            sales_exe = update_list.index('sales executive')
            # if 'punch by' not in update_list:
            #     raise UserError(_('Column header name does not match please replace with [punch by] !!'))
            # punch_by = update_list.index('punch by')
            if 'dr name' not in update_list:
                raise UserError(_('Column header name does not match please replace with [dr name] !!'))
            dr_name = update_list.index('dr name')
            if 'sap code' not in update_list:
                raise UserError(_('Column header name does not match please replace with [sap code] !!'))
            sap_code = update_list.index('sap code')
            if 'rm name' not in update_list:
                raise UserError(_('Column header name does not match please replace with [rm name] !!'))
            rm_name = update_list.index('rm name')
            if 'region' not in update_list:
                raise UserError(_('Column header name does not match please replace with [region] !!'))
            region = update_list.index('region')
            if 'gcrm  no.' not in update_list:
                raise UserError(_('Column header name does not match please replace with [gcrm  no.] !!'))
            gcrm_no = update_list.index('gcrm  no.')
            if 'product name' not in update_list:
                raise UserError(_('Column header name does not match please replace with [product name] !!'))
            products = update_list.index('product name')
            if 'price' not in update_list:
                raise UserError(_('Column header name does not match please replace with [price] !!'))
            price = update_list.index('price')
            if 'qty' not in update_list:
                raise UserError(_('Column header name does not match please replace with [qty] !!'))
            qty = update_list.index('qty')
            if 'delivery address' not in update_list:
                raise UserError(_('Column header name does not match please replace with [delivery address] !!'))
            delivery = update_list.index('delivery address')
            break
        for line in range(1, sh.nrows):  # sh.nrows
            row = sh.row_values(line)
            type = isinstance(row[system_date], float)
            type_date = isinstance(row[req_date], float)
            if type == True:
                seconds = (row[system_date] - 25569) * 86400.0
                date = datetime.utcfromtimestamp(seconds)
                row_date = date.strftime('%Y/%m/%d')
            else:
                row_date = row[system_date]
            if type_date is True:
                seconds1 = (row[req_date] - 25569) * 86400.0
                convert_date = datetime.utcfromtimestamp(seconds1)
                requestion_date = convert_date.strftime('%Y/%m/%d')
            else:
                requestion_date = row[req_date]
            partner = partner_obj.search([('name','=',row[organization].rstrip(' '))], limit=1)
            if not partner:
                raise UserError(_('Customer does not match in the system for line'
                                  ' "%s" !!!') % (line + 1))
            partner_shipping = partner.child_ids.filtered(
                lambda c: (c.name == str(row[delivery]).strip()) and c.type == 'delivery')
            if not partner_shipping:
                if str(row[organization]).rstrip(' ') == str(row[delivery]).strip():
                    partner_shipping = partner
                if not partner:
                    raise UserError(_('Delivery address does not match in the system for '
                                      'row "%s" !!!') % (line + 1))
            if row[products]:
                product_id = product.search([('name', '=', row[products].rstrip(' '))], limit=1)
                if not product_id:
                    raise UserError(_('Product does not match in the system for '
                                      'row "%s" !!!') % (line + 1))
            division_id = division_obj.search([('name', '=', row[division].rstrip(' '))])
            if not division_id:
                raise UserError(_('Division does not match in the system for '
                                      'row "%s" !!!') % (line + 1))
            user_id = user_obj.search([('name', '=', row[sales_exe].rstrip(' '))])
            if not user_id:
                raise UserError(_('Sales executive does not match in the system for '
                                      'row "%s" !!!') % (line + 1))
            sale_id = sale_obj.sudo().create({
                'partner_id': partner.id,
                'partner_shipping_id': partner_shipping.id or partner.id,
                'sale_type': 'gcrm',
                'sap_code': row[sap_code],
                'rm_name': row[rm_name],
                'region': row[region],
                'gcrm_no': row[gcrm_no],
                'requisition_from': row[req_from],
                'requisition_date': requestion_date,
                'division_id': division_id.id,
                'date_order': row_date,
                'user_id': user_id.id,
                # 'punch_by': row[punch_by],
                'dr_name': row[dr_name],
                'delivery_address': row[delivery]
            })
            order_line.create({
                'product_id': product_id.id,
                'order_id': sale_id.id,
                'name': product_id.name,
                'product_uom_qty': row[qty],
                'price_unit': row[price]
            })
            order_list.append(sale_id.id)
        action = self.env.ref('qms_sale_orders.action_gcrm_order_unprocessed').read()[0]
        if len(order_list) > 1:
            action['domain'] = [('id', 'in', order_list)]
        return action