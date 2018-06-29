# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError
import xmlrpclib
import datetime
import urllib, base64
import logging
import random

class Sinc_Base(models.Model):
    _name = 'sinc.base'

    @api.multi
    def _buscar(self, conexion, res_model, filtro):
        ids = conexion['models'].execute_kw(conexion['database'], conexion['uid'], conexion['password'], res_model, 'search', [filtro])
        if ids:
            return ids
        else:
            return False

    def _leer(self, conexion, res_model, ids_array):
        registros = conexion['models'].execute_kw(conexion['database'], conexion['uid'], conexion['password'], res_model, 'read', ids_array)
        if registros:
            return registros
        else:
            return False

    def preparar_filtro_buscar_origen(self, trigger_id):
        filtro = self.filtro_origen_base()
        if trigger_id != '':
            filtro.append(('id', '=', trigger_id))
        return filtro

    def preparar_filtro_buscar_destino(self, conexion, obj):
        filtro = []
        for llave in self.llaves():
            if llave == 'parent_id':
                filtro.append([llave, '=', '---'])
            else:
                filtro.append([llave, '=', obj[llave]])
        return filtro

    def _preparar_diccionario(self, conexion, obj):
        dict = {}
        for campo in self.campos()['estandar']:
            dict[campo] = obj[campo]

        m2o_dict = self._preparar_m2o(conexion, obj)
        for campo in m2o_dict:
            dict[campo] = m2o_dict[campo]
        return dict


    def _preparar_m2o(self, conexion, obj):
        dict = {}
        for campo in self.campos()['m2o']:
            if obj[campo[0]]:
                sinc_obj = self.env[campo[1]]
                id = self._buscar(conexion, sinc_obj.res_model(), sinc_obj.preparar_filtro_buscar_destino(conexion, obj[campo[0]]))
                if id:
                    dict[campo[0]] = id[0]
        return dict

    @api.multi
    def transferir(self, conexion, obj):
        obj_dict = self._preparar_diccionario(conexion, obj)
        logging.getLogger('obj.name').warn(obj.name)
        logging.getLogger('self.res_model()').warn(self.res_model())
        logging.getLogger('self.preparar_filtro_buscar_destino(conexion, obj)').warn(self.preparar_filtro_buscar_destino(conexion, obj))
        obj_id = self._buscar(conexion, self.res_model(), self.preparar_filtro_buscar_destino(conexion, obj))
        if not obj_id:
            logging.warn(self.res_model())
            logging.warn(self.preparar_filtro_buscar_destino(conexion, obj))
            logging.warn(self.res_model())
            logging.warn(obj)
            logging.warn(obj_dict)

            nuevo_obj_destino_id = conexion['models'].execute_kw(conexion['database'], conexion['uid'], conexion['password'], self.res_model(), 'create', [obj_dict])
        else:
            conexion['models'].execute_kw(conexion['database'], conexion['uid'], conexion['password'], self.res_model(), 'write', [[obj_id[0]], obj_dict])
            nuevo_obj_destino_id = obj_id[0]
        return nuevo_obj_destino_id



class Sinc_PDV_Ubicaciones(models.Model):
    _name = 'sinc_pdv.out.ubicaciones'
    _inherit = 'sinc.base'

    def res_model(self):
        return 'stock.location'

    def campos(self):
        dict = {}
        dict['estandar'] = ['name', 'usage', 'scrap_location', 'return_location', 'posx', 'posy', 'posz', 'barcode']
        dict['m2o'] = [['location_id', 'sinc_pdv.out.ubicaciones']]
#        dict['o2m'] = []
#        dict['m2m'] = []
        return dict

    def filtro_origen_base(self):
        return [('company_id', '=', 1), ('barcode', '!=', False)]

    def llaves(self):
        return ['barcode']


class Sinc_PDV_Pos_Sat_Resolucion(models.Model):
    _name = 'sinc_pdv.out.pos_sat_resolucion'
    _inherit = 'sinc.base'

    def res_model(self):
        return 'pos_sat.resolucion'

    def campos(self):
        dict = {}
        dict['estandar'] = ['name', 'fecha', 'serie', 'direccion', 'inicial', 'final', 'primera', 'valido', 'tipo_doc', 'fecha_ingreso', 'fecha_vencimiento']
        dict['m2o'] = []
#        dict['o2m'] = []
#        dict['m2m'] = []
        return dict

    def filtro_origen_base(self):
        return [('name', '!=', '')]

    def llaves(self):
        return ['name']


class Sinc_PDV_Diarios(models.Model):
    _name = 'sinc_pdv.out.diarios'
    _inherit = 'sinc.base'

    def res_model(self):
        return 'account.journal'

    def campos(self):
        dict = {}
        dict['estandar'] = ['sinc_id', 'name', 'type', 'code', 'requiere_resolucion', 'clave_gface', 'tipo_documento_gface', 'serie_documento_gface', 'serie_gface', 'numero_resolucion_gface', 'fecha_resolucion_gface', 'rango_inicial_gface', 'rango_final_gface', 'numero_establecimiento_gface', 'dispositivo_gface', 'nombre_establecimiento_gface']
        dict['m2o'] = []
