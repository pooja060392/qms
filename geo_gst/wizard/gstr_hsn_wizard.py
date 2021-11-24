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


class WizardHSNExport(models.TransientModel):
    _name = 'gstr.hsn'

    start_date = fields.Date('From Date', default=fields.Datetime.now(), required=True)
    end_date = fields.Date('To Date', default=fields.Datetime.now(), required=True)


    def print_hsn_report(self,vals):
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
                                                         ('invoice_date', '>=', invoice_obj.start_date),
                                                         ('invoice_date', '<=', invoice_obj.end_date)])

        f_name = '/tmp/hsn.xlsx'
        workbook = xlsxwriter.Workbook(f_name)
        worksheet = workbook.add_worksheet('GSTR HSN Summary')
        worksheet.set_column('A:J', 17)

        row = 1
        col = 0
        new_row = row + 1

        worksheet.write('A%s' % (row), 'HSN')
        worksheet.write('B%s' % (row), 'Description')
        worksheet.write('C%s' % (row), 'UQC')
        worksheet.write('D%s' % (row), 'Total Quantity')
        worksheet.write('E%s' % (row), 'Total Value')
        worksheet.write('F%s' % (row), 'Taxable Value')
        worksheet.write('G%s' % (row), 'Integrated Tax Amount')
        worksheet.write('H%s' % (row), 'Central Tax Amount')
        worksheet.write('I%s' % (row), 'State/UT Tax Amount')
        worksheet.write('J%s' % (row), 'Ces Amount')

        partner_state = self.env.user.company_id.partner_id.state_id.name

        ls = []
        t = []
        for obj in invoice_id:
            for rec in obj.invoice_line_ids:
                if rec.product_id.hsn_code:
                    ls.append(rec.product_id.hsn_code)

        hsn_no = set(ls)
        for hsn in hsn_no:
            qty = 0
            # total = 0
            taxable = 0
            cgst = 0
            sgst = 0
            igst = 0
            uom = ''

            for inv in invoice_id:
                c = 0
                s = 0
                i = 0

                for line in inv.invoice_line_ids:
                    if line.product_id.hsn_code == hsn:
                        qty += line.quantity
                        # total+=(line.quantity*line.price_unit)
                        taxable += line.price_subtotal
                        uom = line.uom_id.name
                        cgst += line.cgst
                        sgst += line.sgst
                        igst += line.igst

            t_value = taxable + cgst + sgst + igst
            worksheet.write('A%s' % (new_row), hsn.name)
            worksheet.write('B%s' % (new_row), '')
            worksheet.write('C%s' % (new_row), uom)
            worksheet.write('D%s' % (new_row), qty)
            worksheet.write('E%s' % (new_row), t_value)
            worksheet.write('F%s' % (new_row), taxable)
            worksheet.write('G%s' % (new_row), igst)
            worksheet.write('H%s' % (new_row), cgst)
            worksheet.write('I%s' % (new_row), sgst)

            new_row += 1
        workbook.close()
        f = open(f_name, 'rb')
        data = f.read()
        f.close()
        name = 'GSTR HSN Summary'
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

