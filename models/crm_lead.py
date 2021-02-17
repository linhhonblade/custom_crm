# -*- coding: utf-8 -*-

import logging
from odoo import models, fields, _, tools
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

CRM_LEAD_FIELDS_TO_MERGE = [
    'name',
    'partner_id',
    'campaign_id',
    'company_id',
    'country_id',
    'team_id',
    'state_id',
    'stage_id',
    'medium_id',
    'source_id',
    'user_id',
    'title',
    'city',
    'contact_name',
    'description',
    'mobile',
    'partner_name',
    'phone',
    'probability',
    'expected_revenu',
    'street',
    'street2',
    'zip',
    'create_date',
    'date_action_las',
    'email_from',
    'email_cc',
    'website',
    'linkedin',
    'facebook',
    'skype',
    'whatsapp']

# Subset of partner fields: sync any of those
PARTNER_FIELDS_TO_SYNC = [
    'mobile',
    'title',
    'function',
    'website',
    'linkedin',
    'facebook',
    'skype',
    'whatsapp'
]

# Subset of partner fields: sync all or none to avoid mixed addresses
PARTNER_ADDRESS_FIELDS_TO_SYNC = [
    'street',
    'street2',
    'city',
    'zip',
    'state_id',
    'country_id',
]

class Lead(models.Model):
    _order = "id desc, priority"
    _inherit = "crm.lead"

    linkedin = fields.Char('LinkedIn', help="LinkedIn of the contact",
                          compute="_compute_partner_id_values", store=True, readonly=False)
    facebook = fields.Char('Facebook', help="Facebook of the contact",
                            compute="_compute_partner_id_values", store=True, readonly=False)
    skype = fields.Char('Skype', help="Skype of the contact",
                            compute="_compute_partner_id_values", store=True, readonly=False)
    whatsapp = fields.Char('WhatsApp', help="WhatsApp of the contact",
                          compute="_compute_partner_id_values", store=True, readonly=False)

    am_id = fields.Many2one('res.users', string='AM', index=True, tracking=True)
    pmo_id = fields.Many2one('res.users', string='PMO', index=True, tracking=True)

    def _message_auto_subscribe_followers(self, updated_values, default_subtype_ids):
        """ Optional method to override in addons inheriting from mail.thread.
        Return a list tuples containing (
          partner ID,
          subtype IDs (or False if model-based default subtypes),
          QWeb template XML ID for notification (or False is no specific
            notification is required),
          ), aka partners and their subtype and possible notification to send
        using the auto subscription mechanism linked to updated values.

        Default value of this method is to return the new responsible of
        documents. This is done using relational fields linking to res.users
        with track_visibility set. Since OpenERP v7 it is considered as being
        responsible for the document and therefore standard behavior is to
        subscribe the user and send him a notification.

        Override this method to change that behavior and/or to add people to
        notify, using possible custom notification.

        :param updated_values: see ``_message_auto_subscribe``
        :param default_subtype_ids: coming from ``_get_auto_subscription_subtypes``
        """

        result = []
        field = self._fields.get('user_id')
        user_id = updated_values.get('user_id')
        if field and user_id and field.comodel_name == 'res.users' and (
                getattr(field, 'track_visibility', False) or getattr(field, 'tracking', False)):
            user = self.env['res.users'].sudo().browse(user_id)
            try:  # avoid to make an exists, lets be optimistic and try to read it.
                if user.active:
                    result.append((user.partner_id.id, default_subtype_ids,
                             'mail.message_user_assigned' if user != self.env.user else False))
            except:
                pass

        field = self._fields.get('am_id')
        user_id = updated_values.get('am_id')
        if field and user_id and field.comodel_name == 'res.users' and (
                getattr(field, 'track_visibility', False) or getattr(field, 'tracking', False)):
            user = self.env['res.users'].sudo().browse(user_id)
            try:  # avoid to make an exists, lets be optimistic and try to read it.
                if user.active:
                    result.append((user.partner_id.id, default_subtype_ids,
                             'custom_crm.message_am_assigned' if user != self.env.user else False))
            except:
                pass

        field = self._fields.get('pmo_id')
        user_id = updated_values.get('pmo_id')
        if field and user_id and field.comodel_name == 'res.users' and (
                getattr(field, 'track_visibility', False) or getattr(field, 'tracking', False)):
            user = self.env['res.users'].sudo().browse(user_id)
            try:  # avoid to make an exists, lets be optimistic and try to read it.
                if user.active:
                    result.append((user.partner_id.id, default_subtype_ids,
                                   'custom_crm.message_pmo_assigned' if user != self.env.user else
                                   False))
            except:
                pass

        return result

    # @api.onchange('am_id')
    # @api.model
    # def onchange_am_id(self):
    #     users = self.env.ref('custom_crm.group_sale_am').users.ids
    #     return {'domain': {'am_id': [('id', 'in', users)]}}

    # rewrite the whole function with new PARTNER_FIELDS_TO_SYNC list
    def _prepare_values_from_partner(self, partner):
        # Sync all address fields from partner, or none, to avoid mixing them.
        if any(partner[f] for f in PARTNER_ADDRESS_FIELDS_TO_SYNC):
            values = {f: partner[f] for f in PARTNER_ADDRESS_FIELDS_TO_SYNC}
        else:
            values = {f: self[f] for f in PARTNER_ADDRESS_FIELDS_TO_SYNC}

        # For other fields, get the info from the partner, but only if set
        values.update({f: partner[f] or self[f] for f in PARTNER_FIELDS_TO_SYNC})

        # Fields with specific logic
        partner_name = partner.parent_id.name
        if not partner_name and partner.is_company:
            partner_name = partner.name
        contact_name = False if partner.is_company else partner.name
        values.update({
            'partner_name': partner_name or self.partner_name,
            'contact_name': contact_name or self.contact_name,
        })
        return self._convert_to_write(values)

    # rewrite the whole function for the new CRM_LEAD_FIELDS_TO_SYNC list
    def merge_opportunity(self, user_id=False, team_id=False, auto_unlink=True):
        if len(self.ids) <= 1:
            raise UserError(
                _(
                    'Please select more than one element (lead or opportunity) from the list view.'))

        if len(self.ids) > 5 and not self.env.is_superuser():
            raise UserError(_('To prevent data loss, Leads and Opportunities can only be '
                              'merged by groups of 5.'))

        opportunities = self._sort_by_confidence_level(reverse=True)

        # get SORTED recordset of head and tail, and complete list
        opportunities_head = opportunities[0]
        opportunities_tail = opportunities[1:]

        # merge all the sorted opportunity. This means the value of
        # the first (head opp) will be a priority.
        merged_data = opportunities._merge_data(list(CRM_LEAD_FIELDS_TO_MERGE))

        # force value for salesperson and Sales Team
        if user_id:
            merged_data['user_id'] = user_id
        if team_id:
            merged_data['team_id'] = team_id

        # merge other data (mail.message, attachments, ...) from tail into head
        opportunities_head.merge_dependencies(opportunities_tail)

        # check if the stage is in the stages of the Sales Team. If not, assign the stage
        # with the lowest sequence
        if merged_data.get('team_id'):
            team_stage_ids = self.env['crm.stage'].search(['|',
                                                           ('team_id', '=',
                                                            merged_data['team_id']),
                                                           ('team_id', '=', False)],
                                                          order='sequence')
            if merged_data.get('stage_id') not in team_stage_ids.ids:
                merged_data['stage_id'] = team_stage_ids[0].id if team_stage_ids else False

        # write merged data into first opportunity
        opportunities_head.write(merged_data)

        # delete tail opportunities
        # we use the SUPERUSER to avoid access rights issues because as the user had the
        # rights to see the records it should be safe to do so
        if auto_unlink:
            opportunities_tail.sudo().unlink()
        return opportunities_head

    def _prepare_customer_values(self, partner_name, is_company=False, parent_id=False):
        """ Extract data from lead to create a partner.
        :param partner_name : furtur name of the partner
        :param is_company : True if the partner is a company
        :param parent_id : id of the parent partner (False if no parent)

        :return: dictionary of values to give at res_partner.create()
        """
        res = super(Lead, self)._prepare_customer_values(partner_name, is_company, parent_id)
        res['facebook'] = self.facebook
        res['linkedin'] = self.linkedin
        res['skype'] = self.skype
        res['whatsapp'] = self.whatsapp
        return res