#        dict['o2m'] = []
#        dict['m2m'] = []
        return dict

    def filtro_origen_base(self):
        return [('company_id', '=', 1)]

    def llaves(self):
        return ['sinc_id']

    def copiar_secuencia(self, conexion, diario, nuevo_diario_destino_id):
        diario_destino = self._leer(conexion, self.res_model(), [nuevo_diario_destino_id])[0]
        secuencia_id = diario_destino['sequence_id'][0]
        resolucion_id = self._buscar(conexion, 'pos_sat.resolucion', [['name', '=', diario.sequence_id.resolucion_id.name]])
        if resolucion_id:
            conexion['models'].execute_kw(conexion['database'], conexion['uid'], conexion['password'], 'ir.sequence', 'write', [[diario_destino['sequence_id'][0]], {'resolucion_id': resolucion_id[0]}])


class Sinc_PDV_Categorias_PDV(models.Model):
    _name = 'sinc_pdv.out.categorias_pdv'
    _inherit = 'sinc.base'

    def res_model(self):
        return 'pos.category'

    def campos(self):
        dict = {}
        dict['estandar'] = ['name', 'sequence']
        dict['m2o'] = [['parent_id', 'sinc_pdv.out.categorias_pdv']]
#        dict['o2m'] = []
#        dict['m2m'] = []
        return dict

    def filtro_origen_base(self):
        return []

    def llaves(self):
        return ['sequence']

    def preparar_filtro_buscar_destino2(self, conexion, obj):
        filtro = []
        categoria_ids = self._buscar(conexion, 'pos.category', [['name', '!=', '']])
        if categoria_ids:
            for categoria in self._leer(conexion, self.res_model(), [categoria_ids]):
                nombre_origen = ''
                if obj.parent_id:
                    nombre_origen = obj.parent_id.name
                nombre_origen += ' - ' + obj.name

                nombre_destino = ''
                if categoria['parent_id']:
                    nombre_destino = categoria['parent_id'][1]
                nombre_destino += ' - ' + categoria['name']

                if nombre_origen == nombre_destino:
                    filtro.append(['name', '=', obj.name])
                    filtro.append(['parent_id', '=', categoria['id']])
                else:
                    filtro.append(['parent_id', '=', -1])
        else:
            filtro.append(['parent_id', '=', -1])

        return filtro


class Sinc_PDV(models.Model):
    _name = 'sinc_pdv.out'
    _inherit = 'sinc.base'

    def _preparar_diccionario2(self, obj, campos):
        dict = {}
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
            id = self._buscar(conexion, res_model, [[filtro_existe, '=', line[filtro_existe]]])
            if id:
                ids.append((4, id[0]))
        return ids

    @api.multi
    def _ubicaciones(self, conexion, trigger_id = ''):
        sinc_ubicaciones_obj = self.env['sinc_pdv.out.ubicaciones']
        for ubicacion in self.env[sinc_ubicaciones_obj.res_model()].search(sinc_ubicaciones_obj.preparar_filtro_buscar_origen(trigger_id), order='id asc'):
            sinc_ubicaciones_obj.transferir(conexion, ubicacion)

    @api.multi
    def _pos_sat_resolucion(self, conexion, trigger_id = ''):
        sinc_resolucion_obj = self.env['sinc_pdv.out.pos_sat_resolucion']
        for resolucion in self.env[sinc_resolucion_obj.res_model()].search(sinc_resolucion_obj.preparar_filtro_buscar_origen(trigger_id), order='id asc'):
            sinc_resolucion_obj.transferir(conexion, resolucion)

    @api.multi
    def _diarios(self, conexion, trigger_id = ''):
        sinc_diarios_obj = self.env['sinc_pdv.out.diarios']
        x = 1
        for diario in self.env[sinc_diarios_obj.res_model()].search(sinc_diarios_obj.preparar_filtro_buscar_origen(trigger_id), order='id asc'):
            logging.getLogger('Diario No. ').warn(x)
            x += 1
            nuevo_diario_destino_id = sinc_diarios_obj.transferir(conexion, diario)
            if nuevo_diario_destino_id:
                sinc_diarios_obj.copiar_secuencia(conexion, diario, nuevo_diario_destino_id)

    @api.multi
    def _categorias_pdv(self, conexion, trigger_id = ''):
        sinc_categorias_obj = self.env['sinc_pdv.out.categorias_pdv']
        for categoria in self.env[sinc_categorias_obj.res_model()].search(sinc_categorias_obj.preparar_filtro_buscar_origen(trigger_id), order='id asc'):
            sinc_categorias_obj.transferir(conexion, categoria)

    @api.multi
    def _categorias_producto(self, conexion, trigger_id = ''):
        res_model = 'product.category'
        campos = ['name', 'type', 'sinc_id']
        filtro_search = []
        if trigger_id != '':
            filtro_search.append(('id', '=', trigger_id))
        filtro_existe = 'sinc_id'
        logging.warn(filtro_search)
        for obj in self.env[res_model].search(filtro_search, order='parent_id'):
            obj_dict = self._preparar_diccionario2(obj, campos)
            parent_id = self._buscar(conexion, 'product.category', [[filtro_existe, '=', obj.parent_id.sinc_id]])
            logging.getLogger('PARENT_ID... ').warn(parent_id)
            logging.getLogger('obj.sinc_id... ').warn(obj.sinc_id)
            if parent_id:
                obj_dict['parent_id'] = parent_id[0]
            obj_id = self._buscar(conexion, res_model, [[filtro_existe, '=', obj[filtro_existe]]])
            if not obj_id:
                logging.warn(obj_dict)
                obj_id = conexion['models'].execute_kw(conexion['database'], conexion['uid'], conexion['password'], res_model, 'create', [obj_dict])
                conexion['models'].execute_kw(conexion['database'], conexion['uid'], conexion['password'], res_model, 'write', [[obj_id], {'create_date': obj.create_date}])
            else:
                logging.warn(obj_dict)
                conexion['models'].execute_kw(conexion['database'], conexion['uid'], conexion['password'], res_model, 'write', [[obj_id[0]], obj_dict])


    @api.multi
    def _pdv(self, conexion, trigger_id = ''):
        res_model = 'pos.config'
        campos = ['name', 'active', 'group_by', 'allow_discount', 'allow_price_change', 'takeout_option', 'ask_tag_number', 'tipo_impresora', 'iface_precompute_cash', 'iface_invoicing']
        filtro_search = ['|', ('active','=',True), ('active','=',False)]
        if trigger_id != '':
            filtro_search.append(('id', '=', trigger_id))
        filtro_existe = 'name'
        for obj in self.env[res_model].search(filtro_search, order='id asc'):
            obj_dict = self._preparar_diccionario2(obj, campos)
            journal_id = self._buscar(conexion, 'account.journal', [['code', '=', obj.journal_id.code]])
            if journal_id:
                obj_dict['journal_id'] = journal_id[0]
            stock_location_id = self._buscar(conexion, 'stock.location', [['barcode', '=', obj.stock_location_id.barcode]])
            if stock_location_id:
                obj_dict['stock_location_id'] = stock_location_id[0]
            invoice_journal_id = self._buscar(conexion, 'account.journal', [['code', '=', obj.invoice_journal_id.code]])
            if invoice_journal_id:
                obj_dict['invoice_journal_id'] = invoice_journal_id[0]

            iface_start_categ_id = self._buscar(conexion, 'pos.category', [['sequence', '=', obj.iface_start_categ_id.sequence]])
            if iface_start_categ_id:
                obj_dict['iface_start_categ_id'] = iface_start_categ_id[0]

