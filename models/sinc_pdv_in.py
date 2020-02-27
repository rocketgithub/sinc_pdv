# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError
import xmlrpc.client
import time
import urllib, base64
import logging
import random
from dateutil import parser


class Sinc_PDV_in(models.Model):
    _name = 'sinc_pdv.in'
    _inherit = 'sinc_pdv.base'

    @api.multi
    def iniciar_transferencia(self, conexion, model = '', obj = '', restante = 0):
        common = xmlrpc.client.ServerProxy('{}/xmlrpc/2/common'.format(conexion['url']))
        conexion['uid'] = common.authenticate(conexion['database'], conexion['username'], conexion['password'], {})
        conexion['models'] = xmlrpc.client.ServerProxy('{}/xmlrpc/2/object'.format(conexion['url']))

        logging.warn('INICIO SINCRONIZACION PDV IN '+str(restante))
        config_ids = self.buscar_destino(conexion, 'pos.config', [], {'order': 'sinc_date asc'})
        config_ids = [x for x in config_ids if x % 3 == restante]
        pos = 0
        procesado = False
        while not procesado and pos < len(config_ids):
            logging.getLogger('config_ids').warn(config_ids)

            logging.warn('INICIO in_crear_pedido '+str(restante))
            sinc_pdv_obj = self.env[self.modelo_relacionado('pos.config')]
            res1 = sinc_pdv_obj.in_crear_pedido(conexion, config_ids[pos])
            logging.warn('FIN in_crear_pedido '+str(restante))

            logging.warn('INICIO in_ajuste_inventario '+str(restante))
            sinc_stock_inventory_obj = self.env[self.modelo_relacionado('stock.inventory')]
            res2 = sinc_stock_inventory_obj.in_ajuste_inventario(conexion, config_ids[pos])
            logging.warn('FIN in_ajuste_inventario '+str(restante))

            if res1 == True or res2 == True:
                self.modificar_destino(conexion, 'pos.config', config_ids[pos], {'sinc_date': time.strftime('%Y-%m-%d %H:%M:%S')})
                procesado = True

            pos += 1

        logging.getLogger('res1... '+str(restante)).warn(res1)
        logging.getLogger('res2... '+str(restante)).warn(res2)
        logging.warn('FIN SINCRONIZACION PDV IN!!! '+str(restante))
