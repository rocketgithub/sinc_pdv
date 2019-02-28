# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import api, fields, models
import logging

class BaseConfigSettings(models.TransientModel):

    _inherit = 'res.config.settings'

    url = fields.Char('URL', default='http://50.116.34.232')
    database = fields.Char('Base de datos destino', default='grupor2c')
    username = fields.Char('Usuario', default='admin')
    password = fields.Char('Contraseña', default='guateburgersa')

    @api.model
    def get_default_url(self, fields):
        url = self.env["ir.config_parameter"].get_param("sinc.url", default=None)
        return {'url': url or False}

    @api.multi
    def set_url(self):
        for record in self:
            self.env['ir.config_parameter'].set_param("sinc.url", record.url or '')

    @api.model
    def get_default_database(self, fields):
        database = self.env["ir.config_parameter"].get_param("sinc.database", default=None)
        return {'database': database or False}

    @api.multi
    def set_database(self):
        for record in self:
            self.env['ir.config_parameter'].set_param("sinc.database", record.database or '')

    @api.model
    def get_default_username(self, fields):
        username = self.env["ir.config_parameter"].get_param("sinc.username", default=None)
        return {'username': username or False}

    @api.multi
    def set_username(self):
        for record in self:
            self.env['ir.config_parameter'].set_param("sinc.username", record.username or '')

    @api.model
    def get_default_password(self, fields):
        password = self.env["ir.config_parameter"].get_param("sinc.password", default=None)
        return {'password': password or False}

    @api.multi
    def set_password(self):
        for record in self:
            self.env['ir.config_parameter'].set_param("sinc.password", record.password or '')

    @api.model
    def datos_conexion(self):
        dict = {}
        dict['url'] = self.env["ir.config_parameter"].get_param("sinc.url")
        dict['database'] = self.env["ir.config_parameter"].get_param("sinc.database")
        dict['username'] = self.env["ir.config_parameter"].get_param("sinc.username")
        dict['password'] = self.env["ir.config_parameter"].get_param("sinc.password")
        return dict

    def sincronizacion_out(self, transferencias = {}):
        sinc_obj = self.env['sinc_pdv.out']
        sinc_obj.iniciar_transferencia(self.datos_conexion(), transferencias)

    def sincronizacion_in(self):
        sinc_obj = self.env['sinc_pdv.in']
        sinc_obj.iniciar_transferencia(self.datos_conexion())

    def sincronizacion_in0(self):
        sinc_obj = self.env['sinc_pdv.in']
        sinc_obj.iniciar_transferencia(self.datos_conexion(), restante = 0)

    def sincronizacion_in1(self):
        sinc_obj = self.env['sinc_pdv.in']
        sinc_obj.iniciar_transferencia(self.datos_conexion(), restante = 1)

    def sincronizacion_in2(self):
        sinc_obj = self.env['sinc_pdv.in']
        sinc_obj.iniciar_transferencia(self.datos_conexion(), restante = 2)