#            categoria_id = self._buscar(conexion, 'product.category', [['sinc_id', '=', obj.sinc_id.sinc_id]])
#            if categoria_id:
#                obj_dict['categoria_id'] = categoria_id[0]

            obj_id = self._buscar(conexion, res_model, [[filtro_existe, '=', obj[filtro_existe]]])
            if not obj_id:

                m2m_res_model = 'account.journal'
                m2m_obj = obj.journal_ids
                m2m_campo = 'journal_ids'
                m2m_filtro_existe = 'code'
                obj_dict['journal_ids'] = self._preparar_m2m(conexion, m2m_res_model, m2m_obj, m2m_campo, m2m_filtro_existe)

                m2m_res_model = 'product.category'
                m2m_obj = obj.categorias_id
                m2m_campo = 'categorias_id'
                m2m_filtro_existe = 'sinc_id'
                obj_dict['categorias_id'] = self._preparar_m2m(conexion, m2m_res_model, m2m_obj, m2m_campo, m2m_filtro_existe)

                conexion['models'].execute_kw(conexion['database'], conexion['uid'], conexion['password'], res_model, 'create', [obj_dict])
            else:
                registro = self._leer(conexion, 'pos.config', [obj_id[0]])[0]

                m2m_res_model = 'account.journal'
                m2m_obj = obj.journal_ids
                m2m_campo = 'journal_ids'
                m2m_filtro_existe = 'code'
                m2m_ids_borrar = registro['journal_ids']
                obj_dict['journal_ids'] = self._preparar_m2m(conexion, m2m_res_model, m2m_obj, m2m_campo, m2m_filtro_existe, m2m_ids_borrar)

                m2m_res_model = 'product.category'
                m2m_obj = obj.categorias_id
                m2m_campo = 'categorias_id'
                m2m_filtro_existe = 'sinc_id'
                m2m_ids_borrar = registro['categorias_id']
                obj_dict['categorias_id'] = self._preparar_m2m(conexion, m2m_res_model, m2m_obj, m2m_campo, m2m_filtro_existe, m2m_ids_borrar)

                conexion['models'].execute_kw(conexion['database'], conexion['uid'], conexion['password'], res_model, 'write', [[obj_id[0]], obj_dict])

    @api.multi
    def _usuarios(self, conexion, trigger_id = ''):
        res_model = 'res.users'
        campos = ['name', 'login', 'tz', 'notify_email', 'signature', 'barcode', 'pos_security_pin', 'password_crypt']
        filtro_search = [('company_id', '=', 1), ('default_pos_id', '!=', False), '|', ('active','=',True), ('active','=',False)]
        if trigger_id != '':
            filtro_search.append(('id', '=', trigger_id))
        filtro_existe = 'login'
        for obj in self.env[res_model].search(filtro_search, order='id asc'):
            obj_dict = self._preparar_diccionario2(obj, campos)
            default_pos_id = self._buscar(conexion, 'pos.config', [['name', '=', obj.default_pos_id.name]])
            if default_pos_id:
                obj_dict['default_pos_id'] = default_pos_id[0]
            default_location_id = self._buscar(conexion, 'stock.location', [['barcode', '=', obj.default_location_id.barcode]])
            if default_location_id:
                obj_dict['default_location_id'] = default_location_id[0]
            obj_id = self._buscar(conexion, res_model, [[filtro_existe, '=', obj[filtro_existe]]])
            if not obj_id:
                logging.getLogger('CREAR USUARIO').warn(obj_dict)
                conexion['models'].execute_kw(conexion['database'], conexion['uid'], conexion['password'], res_model, 'create', [obj_dict])
            else:
                conexion['models'].execute_kw(conexion['database'], conexion['uid'], conexion['password'], res_model, 'write', [[obj_id[0]], obj_dict])

    @api.multi
    def _productos(self, conexion, trigger_id = ''):
        res_model = 'product.product'
        campos = ['name', 'sale_ok', 'purchase_ok', 'type', 'default_code', 'barcode', 'lst_price', 'standard_price', 'sale_delay', 'produce_delay', 'available_in_pos', 'to_weight', 'description_sale', 'description_purchase', 'description_picking']
        filtro_search = [('company_id', '=', 1), ('default_code', '!=', False)]
        if trigger_id != '':
            filtro_search.append(('id', '=', trigger_id))
        filtro_existe = 'default_code'
        logging.warn(filtro_search)
        for obj in self.env[res_model].search(filtro_search, order='id asc'):
            obj_dict_template = {}
            obj_dict = self._preparar_diccionario2(obj, campos)
            categ_id = self._buscar(conexion, 'product.category', [['sinc_id', '=', obj.categ_id.sinc_id]])
            if categ_id:
                obj_dict_template['categ_id'] = categ_id[0]

            if obj.pos_categ_id:
                pos_categ_id = self._buscar(conexion, 'pos.category', [['sequence', '=', obj.pos_categ_id.sequence]])
                if pos_categ_id:
                    obj_dict['pos_categ_id'] = pos_categ_id[0]

            obj_id = self._buscar(conexion, res_model, [[filtro_existe, '=', obj[filtro_existe]]])
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

                registro = self._leer(conexion, res_model, [obj_id])[0]
                product_tmpl_id = registro['product_tmpl_id'][0]
                obj_dict_template['image'] = obj.image_small
                conexion['models'].execute_kw(conexion['database'], conexion['uid'], conexion['password'], 'product.template', 'write', [[product_tmpl_id], obj_dict_template])

            else:

                registro = self._leer(conexion, res_model, [obj_id[0]])[0]

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
                logging.warn(obj_dict_template)
                conexion['models'].execute_kw(conexion['database'], conexion['uid'], conexion['password'], 'product.template', 'write', [[product_tmpl_id], obj_dict_template])

    @api.multi
    def _pos_gt_extra(self, conexion, trigger_id = ''):
        res_model = 'pos_gt.extra'
        campos = ['name', 'type']
        filtro_search = []
        if trigger_id != '':
            filtro_search.append(('id', '=', trigger_id))
        filtro_existe = 'name'
        for obj in self.env[res_model].search(filtro_search, order='id asc'):
            obj_dict = self._preparar_diccionario2(obj, campos)
            obj_id = self._buscar(conexion, res_model, [[filtro_existe, '=', obj[filtro_existe]]])
            if not obj_id:
                products_id = []
                for line in obj.products_id:
                    product_id = self._buscar(conexion, 'product.product', [['default_code', '=', line.product_id.default_code]])
                    if product_id:
                        products_id.append((0, 0, {
                            'product_id': product_id[0],
                            'name': line.name,
                            'qty': line.qty,
                            'price_extra': line.price_extra,
                        }))
                obj_dict['products_id'] = products_id
                conexion['models'].execute_kw(conexion['database'], conexion['uid'], conexion['password'], res_model, 'create', [obj_dict])
            else:
                registro = self._leer(conexion, 'pos_gt.extra', [obj_id[0]])[0]
                if registro['products_id'] != []:
                    conexion['models'].execute_kw(conexion['database'], conexion['uid'], conexion['password'], 'pos_gt.extra.line', 'unlink', [registro['products_id']])

                products_id = []
                for line in obj.products_id:
                    product_id = self._buscar(conexion, 'product.product', [['default_code', '=', line.product_id.default_code]])
                    if product_id:
                        products_id.append((0, 0, {
                            'product_id': product_id[0],
                            'name': line.name,
                            'qty': line.qty,
                            'price_extra': line.price_extra,
                        }))
                obj_dict['products_id'] = products_id
                conexion['models'].execute_kw(conexion['database'], conexion['uid'], conexion['password'], res_model, 'write', [[obj_id[0]], obj_dict])

    @api.multi
    def _lista_materiales(self, conexion, trigger_id = ''):
        res_model = 'mrp.bom'
        campos = ['code', 'product_qty', 'type']
        filtro_search = [('active', '=', True), ('code', '!=', False)]
        if trigger_id != '':
            filtro_search.append(('id', '=', trigger_id))
        filtro_existe = 'code'
        for obj in self.env[res_model].search(filtro_search, order='id asc'):
            logging.getLogger('Lista').warn(obj.code)
            obj_dict = self._preparar_diccionario2(obj, campos)
            product_tmpl_id = self._buscar(conexion, 'product.template', [['default_code', '=', obj.product_tmpl_id.default_code]])
            if product_tmpl_id:
                obj_dict['product_tmpl_id'] = product_tmpl_id[0]

                obj_id = self._buscar(conexion, res_model, [[filtro_existe, '=', obj[filtro_existe]]])
                if not obj_id:
                    bom_line_ids = []
                    for line in obj.bom_line_ids:
                        product_id = self._buscar(conexion, 'product.product', [['default_code', '=', line.product_id.default_code]])
                        logging.getLogger('PRODUCT_ID ').warn(product_id)
                        if product_id:
                            bom_line_ids.append((0, 0, {
                                'product_id': product_id[0],
                                'product_qty': line.product_qty,
                            }))
                    obj_dict['bom_line_ids'] = bom_line_ids
                    logging.warn(obj_dict)
                    obj_id = conexion['models'].execute_kw(conexion['database'], conexion['uid'], conexion['password'], res_model, 'create', [obj_dict])
                else:
                    registro = self._leer(conexion, 'mrp.bom', [obj_id[0]])[0]
                    conexion['models'].execute_kw(conexion['database'], conexion['uid'], conexion['password'], 'mrp.bom.line', 'unlink', [registro['bom_line_ids']])

                    bom_line_ids = []
                    for line in obj.bom_line_ids:
                        product_id = self._buscar(conexion, 'product.product', [['default_code', '=', line.product_id.default_code]])
                        if product_id:
                            bom_line_ids.append((0, 0, {
                                'product_id': product_id[0],
                                'product_qty': line.product_qty,
                            }))
                    obj_dict['bom_line_ids'] = bom_line_ids

                    conexion['models'].execute_kw(conexion['database'], conexion['uid'], conexion['password'], res_model, 'write', [[obj_id[0]], obj_dict])

    @api.multi
    def _ajuste_inicial(self, conexion):
        self._cr.execute("""\
            SELECT location_id, product_id, SUM(qty) as product_qty
            FROM stock_quant
            WHERE location_id IN (SELECT distinct(stock_location_id) FROM pos_config)
            GROUP BY location_id, product_id
            """)
        dict = {}
        for location_id, product_id, product_qty in self._cr.fetchall():
            ubicacion_bd_origen = self.env['stock.location'].browse(location_id)
            producto_bd_origen = self.env['product.product'].browse(product_id)
            ubicacion_bd_destino_id = self._buscar(conexion, 'stock.location', [['barcode', '=', ubicacion_bd_origen.barcode]])
            producto_bd_destino_id = self._buscar(conexion, 'product.product', [['default_code', '=', producto_bd_origen.default_code]])

            if ubicacion_bd_destino_id and producto_bd_destino_id:
                ubicacion_bd_destino_id = ubicacion_bd_destino_id[0]
                producto_bd_destino_id = producto_bd_destino_id[0]
                if ubicacion_bd_destino_id not in dict:
                    dict[ubicacion_bd_destino_id] = {}
                    dict[ubicacion_bd_destino_id]['name'] = 'Ajuste inicial - ' + ubicacion_bd_origen.name
                    dict[ubicacion_bd_destino_id]['location_id'] = ubicacion_bd_destino_id
