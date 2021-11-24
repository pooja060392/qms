# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import Warning
import xlrd
import base64
import xlsxwriter


import logging
_logger = logging.getLogger(__name__)

try:
    import xlsxwriter
except ImportError:
    _logger.debug('Can not import xlsxwriter`.')


class StockInventory(models.Model):
    _inherit = "stock.inventory"

    file_name_details = fields.Binary('Faulty Sheet')
    faulty_file_name = fields.Char('Faulty File Name')


# TABLE : FOR PO Excell
class PurchaseExcelWizard(models.Model):
    _name = "inventory.excel.wizard"

    inventory_id = fields.Many2one('stock.inventory', string='Purchase')
    company_id = fields.Many2one('res.company', string='Company')

    def print_xls_report(self):
        data = self.read()[0]
        return {'type': 'ir.actions.report',
                'report_name': 'nuro_inventory_import.report_inventory_excel',
                'data': data
                }


# EXPORT RFQ FUNCTION
class RFQXlsx(models.AbstractModel):
    _name = 'report.nuro_inventory_import.report_inventory_excel'
    _inherit = 'report.report_xlsx.abstract'

    def generate_xlsx_report(self, workbook, data, inventory):
        for obj in inventory:
            report_name = "Inventory Items"
            sheet = workbook.add_worksheet(report_name[:31])
            header = workbook.add_format({'bold': True, 'align': 'center', 'border': 1})
            bold = workbook.add_format({'bold': False, 'align': 'center', 'border': 1})
            sheet.set_column('A:A', 18)
            sheet.set_column('B:B', 12)
            sheet.set_column('C:C', 25)
            sheet.set_column('D:D', 25)
            sheet.set_column('E:F', 20)
            sheet.set_column('G:G', 12)
            sheet.write('A1', "INVENTORY ID", header)
            sheet.write('B1', "LOCATION", header)
            sheet.write('C1', "PRODUCT", header)
            sheet.write('D1', "PRODUCT REF", header)
            sheet.write('E1', "LOCATION", header)
            sheet.write('F1', "LOT/SERIAL", header)
            sheet.write('G1', "QUANTITY", header)
            row, col = 1, 0
            sheet.write(row, col, obj.id, bold)
            sheet.write(row, col+1, obj.location_id.id, bold)
            sheet.write(row, col+2, '', bold)
            sheet.write(row, col+3, '', bold)
            sheet.write(row, col+4, obj.location_id.id, bold)
            sheet.write(row, col+5, '', bold)
            sheet.write(row, col+6, '', bold)



class RFQImport(models.TransientModel):
    _name = "stock.inventory.importation"
    _description = "import Stock Inventory xls"

    upload_file = fields.Binary(string="Upload File", required=True)
    file_name = fields.Char(string="File Name", default="Inventory Item")


    # import xls file button

    def import_xls_action(self):
        data = base64.b64decode(self.upload_file)
        with open('/tmp/' + self.file_name, 'wb') as file:
            file.write(data)
        xl_workbook = xlrd.open_workbook(file.name)
        sheet_names = xl_workbook.sheet_names()
        xl_sheet = xl_workbook.sheet_by_name(sheet_names[0])
        num_cols = xl_sheet.ncols
        headers = []
        for col_idx in range(0, num_cols):
            cell_obj = xl_sheet.cell(0, col_idx)
            headers.append(cell_obj.value)
        import_data = []
        f_name = '/tmp/faulty_sheet.xlsx'
        workbook = xlsxwriter.Workbook(f_name)
        worksheet = workbook.add_worksheet('Report')
        worksheet.set_column('A:F', 15)
        style = workbook.add_format({
            'bold': 1,
            'border': 1,
            'align': 'center',
            'valign': 'vcenter'})
        style.set_font_size(8)
        align_value = workbook.add_format({
            'align': 'center',
            'valign': 'vcenter',
            'border': 1})
        align_value.set_font_size(8)
        worksheet.write('A1', "PRODUCT", style)
        worksheet.write('B1', "PRODUCT REF", style)
        worksheet.write('C1', "LOT/SERIAL", style)
        worksheet.write('D1', "QTY", style)
        worksheet.write('E1', "LINE", style)
        worksheet.write('F1', "REASON", style)
        new_row = 2
        for row_idx in range(1, xl_sheet.nrows):  # Iterate through rows
            row_dict = {}
            for col_idx in range(0, num_cols):  # Iterate through columns
                cell_obj = xl_sheet.cell(row_idx, col_idx)  # Get cell object by row, col
                row_dict[headers[col_idx]] = cell_obj.value
            import_data.append(row_dict)
        active_id = self.env.context.get('active_id', False)
        if active_id:
            for move_line in self.env['stock.inventory'].browse(active_id):
                move_line.line_ids.unlink()
        product_list = []
        lot_list = []
        count = 1.0
        for row in import_data:
            count += 1
            stock_inventory = self.env['stock.inventory'].search([('id', '=', int(row["INVENTORY ID"]))])
            if not stock_inventory:
                raise Warning(_('You are not using it for correct picking'))
            product_id = self.env['product.product'].search([('name', '=', row["PRODUCT"])])
            lot_id = self.env['stock.production.lot'].search([('name', '=', row['LOT/SERIAL']),('product_id', '=', product_id.id)])
            if lot_id:
                lot_number = lot_id.id
            else:
                lot_number = False
            if product_id.id in product_list and lot_id.id in lot_list:
                worksheet.write("A%s" % (new_row), row["PRODUCT"], align_value)
                worksheet.write("B%s" % (new_row), row["PRODUCT REF"], align_value)
                worksheet.write("C%s" % (new_row), row["LOT/SERIAL"], align_value)
                worksheet.write("D%s" % (new_row), row["QUANTITY"], align_value)
                worksheet.write("E%s" % (new_row), count, align_value)
                worksheet.write("F%s" % (new_row), 'Duplicate Product with duplicate lot', align_value)
                new_row += 1
                continue
            if not product_id:
                worksheet.write("A%s" % (new_row), row["PRODUCT"], align_value)
                worksheet.write("B%s" % (new_row), row["PRODUCT REF"], align_value)
                worksheet.write("C%s" % (new_row), row["LOT/SERIAL"], align_value)
                worksheet.write("D%s" % (new_row), row["QUANTITY"], align_value)
                worksheet.write("E%s" % (new_row), count, align_value)
                worksheet.write("F%s" % (new_row), 'Product Not Available', align_value)
                new_row += 1
                continue
            product_list.append(product_id.id)
            if lot_id:
                lot_list.append(lot_number)
            stock_inventory_line = self.env['stock.inventory.line']
            stock_inventory_line.create(
                {
                    'inventory_id': int(row["INVENTORY ID"]),
                    'product_id': product_id.id,
                    'location_id': row["LOCATION"],
                    'prod_lot_id': lot_number,
                    'product_qty': row["QUANTITY"],
                })
        workbook.close()
        f = open(f_name, 'rb')
        data = f.read()
        f.close()
        name = 'Inventory Faulty Report'
        self.env['stock.inventory'].browse(active_id).write({'faulty_file_name': name + '.xlsx', 'file_name_details': base64.b64encode(data)})
