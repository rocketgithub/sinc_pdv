# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import api, fields, models
import logging

class BaseConfigSettings(models.TransientModel):

    _inherit = 'res.config.settings'

    url = fields.Char('URL', default='http://66.228.61.148')
    database = fields.Char('Base de datos destino', default='pruebas_destino')
    username = fields.Char('Usuario', default='admin')
    password = fields.Char('Contraseña', default='guateburgersa')
   
    def datos_conexion(self):
        for config in self:
            dict = {}
            dict['url'] = config.url
            dict['database'] = config.database
            dict['username'] = config.username
            dict['password'] = config.password
        return dict

    def sincronizacion_inicial(self):
        for config in self:
            sinc_obj = self.env['sinc_pdv.out']
            sinc_obj.iniciar(self.datos_conexion())
            logging.warn(config.url)

    def sincronizacion_diaria(self):
        for config in self:
            sinc_obj = self.env['sinc_pdv.in']
            sinc_obj.iniciar(self.datos_conexion())
            logging.warn(config.url)