#                    dict[ubicacion_bd_destino_id]['filter'] = 'partial'
                    dict[ubicacion_bd_destino_id]['line_ids'] = []

                if product_qty < 0:
                    product_qty = 0
                dict[ubicacion_bd_destino_id]['line_ids'].append((0, 0, {
                    'location_id': ubicacion_bd_destino_id,
                    'product_id': producto_bd_destino_id,
                    'product_qty': product_qty,
                }))

        for ubicacion_bd_destino_id in dict:
            logging.warn(dict[ubicacion_bd_destino_id])
            obj_id = conexion['models'].execute_kw(conexion['database'], conexion['uid'], conexion['password'], 'stock.inventory', 'create', [dict[ubicacion_bd_destino_id]])
            logging.warn(obj_id)
            conexion['models'].execute_kw(conexion['database'], conexion['uid'], conexion['password'], 'stock.inventory', 'action_start', [[obj_id]])
            conexion['models'].execute_kw(conexion['database'], conexion['uid'], conexion['password'], 'stock.inventory', 'action_done', [[obj_id]])


    @api.multi
    def iniciar(self, conexion, model = '', obj = ''):
        common = xmlrpclib.ServerProxy('{}/xmlrpc/2/common'.format(conexion['url']))
        conexion['uid'] = common.authenticate(conexion['database'], conexion['username'], conexion['password'], {})
        conexion['models'] = xmlrpclib.ServerProxy('{}/xmlrpc/2/object'.format(conexion['url']))

        # Ejemplo cargar imagen
        # producto = self.env['product.product'].browse(624)
        # conexion['models'].execute_kw(conexion['database'], conexion['uid'], conexion['password'], 'product.template', 'write', [[40], {'image': producto.image}])

        logging.getLogger('MODEL ').warn(model)
        logging.getLogger('OBJ ').warn(obj)
        if model != '':
            ubicaciones_obj = self.env['stock.location']
            resolucion_obj = self.env['pos_sat.resolucion']
            diarios_obj = self.env['account.journal']
            categorias_pdv_obj = self.env['pos.category']
            pdv_obj = self.env['pos.config']
            usuarios_obj = self.env['res.users']
            extra_obj = self.env['pos_gt.extra']
            lista_materiales_obj = self.env['mrp.bom']
            productos_obj = self.env['product.product']

            logging.getLogger('COMP ').warn(model == productos_obj)

            if model == ubicaciones_obj:
                self._ubicaciones(conexion, obj.id)
            elif model == resolucion_obj:
                self._pos_sat_resolucion(conexion, obj.id)
            elif model == diarios_obj:
                self._diarios(conexion, obj.id)
            elif model == categorias_pdv_obj:
                self._categorias_pdv(conexion, obj.id)
            elif model == pdv_obj:
                self._pdv(conexion, obj.id)
            elif model == usuarios_obj:
                self._usuarios(conexion, obj.id)
            elif model == extra_obj:
                self._pos_gt_extra(conexion, obj.id)
            elif model == lista_materiales_obj:
                self._lista_materiales(conexion, obj.id)
            elif model == productos_obj:
                self._productos(conexion, obj.id)
        else:
            logging.warn('INICIO')
            # logging.warn('Transfiriendo ubicaciones')
            # self._ubicaciones(conexion)
            # logging.warn('Transfiriendo pos_sat_resoluciones')
            # self._pos_sat_resolucion(conexion)
            # logging.warn('Transfiriendo diarios')
            # self._diarios(conexion)
            # logging.warn('Transfiriendo categorias de producto')
            # self._categorias_producto(conexion)
            # self._categorias_producto(conexion)
            # logging.warn('Transfiriendo categorias de pdv')
            # self._categorias_pdv(conexion)
            # self._categorias_pdv(conexion)
            # logging.warn('Transfiriendo pdv')
            # self._pdv(conexion)
            # logging.warn('Transfiriendo usuarios')
            # self._usuarios(conexion)
            # logging.warn('Transfiriendo productos')
            # self._productos(conexion)
            # logging.warn('Transfiriendo pos_gt_extra')
            # self._pos_gt_extra(conexion)
            # logging.warn('Transfiriendo productos')
            # self._productos(conexion)
            logging.warn('Transfiriendo lista de materiales')
            self._lista_materiales(conexion)
            # logging.warn('Creando ajuste inicial')
            # self._ajuste_inicial(conexion)
            logging.warn('FIN!!!')

