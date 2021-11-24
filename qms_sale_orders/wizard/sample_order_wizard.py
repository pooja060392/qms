from odoo import api, fields, models
import xlsxwriter
import base64
import datetime
from datetime import date

class SampleWizard(models.TransientModel):
    _name = 'sample.wizard'

    from_date = fields.Date('From Date',default=fields.Datetime.now)
    to_date = fields.Date('To Date',default=fields.Datetime.now)


    def print_sample_excel(self):
        f_name = '/tmp/report.xlsx'
        workbook = xlsxwriter.Workbook(f_name)
        worksheet = workbook.add_worksheet('Report')
        worksheet.set_column('A:N', 12)
        style = workbook.add_format({
            'bold': 1,
            'border': 1,
            'align': 'center',
            'valign': 'vcenter'})
        bold_size_format = workbook.add_format({
            'bold': 1,
            'border': 1,
            'align': 'center',
            'valign': 'vcenter'})
        bold_size_format.set_font_size(12)

        worksheet.write(1, 0, 'Sales Executive', style)
        worksheet.write(1, 1, 'CANCEL', style)
        worksheet.write(1, 2, 'COMPLETE', style)
        worksheet.write(1, 3, 'PENDING', style)
        worksheet.write(1, 5, 'TOTAL PENDING  SAMPLE COST', style)
        worksheet.write(1, 4, 'Grand Total', style)
        a = 2
        approved = 0
        need_approval = 0
        reject = 0
        pending_return_amt = 0.0
        grand_total = 0.0
        cancel_grand_tot = 0
        approved_grand_tot = 0
        need_approval_grand = 0
        users = self.env['res.users'].search([('is_salesperson', '=', True)])
        for user in users:
            order_line = self.env['sale.order.line'].search([('type', '=', 'sample'),
                                                             ('date_order', '>=', self.from_date),
                                                             ('date_order', '<=', self.to_date),
                                                             ('salesman_id', '=', user.id),
                                                             ('order_id.sale_type', '=', 'sample_gift')])
            if order_line:
                for rec in order_line:
                    if rec.line_status == 'approved':
                        approved = approved+1
                    if rec.line_status == 'need_approval':
                        need_approval = need_approval+1
                    if rec.line_status == 'rejected':
                        reject = reject + 1
                    if rec.return_status == 'waiting_return':
                        pending_return_amt = pending_return_amt + rec.price_subtotal
                grand_total = grand_total + approved + reject + need_approval
                cancel_grand_tot = cancel_grand_tot + reject
                approved_grand_tot = approved_grand_tot + approved
                need_approval_grand = need_approval_grand + need_approval
                worksheet.write(a, 0, rec.salesman_id.name)
                worksheet.write(a, 1, reject)
                worksheet.write(a, 2, approved)
                worksheet.write(a, 3, need_approval)
                worksheet.write(a, 5, pending_return_amt)
                worksheet.write(a, 4, grand_total)
                approved = 0
                need_approval = 0
                reject = 0
                pending_return_amt = 0
                grand_total = 0.0
            a =a+ 1
        worksheet.write(a, 0, 'Grand Total', style)
        worksheet.write(a, 1, cancel_grand_tot)
        worksheet.write(a, 2, approved_grand_tot)
        worksheet.write(a, 3, need_approval_grand)

        style.set_font_size(12)
        workbook.close()
        f = open(f_name, 'rb')
        data = f.read()
        f.close()
        name = 'Report'



        out_wizard = self.env['xlsx.output'].create({'name': name + '.xlsx',
                                                     'xls_output': base64.encodebytes(data)})
        view_id = self.env.ref('qms_sale_order.xlsx_output_form').id
        return {
            'type': 'ir.actions.act_window',
            # 'name': _(name),
            'res_model': 'xlsx.output',
            'target': 'new',
            'view_mode': 'form',
            'res_id': out_wizard.id,
            'views': [[view_id, 'form']],
        }

