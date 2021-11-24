
from odoo import models, fields, api, _
from odoo.exceptions import UserError
from odoo.osv import expression


class ResPartner(models.Model):
    _inherit = 'res.partner'

    partner_state_enable = fields.Boolean(
        compute='_compute_partner_state_enable',
    )


    def _compute_partner_state_enable(self):
        if self.env.user.company_id.partner_state_enable:
            partners = self.filtered(lambda r:
                                     r.commercial_partner_id == r)
            partners.update({'partner_state_enable': True})

    partner_state = fields.Selection('_get_partner_states', string='Status',
                                     readonly=True, required=True, default='potential',
                                     track_visibility='onchange')

    @api.model
    def _get_partner_states(self):
        return [
            ('potential', _('Potential')),
            ('pending', _('Pending Approval')),
            ('approved', _('Approved')),
            ('rejected', _('Rejected'))
        ]


    def write(self, vals):
        for partner in self.filtered(lambda r:
                                     r.partner_state in
                                     ['approved', 'pending']):
            fields = partner.check_fields('track')
            if fields:
                fields_set = set(fields)
                vals_set = set(vals)
                if fields_set & vals_set:
                    partner.partner_state_potential()

        return super(ResPartner, self).write(vals)


    def partner_state_potential(self):
        template_id = self.env.ref('qms_partner_state.email_template_partner_to_potential_vendor')
        if template_id:
            values = template_id.generate_email(self.id)
            values['email_to'] = self.create_uid.email
            values['email_from'] = self.env.user.email
            values['body_html'] = """
                <p>Dear {name},</p>
                <p>Vendor with the name <b>{subject}</b> Has been Potential.
                </p>
                <p>Thank you,</p>
                """.format(name=self.create_uid.name,subject=self.name)
            values['body_html'] = values['body_html']
            mail = self.env['mail.mail'].create(values)
            try:
                mail.send()
            except Exception:
                pass
            # template_id.send_mail(self.id, force_send=True, raise_exception=True)
        self.update({'partner_state': 'potential'})


    def partner_state_pending(self):
        self.ensure_one()
        # Send mail to all users with approval access for approval
        approval_group = self.env.ref('qms_partner_state.approve_partners')
        recipient_users = approval_group.users.filtered(lambda x: x.email)
        for users in recipient_users:
            template = self.env.ref('qms_partner_state.email_template_partner_approval', False)
            action_id = self.env.ref('base.action_partner_supplier_form').id
            params = "/web#id=%s&view_type=form&model=res.partner&action=%s" % (
                self.id, action_id
            )
            current_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
            partner_url = str(current_url) + str(params)
            if template:

                values = template.generate_email(self.id)
                values['email_to'] = users.email
                values['email_from'] = self.env.user.email
                values['body_html'] = """
                <p>Dear {name},</p>
                <p>You are Requested to approve a new Vendor created in the <b>{company}</b> with the name of 
                <b>{subject}</b>.</p>
                 <p>Here is the Link.</p>
                 <p>
                <a href="_partner_url" style="background-color: #9E588B; margin-top: 10px; padding: 10px;
                text-decoration: none; color: #fff; border-radius: 5px; font-size: 16px;">View/Approve</a>
                </p>
                 <p>Thank you,</p>
                                        """.format(name=users.name,subject=self.name, company=self.company_id.name)
                values['body_html'] = values['body_html'].replace('_partner_url', partner_url)
                mail = self.env['mail.mail'].create(values)
                try:
                    mail.send()
                except Exception:
                    pass

                # template.send_mail(self.id, force_send=True, raise_exception=True)
        #
        # vals = template.generate_email(self.id)
        # vals['recipient_ids'] = [(4, user.partner_id.id) for user in recipient_users]
        # self.env['mail.mail'].create(vals)
        fields = self.check_fields('approval')
        if not fields:
            self.partner_state = 'pending'
            return

        partner_data = self.read(fields)[0]
        if all(partner_data.values()):
            self.partner_state = 'pending'
            return
        for partner_field, value in partner_data.items():
            if not value:
                raise UserError(_(
                    "Can not request approval, "
                    "required field %s" % (
                        partner_field)))
        self.partner_state = 'pending'


    def partner_state_approved(self):
        template_id = self.env.ref('qms_partner_state.email_template_partner_approve_vendor')
        if template_id:
            values = template_id.generate_email(self.id)
            values['email_to'] = self.create_uid.email
            values['email_from'] = self.env.user.email
            values['body_html'] = """
                <p>Dear {name},</p>
                <p>Vendor with the name <b>{subject}</b> Has been Approved.
                </p>
                <p>Thank you,</p>
                """.format(name=self.create_uid.name,subject=self.name)
            values['body_html'] = values['body_html']
            mail = self.env['mail.mail'].create(values)
            try:
                mail.send()
            except Exception:
                pass
            # template_id.send_mail(self.id, force_send=True, raise_exception=True)
        self.check_partner_approve()
        self.partner_state = 'approved'


    def partner_state_rejected(self):
        template_id = self.env.ref('qms_partner_state.email_template_partner_rejection_vendor')
        if template_id:
            values = template_id.generate_email(self.id)
            values['email_to'] = self.create_uid.email
            values['email_from'] = self.env.user.email
            values['body_html'] = """
                <p>Dear {name},</p>
                <p>Vendor with the name <b>{subject}</b> Has been Rejected.
                </p>
                <p>Thank you,</p>
                """.format(name=self.create_uid.name,subject=self.name)
            values['body_html'] = values['body_html']
            mail = self.env['mail.mail'].create(values)
            try:
                mail.send()
            except Exception:
                pass
            # template_id.send_mail(self.id, force_send=True, raise_exception=True)
        self.partner_state = 'rejected'


    def check_partner_approve(self):
        user_can_approve_partners = self.env[
            'res.users'].has_group('qms_partner_state.approve_partners')
        if not user_can_approve_partners:
            raise UserError(
                _("User can't approve partners, "
                    "please check user permissions!"))
        return True


    def check_fields(self, field_type):
        ret = False
        for rec in self.filtered(lambda x: x.partner_state_enable):
            partner_field_ids = rec.env['res.partner.state_field'].search([])
            if field_type == 'approval':
                ret = [
                    field.field_id.name for field in partner_field_ids if
                    field.approval]
            elif field_type == 'track':
                ret = [
                    field.field_id.name for field in partner_field_ids if
                    field.track]
        return ret

    @api.model
    def _get_tracked_fields(self, updated_fields):
        tracked_fields = []
        # TODO we should use company of modified partner
        for line in self.env['res.partner.state_field'].search([]):
            if line.track and line.field_id.name in updated_fields:
                tracked_fields.append(line.field_id.name)

        if tracked_fields:
            return self.fields_get(tracked_fields)
        return super(ResPartner, self)._get_tracked_fields(updated_fields)


    def message_track(self, tracked_fields, initial_values):
        """
        We need to set attribute temporary because message_track read it
        from field properties to make message
        """
        # TODO we should use company of modified partner
        for line in self.env['res.partner.state_field'].search([(
                'track', '=', True)]):
            field = self._fields[line.field_id.name]
            setattr(field, 'track_visibility', 'always')
        return super(ResPartner, self).message_track(
            tracked_fields, initial_values)

    # @api.model
    # def name_search(self, name, args=None, operator='ilike', limit=100):
    #     args = args or []
    #     domain = []
    #     if name:
    #         domain = [('partner_state', '=', 'approved')]
    #     partners = self.search(domain + args, limit=limit)
    #     return partners.name_get()
