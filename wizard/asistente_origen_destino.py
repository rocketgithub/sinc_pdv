# -*- coding: utf-8 -*-

from odoo import api, models, fields
import logging
import datetime

class SincOrigenDestino(models.TransientModel):
    _name = 'sinc_pdv.sinc_origen_destino_wizard'

    ubicaciones = fields.Boolean('Ubicaciones')
    pos_sat_resolucion = fields.Boolean('POS SAT Resolucion')
    diarios = fields.Boolean('Diarios')
    categorias_pdv = fields.Boolean('Categorias PDV')
    categorias_producto = fields.Boolean('Categorias producto')
    pdv = fields.Boolean('Puntos de Venta')
    usuarios = fields.Boolean('Usuarios')
    productos = fields.Boolean('Productos')
    productos_template = fields.Boolean('Productos template')
    pos_gt_extra = fields.Boolean('POS GT extra')
    lista_materiales = fields.Boolean('Lista de materiales')
    ajuste_inicial = fields.Boolean('Ajuste inicial')
    
    @api.multi
    def sinc_origen_destino(self):
        logging.warn('SINCRONIZACION ORIGEN DESTINO')
        settings_obj = self.env['res.config.settings']
        dict = {}
        dict['ubicaciones'] = self.ubicaciones
        dict['pos_sat_resolucion'] = self.pos_sat_resolucion
        dict['diarios'] = self.diarios
        dict['categorias_pdv'] = self.categorias_pdv
        dict['categorias_producto'] = self.categorias_producto
        dict['pdv'] = self.pdv
        dict['usuarios'] = self.usuarios
        dict['productos'] = self.productos
        dict['productos_template'] = self.productos_template
        dict['pos_gt_extra'] = self.pos_gt_extra
        dict['lista_materiales'] = self.lista_materiales
        dict['ajuste_inicial'] = self.ajuste_inicial
        settings_obj.sincronizacion_out(dict)
