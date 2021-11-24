# -*- coding: utf-8 -*-
##############################################################################
#
#    India-GST
#
#    Merlin Tecsol Pvt. Ltd.
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from odoo import api, models, fields, _

import xlsxwriter
import base64
import datetime
from datetime import date


class WizardGstrB2CL(models.TransientModel):
    _name = 'gstr.b2cl'

    start_date = fields.Date('From Date', default=fields.Datetime.now(), required=True)
    end_date = fields.Date('To Date', default=fields.Datetime.now(), required=True)


    def print_b2cl_report(self,vals):
        invoice_obj = self.env['check.date'].search([])
        if invoice_obj:
            invoice_obj[-1].write(
                            {'start_date':self.start_date,
                            'end_date':self.end_date,
                            })
        if not invoice_obj:
            invoice_obj.create(
                            {'start_date':self.start_date,
                            'end_date':self.end_date,
                            })
        invoice_obj = self.env['check.date'].search([])[-1]
        invoice_id = self.env['account.move'].search([('type', '=', 'out_invoice'),
                                                         ('state', 'in', ['open', 'paid']),
                                                         ('date_invoice', '>=', invoice_obj.start_date),
                                                         ('date_invoice', '<=', invoice_obj.end_date)])

        f_name = '/tmp/b2cl.xlsx'
        workbook = xlsxwriter.Workbook(f_name)
        worksheet = workbook.add_worksheet('GSTR B2CL')
        worksheet.set_column('A:H', 15)
        date_format = workbook.add_format({'num_format': 'd-mmm-yyyy'})

        row = 1
        col = 0
        new_row = row + 1

        worksheet.write('A%s' % (row), 'Invoice Number')
        worksheet.write('B%s' % (row), 'Invoice date')
        worksheet.write('C%s' % (row), 'Invoice Value')
        worksheet.write('D%s' % (row), 'Place Of Supply')
        worksheet.write('E%s' % (row), 'Rate')
        worksheet.write('F%s' % (row), 'Taxable Value')
        worksheet.write('G%s' % (row), 'Cess Amount')
        worksheet.write('H%s' % (row), 'E-Commerce GSTIN')

        partner_state = self.env.user.company_id.partner_id.state_id.name

        ls = []
        for obj in invoice_id:
            if obj.flag_field == False and obj.amount_total > 250000 and obj.partner_id.property_account_position_id.name == 'Inter State' and obj.export_invoice == False:
                for rec in obj.invoice_line_ids:
                    if rec.invoice_line_tax_ids:
                        if rec.tax_desc == 'gst' and rec.gst_amount == 5:
                            ls.append([rec.tax_desc, rec.gst_amount])
                        if rec.tax_desc == 'gst' and rec.gst_amount == 12:
                            ls.append([rec.tax_desc, rec.gst_amount])
                        if rec.tax_desc == 'gst' and rec.gst_amount == 18:
                            ls.append([rec.tax_desc, rec.gst_amount])
                        if rec.tax_desc == 'gst' and rec.gst_amount == 28:
                            ls.append([rec.tax_desc, rec.gst_amount])
                        if rec.tax_desc == 'igst' and rec.gst_amount == 5:
                            ls.append([rec.tax_desc, rec.gst_amount])
                        if rec.tax_desc == 'igst' and rec.gst_amount == 12:
                            ls.append([rec.tax_desc, rec.gst_amount])
                        if rec.tax_desc == 'igst' and rec.gst_amount == 18:
                            ls.append([rec.tax_desc, rec.gst_amount])
                        if rec.tax_desc == 'igst' and rec.gst_amount == 28:
                            ls.append([rec.tax_desc, rec.gst_amount])
                        if rec.tax_desc == 'none' and rec.gst_amount == 0:
                            ls.append([rec.tax_desc, rec.gst_amount])

        for obj in invoice_id:
            if obj.flag_field == False and obj.amount_total > 250000 and obj.partner_id.property_account_position_id.name == 'Inter State' and obj.export_invoice == False:
                for row in set(map(tuple, ls)):
                    r = 0
                    for rec in obj.invoice_line_ids:
                        if rec.invoice_line_tax_ids:
                            if rec.tax_desc == row[0] and rec.gst_amount == row[1]:
                                r += rec.price_subtotal
                        if r == 0:
                            pass
                        else:
                            inv_date = datetime.datetime.strptime(obj.date_invoice, '%Y-%m-%d')

                            worksheet.write('A%s' % (new_row), obj.number)
                            worksheet.write('B%s' % (new_row), inv_date, date_format)
                            worksheet.write('C%s' % (new_row), obj.amount_total)
                            worksheet.write_rich_string('D%s' % (new_row), str(obj.partner_id.state_id.state_code) + \
                                                        "-" + str(obj.partner_id.state_id.name))
                            worksheet.write('E%s' % (new_row), row[1])
                            worksheet.write('F%s' % (new_row), r)
                            worksheet.write('G%s' % (new_row), '')
                            worksheet.write('H%s' % (new_row), obj.partner_id.e_commerce_tin)

                            new_row += 1
        workbook.close()
        f = open(f_name, 'rb')
        data = f.read()
        f.close()
        name = 'GSTR B2CL Report'
        dt = 'From_' + str(self.start_date) + '' + '_To_' + str(self.end_date)
        out_wizard = self.env['xlsx.output'].create({'name': name + '_' + dt + '.xlsx',
                                                     'xls_output': base64.encodebytes(data)})
        view_id = self.env.ref('geo_gst.xlsx_output_form').id
        return {
            'type': 'ir.actions.act_window',
            'name': _(name),
            'res_model': 'xlsx.output',
            'target': 'new',
            'view_mode': 'form',
            'res_id': out_wizard.id,
            'views': [[view_id, 'form']],
        }
