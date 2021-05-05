# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError
import xmlrpc.client
import datetime
import urllib, base64
import logging
import random
from dateutil import parser

# Este modulo utiliza el modulo complementario sinc_pdv_extra.

# La clase Sinc_PDV_out define funciones para especificamente trasnferir del servidor origen al servidor destino.
class Sinc_PDV_out(models.Model):
    _name = 'sinc_pdv.out'
    _inherit = 'sinc_pdv.base'

    def transferir_datos(self, conexion, res_model):
        sinc_obj = self.env[self.modelo_relacionado(res_model)]
        x = 1
        for obj_origen in self.env[sinc_obj.res_model_origen()].search(sinc_obj.filtro_base_origen(), order='id asc'):
            logging.getLogger('No... ').warn(x)
            logging.getLogger('ID... ').warn(obj_origen.id)
            x += 1
            sinc_obj.transferir(conexion, obj_origen)

    @api.multi
    def ajuste_inicial(self, conexion):
        sinc_stock_inventory_obj = self.env['sinc_pdv.inventario']
        sinc_stock_inventory_obj.out_ajuste_inicial(conexion)

    # La funcion iniciar() es la funcion que se ejecuta cuando desde la interfaz de Odoo se presiona el boton para tranferir
    # informacion desde el servidor origen hacia el servidor destino.
    @api.multi
    def iniciar_transferencia(self, conexion, transferencias):

        common = xmlrpc.client.ServerProxy('{}/xmlrpc/2/common'.format(conexion['url']))
        conexion['uid'] = common.authenticate(conexion['database'], conexion['username'], conexion['password'], {})
        conexion['models'] = xmlrpc.client.ServerProxy('{}/xmlrpc/2/object'.format(conexion['url']))

        logging.warn('INICIO SINCRONIZACION PDV')
        if transferencias['ubicaciones']:
            self.transferir_datos(conexion, 'stock.location')
        if transferencias['pos_sat_resolucion']:
            self.transferir_datos(conexion, 'pos_sat.resolucion')
        if transferencias['clientes']:
            self.transferir_datos(conexion, 'res.partner')
        if transferencias['diarios']:
            self.transferir_datos(conexion, 'account.journal')
        if transferencias['categorias_pdv']:
            self.transferir_datos(conexion, 'pos.category')
        if transferencias['categorias_producto']:
            self.transferir_datos(conexion, 'product.category')
        if transferencias['lista_precios']:
            self.transferir_datos(conexion, 'product.pricelist')
        if transferencias['pdv']:
            self.transferir_datos(conexion, 'pos.config')
        if transferencias['usuarios']:
            self.transferir_datos(conexion, 'res.users')
        if transferencias['categorias_unidades_medida']:
            self.transferir_datos(conexion, 'uom.category')
        if transferencias['unidades_medida']:
            self.transferir_datos(conexion, 'uom.uom')
        if transferencias['productos']:
            self.transferir_datos(conexion, 'product.product')
        if transferencias['productos_template']:
            self.transferir_datos(conexion, 'product.template')
        if transferencias['pos_gt_extra']:
            self.transferir_datos(conexion, 'pos_gt.extra')
        if transferencias['lista_materiales']:
            self.transferir_datos(conexion, 'mrp.bom')
        if transferencias['ajuste_inicial']:
            self.ajuste_inicial(conexion)
        logging.warn('FIN SINCRONIZACION PDV!!!')
