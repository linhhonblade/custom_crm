# -*- coding: utf-8 -*-

from odoo import fields, models, api

class Users(models.Model):
    _inherit = 'res.users'

    is_am = fields.Boolean(compute="_compute_is_am", compute_sudo=True, string='AM', store=True)

    @api.depends('groups_id')
    def _compute_is_am(self):
        am_group_id = self.env['ir.model.data'].xmlid_to_res_id('custom_crm.group_sale_am')
        am_users = self.filtered_domain([('groups_id', 'in', [am_group_id])])
        am_users.is_am = True
        (self - am_users).is_am = False