class Sinc_PDV_in(models.Model):
    _name = 'sinc_pdv.in'
    _inherit = 'sinc.base'


    @api.multi
    def _ajustes_inventario(self, conexion):
#        ubicacion_ids = []
        pos = {}
        config_ids = self._buscar(conexion, 'pos.config', [['active', '=', True]])
        for config in self._leer(conexion, 'pos.config', [config_ids]):
#            if config['stock_location_id'][0] not in ubicacion_ids:
            if config['stock_location_id'][0] not in pos.keys():
                logging.getLogger('config.name... ').warn(config['name'])
                logging.getLogger('config.stock_location_id... ').warn(config['stock_location_id'][0])
#                ubicacion_ids.append(config['stock_location_id'][0])
                ubicacion_destino = self._leer(conexion, 'stock.location', [config['stock_location_id'][0]])
                if ubicacion_destino[0]['barcode']:
                    logging.getLogger('ubicacion_destino... ').warn(ubicacion_destino)
                    ubicacion_origen = self.env['stock.location'].search([('barcode', '=', ubicacion_destino[0]['barcode'])])
                    if ubicacion_origen:
                        ubicacion_origen = ubicacion_origen[0]
                        logging.getLogger('ubicacion_origen... ').warn(ubicacion_origen)
                        config_origen = self.env['pos.config'].search([('stock_location_id', '=', ubicacion_origen.id)])
                        if config_origen:
                            config_origen = config_origen[0]
                            pos[config['stock_location_id'][0]] = config_origen.analytic_account_id.id

        limit = 1
