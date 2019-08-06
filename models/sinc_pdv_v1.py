# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError
import xmlrpc.client
import datetime
import urllib, base64
import logging
import random
from dateutil import parser

class Sinc_PDV_V1(models.Model):
    _name = 'sinc_pdv.v1'
    _inherit = 'sinc_pdv.base'

    def _preparar_diccionario(self, obj, campos):
        dict = {}
        dict['sinc_id'] = obj['id']
        for campo in campos:
            dict[campo] = obj[campo]
        return dict


    @api.multi
    def _preparar_m2m(self, conexion, res_model, m2m_obj, campo, filtro_existe, ids_borrar = []):
        ids = []
        if ids_borrar != []:
            for id in ids_borrar:
                ids.append((3, id, False))

        for line in m2m_obj:
            id = self.buscar_destino(conexion, res_model, [[filtro_existe, '=', line[filtro_existe]]])
            if id:
                ids.append((4, id[0]))
        return ids


    @api.multi
    def _transferir_productos(self, conexion):
        res_model = 'product.product'
        campos = ['name', 'sale_ok', 'purchase_ok', 'type', 'default_code', 'barcode', 'lst_price', 'standard_price', 'sale_delay', 'produce_delay', 'available_in_pos', 'to_weight', 'description_sale', 'description_purchase', 'description_picking', 'active']
        filtro_search = [('company_id', '=', 1), ('default_code', '!=', False), '|', ('active','=',True), ('active','=',False)]
        filtro_existe = 'default_code'
        logging.warn(filtro_search)
        for obj in self.env[res_model].search(filtro_search, order='id asc'):
            obj_dict_template = {}
            obj_dict = self._preparar_diccionario(obj, campos)
            categ_id = self.buscar_destino(conexion, 'product.category', [['sinc_id', '=', obj.categ_id.sinc_id]])
            if categ_id:
                obj_dict_template['categ_id'] = categ_id[0]

            if obj.pos_categ_id:
                pos_categ_id = self.buscar_destino(conexion, 'pos.category', [['sequence', '=', obj.pos_categ_id.sequence]])
                if pos_categ_id:
                    obj_dict['pos_categ_id'] = pos_categ_id[0]

            obj_id = self.buscar_destino(conexion, res_model, [[filtro_existe, '=', obj[filtro_existe]], '|', ['active','=',True], ['active','=',False]])
            logging.warn(obj_id)
            if not obj_id:

                m2m_res_model = 'account.tax'
                m2m_obj = obj.taxes_id
                m2m_campo = 'taxes_id'
                m2m_filtro_existe = 'name'
                obj_dict['taxes_id'] = self._preparar_m2m(conexion, m2m_res_model, m2m_obj, m2m_campo, m2m_filtro_existe)

                m2m_res_model = 'account.tax'
                m2m_obj = obj.supplier_taxes_id
                m2m_campo = 'supplier_taxes_id'
                m2m_filtro_existe = 'name'
                obj_dict['supplier_taxes_id'] = self._preparar_m2m(conexion, m2m_res_model, m2m_obj, m2m_campo, m2m_filtro_existe)

                obj_id = conexion['models'].execute_kw(conexion['database'], conexion['uid'], conexion['password'], res_model, 'create', [obj_dict])

                m2m_res_model = 'pos_gt.extra'
                m2m_obj = obj.extras_id
                m2m_campo = 'extras_id'
                m2m_filtro_existe = 'name'
                obj_dict_template['supplier_taxes_id'] = self._preparar_m2m(conexion, m2m_res_model, m2m_obj, m2m_campo, m2m_filtro_existe)

                registro = self.leer_destino(conexion, res_model, [obj_id])[0]
                product_tmpl_id = registro['product_tmpl_id'][0]
                obj_dict_template['image'] = obj.image_small
                conexion['models'].execute_kw(conexion['database'], conexion['uid'], conexion['password'], 'product.template', 'write', [[product_tmpl_id], obj_dict_template])

            else:

                registro = self.leer_destino(conexion, res_model, [obj_id[0]])[0]

                m2m_res_model = 'account.tax'
                m2m_obj = obj.taxes_id
                m2m_campo = 'taxes_id'
                m2m_filtro_existe = 'name'
                m2m_ids_borrar = registro['taxes_id']
                obj_dict['taxes_id'] = self._preparar_m2m(conexion, m2m_res_model, m2m_obj, m2m_campo, m2m_filtro_existe, m2m_ids_borrar)

                m2m_res_model = 'account.tax'
                m2m_obj = obj.supplier_taxes_id
                m2m_campo = 'supplier_taxes_id'
                m2m_filtro_existe = 'name'
                m2m_ids_borrar = registro['supplier_taxes_id']
                obj_dict['supplier_taxes_id'] = self._preparar_m2m(conexion, m2m_res_model, m2m_obj, m2m_campo, m2m_filtro_existe, m2m_ids_borrar)

                conexion['models'].execute_kw(conexion['database'], conexion['uid'], conexion['password'], res_model, 'write', [[obj_id[0]], obj_dict])

                m2m_res_model = 'pos_gt.extra'
                m2m_obj = obj.extras_id
                m2m_campo = 'extras_id'
                m2m_filtro_existe = 'name'
                m2m_ids_borrar = registro['extras_id']
                obj_dict_template['extras_id'] = self._preparar_m2m(conexion, m2m_res_model, m2m_obj, m2m_campo, m2m_filtro_existe, m2m_ids_borrar)

                product_tmpl_id = registro['product_tmpl_id'][0]
                obj_dict_template['image'] = obj.image_small
#                obj_dict_template['sinc1_id'] = obj.id
                obj_dict_template['sinc_id'] = obj.product_tmpl_id.id
                logging.warn(obj_dict_template)
                conexion['models'].execute_kw(conexion['database'], conexion['uid'], conexion['password'], 'product.template', 'write', [[product_tmpl_id], obj_dict_template])

