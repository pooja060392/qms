# -*- coding: utf-8 -*-

from odoo import api, models, _
from datetime import datetime, timedelta, date
from datetime import timedelta
import time
import os
import base64
import urllib
import logging
from odoo.exceptions import UserError, AccessError
logger = logging.getLogger('Attachment Slides')


class MailComposer(models.TransientModel):
    _inherit = 'mail.compose.message'


    def send_mail_action(self):
        res = super(MailComposer, self).send_mail_action()
        active_id = self.env.context.get('active_id')
        active_model = self.env.context.get('active_model')
        if active_model == 'sale.order':
            sale = self.env['sale.order'].browse(active_id)
            # if sale.state == 'waiting_for_approval' or sale.sample_state == 'waiting_for_approval':
            #     raise UserError(_('You can not send quotation using this option as the quotation is not approved!'))
            # for package in sale.packing_line:
            #     if sale.customisation and not package.price > 0.0:
            #         raise UserError(_('Please fill package line product price!!!'))
            current_date = datetime.strptime(str(datetime.now().date()), "%Y-%m-%d")
            validity_date = current_date + timedelta(days=30)
            sale.write({'validity_date': validity_date, 'state': 'sent'})
            
        return res


    def create_attachment(self, slides):
        ''' Function to create attachment for product slides '''
        pptx_path = self.env['ir.config_parameter'].sudo().get_param('pptx_path')
        # if not pptx_path:
        #     warning = {
        #         'title': _('Configuration Warning!'),
        #         'message':
        #             _('PPTX Path(pptx_path) is not configured in configuration parameters!'),
        #     }
        #     return {'warning': warning, 'value': {}}
        # if not os.path.isfile(pptx_path):
        #     warning = {
        #         'title': _('Configuration Warning!'),
        #         'message':
        #             _('PPTX Path(pptx_path) is not correct!'),
        #     }
        #     return {'warning': warning, 'value': {}}
        pdf_file = pptx_path.rsplit('.', 1)[0] + '.pdf'
        time.sleep(5)
        command = "unoconv -e PageRange=%s --export Quality=100 %s " % (slides, pptx_path)
        os.popen("sudo -S %s" % (command), 'w').write('odoo\n')
        logger.info('Slides 2................. %s', slides)
        time.sleep(8)
        import subprocess
        sudoPassword = 'odoo'
        subprocess.Popen('sudo -S', shell=True, stdout=subprocess.PIPE)
        subprocess.Popen(sudoPassword, shell=True, stdout=subprocess.PIPE)
        subprocess.Popen(command, shell=True, stdout=subprocess.PIPE)

        # os.popen("unoconv -e PageRange=%s --export Quality=100 %s " %
        #          (slides, pptx_path))
        # time.sleep(5)
        (filename, header) = urllib.request.urlretrieve('file://' + str(pdf_file))
        f = open(filename, 'rb')
        pdf_file = f.read()
        f.close()
        attachment = self.env['ir.attachment'].create({
            'name': 'Slides.pdf',
            'type': 'binary',
            'datas': base64.encodestring(pdf_file),
            'datas_fname': 'Slides.pdf',
            'mimetype': 'application/x-pdf'
        })
        return attachment


    def onchange_template_id(self, template_id, composition_mode, model, res_id):
        ''' Overidden to create attachment for product slides '''
        result = super(MailComposer, self).onchange_template_id(
            template_id=template_id, composition_mode=composition_mode, model=model, res_id=res_id)
        context = self.env.context or {}
        if context.get('active_model') == 'sale.order' and context.get('active_id'):
            so = self.env['sale.order'].browse(int(context.get('active_id')))
            slides, count = '', 1
            for line in so.order_line:
                if line.attach_slide and line.product_id.slide_number > 0:
                    slides = slides + str(line.product_id.slide_number) + ','
                    # if count == 1:
                    #     slides = str(line.product_id.slide_number) + '-' + \
                    #              str(line.product_id.slide_number)
                    # else:
                    #     slides = slides + ',' + str(line.product_id.slide_number) + \
                    #              str(line.product_id.slide_number)
                # count += 1
            if slides:
                logger.info('Slides 1................. %s', slides)
                attachment = self.create_attachment(slides)
                if result.get('value', {}).get('attachment_ids', []):
                    attachments = result.get('value', {}).get('attachment_ids', [])
                    if len(attachments) > 0:
                        attachment_list = attachments[0][2]
                        attachment_list.append(attachment.id)
                        result['value']['attachment_ids'] = [(6, 0, attachment_list)]
                    else:
                        result['value']['attachment_ids'] = [(6, 0, [attachment.id])]
                else:
                    result['value']['attachment_ids'] = [(6, 0, [attachment.id])]
        return result