#        for ubicacion_id in ubicacion_ids:
        for ubicacion_id in pos:
            if limit <= 2:
                logging.getLogger('LIMIT ... ').warn(limit)
                inventario_destino_id = conexion['models'].execute_kw(conexion['database'], conexion['uid'], conexion['password'], 'stock.inventory', 'search', [[['name', 'not like', 'Ajuste inicial'],['state', '=', 'done'],['location_id', '=', ubicacion_id]]], {'order': 'date desc', 'limit': 1})
                logging.getLogger('inventario_destino_id ... ').warn(inventario_destino_id)
                if inventario_destino_id:
                    inventario_destino = self._leer(conexion, 'stock.inventory', [inventario_destino_id])[0]
                    inventario_origen_id = self.env['stock.inventory'].search([('name', '=', inventario_destino['name'])])
                    if not inventario_origen_id:

                        ubicacion_destino = self._leer(conexion, 'stock.location', [inventario_destino['location_id'][0]])
                        ubicacion_origen = self.env['stock.location'].search([('barcode', '=', ubicacion_destino[0]['barcode'])])[0]
                        logging.getLogger('ubicacion_destino ...').warn(ubicacion_destino)
                        logging.getLogger('ubicacion_origen ...').warn(ubicacion_origen)
                        dict = {}
                        dict['name'] = inventario_destino['name']
                        dict['date'] = inventario_destino['date']
                        dict['location_id'] = ubicacion_origen.id
                        dict['filter'] = 'partial'
                        dict['cuenta_analitica_id'] = pos[ubicacion_id]
                        line_ids = []
                        logging.warn('INICIO PREPARAR PRODUCTOS ... ')
                        for linea in self._leer(conexion, 'stock.inventory.line', [inventario_destino['line_ids']]):
                            producto_destino = self._leer(conexion, 'product.product', [linea['product_id'][0]])
                            logging.getLogger('PRODUCTO DESTINO ....').warn(producto_destino[0]['default_code'])
                            producto_origen = self.env['product.product'].search([('default_code', '=', producto_destino[0]['default_code']), '|', ('active','=',True), ('active','=',False)])[0]

                            line_ids.append((0, 0, {
                                'location_id': ubicacion_origen.id,
                                'product_id': producto_origen.id,
                                'product_qty': linea['product_qty'],
                            }))
                            dict['line_ids'] = line_ids

                        logging.warn('FIN PREPARAR PRODUCTOS ... ')

                        obj = self.env['stock.inventory'].create(dict)
                        obj.write({'date': inventario_destino['date']})
                        logging.getLogger('INVENTARIO CREADO ....').warn(obj)
                        logging.getLogger('LIMIT... ').warn(limit)
                        logging.getLogger('NOMBRE DESTINO... ').warn(inventario_destino['name'])
                        logging.getLogger('FECHA DESTINO... ').warn(inventario_destino['date'])
                        logging.getLogger('FECHA ORIGEN... ').warn(obj.date)
                        logging.getLogger('INVENTARIO DESTINO ....').warn(inventario_destino)
                        obj.action_start()
                        logging.warn('FINALIZADO action_start')
                        obj.action_done()
                        logging.warn('FINALIZADO action_done')
                        logging.getLogger('FINALIZADO TRASLADO No... ').warn(limit)
                        limit += 1


    @api.multi
    def _ordenes_pdv(self, conexion, config_ids=False):
