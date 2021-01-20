# -*- coding: utf-8 -*-

import logging
from odoo import models, fields

_logger = logging.getLogger(__name__)

class Lead(models.Model):
    _order = "id desc, priority"
    _inherit = "crm.lead"

    linkedin = fields.Char('LinkedIn', help="LinkedIn of the contact",
                          compute="_compute_partner_id_values", store=True, readonly=False)
    facebook = fields.Char('Facebook', help="Facebook of the contact",
                            compute="_compute_partner_id_values", store=True, readonly=False)
    skype = fields.Char('Skype', help="Skype of the contact",
                            compute="_compute_partner_id_values", store=True, readonly=False)
    am_id = fields.Many2one('res.users', string='AM', index=True, tracking=True, default=lambda self: self.env.user)
    pmo_id = fields.Many2one('res.users', string='PMO', index=True, tracking=True, default=lambda self: self.env.user)

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
