# -*- coding: utf-8 -*-

from odoo import fields, models

class Partner(models.Model):
    _name = 'res.partner'
    _inherit = 'res.partner'

    linkedin = fields.Char('LinkedIn', help="LinkedIn of this contact")
    facebook = fields.Char('Facebook', help="Facebook of this contact")
    skype = fields.Char('Skype ID', help="Skype of this contact")
    whatsapp = fields.Char('WhatsApp', help="WhatsApp of this contact")