#        sesion_ids = self._buscar(conexion, 'pos.session', [['state', '=', 'closed']])
        if config_ids:
            sesion_filtro = [['state', '=', 'closed'], ['config_id', 'in', config_ids]]
        else:
            sesion_filtro = [['state', '=', 'closed']]

        sesion_ids = conexion['models'].execute_kw(conexion['database'], conexion['uid'], conexion['password'], 'pos.session', 'search', [sesion_filtro], {'order': 'config_id asc'})
        logging.getLogger('SESION_IDS ...').warn(sesion_ids)
        limit = 1
        sesion_ids_random = random.sample(sesion_ids, len(sesion_ids))
#        for sesion_destino in conexion['models'].execute_kw(conexion['database'], conexion['uid'], conexion['password'], 'pos.session', 'read', [sesion_ids], {'fields': ['name','config_id','id','start_at']}):
        for sesion_id in sesion_ids_random:
            if limit <= 5:
                sesion_destino = conexion['models'].execute_kw(conexion['database'], conexion['uid'], conexion['password'], 'pos.session', 'read', [[sesion_id]], {'fields': ['name','config_id','id','start_at']})
                sesion_destino = sesion_destino[0]
                sesion_origen_id = self.env['pos.session'].search([('name', '=', sesion_destino['name'])])
                logging.getLogger('SESION DESTINO... ').warn(sesion_destino)
                if not sesion_origen_id:
                    logging.warn(sesion_origen_id)
                    try:
                        pos_config_destino = self._leer(conexion, 'pos.config', [sesion_destino['config_id'][0]])
                        pos_config_origen = self.env['pos.config'].search([('name', '=', pos_config_destino[0]['name'])])[0]
                        logging.getLogger('sesion_destino name ').warn(sesion_destino['name'])
                        sesion_origen_id = self.env['pos.session'].create({'name': sesion_destino['name'], 'config_id': pos_config_origen.id})
                        sesion_origen_id.write({'name': sesion_destino['name']})
                        logging.warn(sesion_origen_id)
                        logging.getLogger('SESION STATE').warn(sesion_origen_id.statement_ids)
                        sesion_origen_id.action_pos_session_open()

                        ordenes_destino_ids = conexion['models'].execute_kw(conexion['database'], conexion['uid'], conexion['password'], 'pos.order', 'search', [[['session_id', '=', sesion_destino['id']]]], {'order': 'id asc'})
        #                ordenes_destino_ids = self._buscar(conexion, 'pos.order', [['session_id', '=', sesion_destino['id']]])
                        lineas_destino_ids = self._buscar(conexion, 'pos.order.line', [['order_id', 'in', ordenes_destino_ids]])
                        logging.getLogger('ordenes_destino_ids... ').warn(ordenes_destino_ids)
                        if ordenes_destino_ids and ordenes_destino_ids != []:
                            lineas_pedido = {}
                            for linea in self._leer(conexion, 'pos.order.line', [lineas_destino_ids]):
                                producto_destino = self._leer(conexion, 'product.product', [linea['product_id'][0]])[0]
                                # logging.getLogger('producto_destino... ').warn(producto_destino)
                                producto_origen = self.env['product.product'].search([('default_code', '=', producto_destino['default_code'])])
                                # logging.getLogger('producto_origen... ').warn(producto_origen)
                                key = str(producto_origen.id) + '-' + str(linea['price_unit'])
                                if key not in lineas_pedido:
                                    lineas_pedido[key] = {}
                                    lineas_pedido[key]['product_id'] = producto_origen.id
                                    lineas_pedido[key]['price_unit'] = linea['price_unit']
                                    lineas_pedido[key]['qty'] = linea['qty']
                                else:
                                    lineas_pedido[key]['qty'] += linea['qty']

                            lineas = []
                            for key in lineas_pedido:
                                lineas.append((0, 0, {
                                    'product_id': lineas_pedido[key]['product_id'],
                                    'price_unit': lineas_pedido[key]['price_unit'],
                                    'qty': lineas_pedido[key]['qty'],
                                }))

                            nombre_primera_factura = ''
                            nombre_ultima_factura = ''
                            x = 1
                            for pedido in self._leer(conexion, 'pos.order', [ordenes_destino_ids]):
                                logging.warn(pedido)
                                if pedido['invoice_id']:
                                    factura = self._leer(conexion, 'account.invoice', [pedido['invoice_id'][0]])
                                    logging.warn(factura)
                                    if factura:
                                        if x == 1:
                                            nombre_primera_factura = factura[0]['name']
                                            x += 1
                                        nombre_ultima_factura = factura[0]['name']

                            obj = self.env['pos.order'].create({
                                'session_id': sesion_origen_id.id,
                                'date_order': sesion_destino['start_at'],
                                'partner_id': pos_config_origen.default_client_id.id,
                                'lines': lineas,
                            })
                            logging.getLogger('LINEAS ...').warn(lineas)

                            pagos_destino_ids = self._buscar(conexion, 'account.bank.statement.line', [['pos_statement_id', 'in', ordenes_destino_ids]])
                            pagos = {}
                            for pago in self._leer(conexion, 'account.bank.statement.line', [pagos_destino_ids]):
                                diario_destino = self._leer(conexion, 'account.journal', [pago['journal_id'][0]])[0]
                                if diario_destino['code'] not in pagos:
                                    pagos[diario_destino['code']] = pago['amount']
                                else:
                                    pagos[diario_destino['code']] += pago['amount']
                                logging.getLogger('PAGO...').warn(pagos)
                            for journal_code in pagos:
                                diario_origen = self.env['account.journal'].search([('code', '=', journal_code)])
                                logging.getLogger('journal_code...').warn(journal_code)
                                obj.add_payment({'journal': diario_origen.id ,'amount': pagos[journal_code]})

                            logging.getLogger('obj.amount_total ...').warn(obj.amount_total)
                            obj.action_pos_order_paid()
                            obj.action_pos_order_invoice()

                            logging.warn(obj)
                            logging.warn(obj.invoice_id)
                            logging.warn(nombre_primera_factura + ' - ' + nombre_ultima_factura)
                            factura_origen = obj.invoice_id
                            factura_origen.write({'name': nombre_primera_factura + ' - ' + nombre_ultima_factura, 'date_invoice': sesion_destino['start_at']})

                            obj.invoice_id.sudo().action_invoice_open()
                            obj.account_move = obj.invoice_id.move_id

                        sesion_origen_id.action_pos_session_closing_control()
                        sesion_origen_id.action_pos_session_close()
                        limit += 1
                        logging.getLogger('LIMIT ..... ').warn(limit)
                    except:
                        logging.getLogger('ERROR ...').warn('No se pudo pagar el pedido.')
                        if obj:
                            obj.unlink()
                            if sesion_origen_id:
                                sesion_origen_id.unlink()
    #            if limit > 5:
    #                logging.getLogger('BREAK ..... ').warn(limit)
    #                break

    @api.multi
    def ordenes_pdv_par(self, conexion):
        common = xmlrpclib.ServerProxy('{}/xmlrpc/2/common'.format(conexion['url']))
        conexion['uid'] = common.authenticate(conexion['database'], conexion['username'], conexion['password'], {})
        conexion['models'] = xmlrpclib.ServerProxy('{}/xmlrpc/2/object'.format(conexion['url']))

        config_ids = conexion['models'].execute_kw(conexion['database'], conexion['uid'], conexion['password'], 'pos.config', 'search', [[['active', '=', True]]])
        ids = []
        for config_id in config_ids:
            if config_id % 2 == 0:
                ids.append(config_id)
        logging.getLogger('Diarios con ID par').warn(ids)
        self._ordenes_pdv(conexion, ids)

    @api.multi
    def ordenes_pdv_impar(self, conexion):
        common = xmlrpclib.ServerProxy('{}/xmlrpc/2/common'.format(conexion['url']))
        conexion['uid'] = common.authenticate(conexion['database'], conexion['username'], conexion['password'], {})
        conexion['models'] = xmlrpclib.ServerProxy('{}/xmlrpc/2/object'.format(conexion['url']))

        config_ids = conexion['models'].execute_kw(conexion['database'], conexion['uid'], conexion['password'], 'pos.config', 'search', [[['active', '=', True]]])
        ids = []
        for config_id in config_ids:
            if config_id % 2 != 0:
                ids.append(config_id)
        logging.getLogger('Diarios con ID impar').warn(ids)
        self._ordenes_pdv(conexion, ids)


    @api.multi
    def iniciar(self, conexion, model = '', obj = ''):
        common = xmlrpclib.ServerProxy('{}/xmlrpc/2/common'.format(conexion['url']))
        conexion['uid'] = common.authenticate(conexion['database'], conexion['username'], conexion['password'], {})
        conexion['models'] = xmlrpclib.ServerProxy('{}/xmlrpc/2/object'.format(conexion['url']))

        # self._ordenes_pdv(conexion)
        self._ajustes_inventario(conexion)
