# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError
import xmlrpclib
import datetime
import urllib, base64
import logging
import random
from dateutil import parser

# Este modulo utiliza el modulo complementario sinc_pdv_extra.

# La clase Sinc_PDV_Location define funciones necesarias para la sincronizacion de ubicaciones.
class Sinc_PDV_Ubicaciones(models.Model):
    _name = 'sinc_pdv.stock.location'
    _inherit = 'sinc_pdv.base'

    # La funcion res_model() devuelve el modelo relacionado con este objeto.
    def res_model(self):
        return 'stock.location'

    # La funcion campos() devuelve un diccionario con los campos que se desean transferir al servidor destino.
    # El diccionario puede contener las siguientes llaves: 'estandar', 'm2o', 'o2m', 'm2m'.
    # dict['estandar']: lista con campos que no son Many2one, One2many o Many2many. Ejemplo: campos tipo Integer, Char, Boolean, etc.
    # dict['m2o']: lista con campos Many2one. El formato es ['campo','modelo']
    # dict['o2m']: 
    # dict['m2m']: 
    def campos(self):
        dict = {}
        dict['estandar'] = ['active', 'name', 'usage', 'scrap_location', 'return_location', 'posx', 'posy', 'posz', 'barcode']
        dict['m2o'] = [['location_id', 'stock.location']]
        return dict

    # La funcion filtro_base_origen() devuelve el filtro predeterminado a la hora de hacer una busqueda en el servidor origen.
    def filtro_base_origen(self):
        return [('company_id', '=', 1), '|', ('active','=',True), ('active','=',False)]


class Sinc_PDV_resolucion(models.Model):
    _name = 'sinc_pdv.pos_sat.resolucion'
    _inherit = 'sinc_pdv.base'

    def res_model(self):
        return 'pos_sat.resolucion'

    def campos(self):
        dict = {}
        dict['estandar'] = ['name', 'fecha', 'serie', 'direccion', 'inicial', 'final', 'primera', 'valido', 'tipo_doc', 'fecha_ingreso', 'fecha_vencimiento']
        return dict

    def filtro_base_origen(self):
        return [('name', '!=', '')]


class Sinc_PDV_Diarios(models.Model):
    _name = 'sinc_pdv.account.journal'
    _inherit = 'sinc_pdv.base'

    def res_model(self):
        return 'account.journal'

    def campos(self):
        dict = {}
        dict['estandar'] = ['name', 'type', 'code', 'requiere_resolucion', 'clave_gface', 'tipo_documento_gface', 'serie_documento_gface', 'serie_gface', 'numero_resolucion_gface', 'fecha_resolucion_gface', 'rango_inicial_gface', 'rango_final_gface', 'numero_establecimiento_gface', 'dispositivo_gface', 'nombre_establecimiento_gface']
        return dict

    def filtro_base_origen(self):
        return [('company_id', '=', 1)]

    def transferir(self, conexion, diario_origen):
        status_transferir = super(Sinc_PDV_Diarios, self).transferir(conexion, diario_origen)
        if status_transferir['funcion'] == 'crear':
            self.out_copiar_secuencia(conexion, diario_origen, status_transferir['obj_id'])
        return status_transferir
        
    def out_copiar_secuencia(self, conexion, diario_origen, nuevo_diario_destino_id):
        diario_destino = self.leer_destino(conexion, self.res_model(), [nuevo_diario_destino_id])[0]
        secuencia_destino_id = diario_destino['sequence_id'][0]        
        sinc_resolucion_obj = self.env['sinc_pdv.pos_sat.resolucion']
        resolucion_id = self.buscar_destino(conexion, sinc_resolucion_obj.res_model(), sinc_resolucion_obj.filtro_buscar_destino(conexion, diario_origen.sequence_id.resolucion_id))
        if resolucion_id:
            self.modificar_destino(conexion, 'ir.sequence', secuencia_destino_id, {'resolucion_id': resolucion_id[0]})

class Sinc_PDV_Categorias_PDV(models.Model):
    _name = 'sinc_pdv.pos.category'
    _inherit = 'sinc_pdv.base'

    def res_model(self):
        return 'pos.category'

    def campos(self):
        dict = {}
        dict['estandar'] = ['name', 'sequence']
        dict['m2o'] = [['parent_id', 'pos.category']]
        return dict

    def filtro_base_origen(self):
        return []

class Sinc_PDV_Categorias_Producto(models.Model):
    _name = 'sinc_pdv.product.category'
    _inherit = 'sinc_pdv.base'

    def res_model(self):
        return 'product.category'

    def campos(self):
        dict = {}
        dict['estandar'] = ['name', 'type']
        dict['m2o'] = [['parent_id', 'product.category']]
        return dict

    def filtro_base_origen(self):
        return []

class Sinc_PDV_Punto_De_Venta(models.Model):
    _name = 'sinc_pdv.pos.config'
    _inherit = 'sinc_pdv.base'

    def res_model(self):
        return 'pos.config'

    def campos(self):
        dict = {}
        dict['estandar'] = ['active', 'name', 'group_by', 'allow_discount', 'allow_price_change', 'takeout_option', 'ask_tag_number', 'tipo_impresora', 'iface_precompute_cash', 'iface_invoicing']
        dict['m2o'] = [['journal_id', 'account.journal'], ['stock_location_id', 'stock.location'], ['invoice_journal_id', 'account.journal'], ['iface_start_categ_id', 'pos.category']]
        dict['m2m'] = [['journal_ids', 'account.journal'], ['categorias_id', 'product.category']]
        return dict

    def filtro_base_origen(self):
        return [('company_id','=', 1), '|', ('active','=',True), ('active','=',False)]

    def in_crear_pedido(self, conexion, config_id):
        logging.getLogger('config_id').warn(config_id)
        sesion_ids = self.buscar_destino(conexion, 'pos.session', [['config_id', '=', config_id], ['sinc_id', '=', 0], ['state', '=', 'closed']], {'order': 'stop_at asc'})
        logging.getLogger('SESION_IDS ...').warn(sesion_ids)
        res = False
        if sesion_ids:
            for sesion_id in sesion_ids:
                logging.getLogger('SESION_ID...').warn(sesion_id)
                sesion_destino = self.leer_destino(conexion, 'pos.session', [sesion_id], {'fields': ['name','config_id','id','start_at']})[0]
                pos_config_destino = self.leer_destino(conexion, 'pos.config', [sesion_destino['config_id'][0]])
                pos_config_origen = self.env['pos.config'].search([('id', '=', pos_config_destino[0]['sinc_id'])])[0]
                sesion_origen_id = self.env['pos.session'].create({'name': sesion_destino['name'], 'config_id': pos_config_origen.id})
                sesion_origen_id.write({'name': sesion_destino['name']})
                sesion_origen_id.action_pos_session_open()

                ordenes_destino_ids = self.buscar_destino(conexion, 'pos.order', [['session_id', '=', sesion_destino['id']]], {'order': 'id asc'})
                lineas_destino_ids = self.buscar_destino(conexion, 'pos.order.line', [['order_id', 'in', ordenes_destino_ids]])
                if ordenes_destino_ids and ordenes_destino_ids != []:
                    lineas_pedido = {}
                    for linea in self.leer_destino(conexion, 'pos.order.line', [lineas_destino_ids]):
                        producto_destino = self.leer_destino(conexion, 'product.product', [linea['product_id'][0]])[0]
                        producto_origen = self.env['product.product'].search([('id', '=', producto_destino['sinc_id']), '|', ('active','=',True), ('active','=',False)])
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

                    for pedido in self.leer_destino(conexion, 'pos.order', [ordenes_destino_ids]):
                        if pedido['invoice_id']:
                            factura = self.leer_destino(conexion, 'account.invoice', [pedido['invoice_id'][0]])
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

                    logging.getLogger('ordenes_destino_ids... ').warn(ordenes_destino_ids)
                    pagos_destino_ids = self.buscar_destino(conexion, 'account.bank.statement.line', [['pos_statement_id', 'in', ordenes_destino_ids]])
                    pagos = {}
                    if pagos_destino_ids:
                        for pago in self.leer_destino(conexion, 'account.bank.statement.line', [pagos_destino_ids]):
                            diario_destino = self.leer_destino(conexion, 'account.journal', [pago['journal_id'][0]])[0]
                            if diario_destino['code'] not in pagos:
                                pagos[diario_destino['code']] = pago['amount']
                            else:
                                pagos[diario_destino['code']] += pago['amount']
                    restante = obj.amount_total
                    for journal_code in pagos:
                        diario_origen = self.env['account.journal'].search([('code', '=', journal_code)])
                        obj.add_payment({'journal': diario_origen.id ,'amount': pagos[journal_code]})
                        restante -= pagos[journal_code]
                        
                    if restante > 0.009:
                        obj.add_payment({'journal': 119 ,'amount': restante})

                    logging.warn('action_pos_order_paid')
                    obj.action_pos_order_paid()
                    logging.warn('action_pos_order_invoice')
                    obj.action_pos_order_invoice()

                    factura_origen = obj.invoice_id
                    factura_origen.write({'name': nombre_primera_factura + ' - ' + nombre_ultima_factura, 'date_invoice': sesion_destino['start_at']})

                    logging.warn('action_invoice_open')
                    obj.invoice_id.sudo().action_invoice_open()
                    obj.account_move = obj.invoice_id.move_id                

                logging.warn('action_pos_session_closing_control')
                sesion_origen_id.action_pos_session_closing_control()
                logging.warn('action_pos_session_close')
                sesion_origen_id.action_pos_session_close()
                self.modificar_destino(conexion, 'pos.session', sesion_destino['id'], {'sinc_id': sesion_origen_id.id})
                res = True
        return res

        
class Sinc_PDV_Usuarios(models.Model):
    _name = 'sinc_pdv.res.users'
    _inherit = 'sinc_pdv.base'

    def res_model(self):
        return 'res.users'

    def campos(self):
        dict = {}
        dict['estandar'] = ['active', 'name', 'login', 'tz', 'notify_email', 'signature', 'barcode', 'pos_security_pin', 'password_crypt']
        dict['m2o'] = [['default_pos_id', 'pos.config'], ['default_location_id', 'stock.location']]
        return dict

    def filtro_base_origen(self):
        return [('company_id', '=', 1), ('default_pos_id', '!=', False), '|', ('active','=',True), ('active','=',False)]


class Sinc_PDV_Productos(models.Model):
    _name = 'sinc_pdv.product.product'
    _inherit = 'sinc_pdv.base'

    def res_model(self):
        return 'product.product'

    def campos(self):
        dict = {}
        dict['estandar'] = ['active', 'name', 'sale_ok', 'purchase_ok', 'type', 'default_code', 'barcode', 'lst_price', 'standard_price', 'sale_delay', 'produce_delay', 'available_in_pos', 'to_weight', 'description_sale', 'description_purchase', 'description_picking']
        dict['m2o'] = [['categ_id', 'product.category'], ['pos_categ_id', 'pos.category']]
        dict['m2m'] = [['taxes_id', 'account.tax'], ['supplier_taxes_id', 'account.tax']]
        return dict

    def filtro_base_origen(self):
        return [('company_id', '=', 1), '|', ('active','=',True), ('active','=',False)]

    def transferir(self, conexion, producto_origen):
        status_transferir = super(Sinc_PDV_Productos, self).transferir(conexion, producto_origen)
        if status_transferir['funcion'] == 'crear':
            self.out_relacionar_product_template(conexion, producto_origen, status_transferir['obj_id'])
        return status_transferir

    def out_relacionar_product_template(self, conexion, product_origen, producto_destino_id):
        producto_destino = self.leer_destino(conexion, self.res_model(), [producto_destino_id])[0]
        product_template_destino_id = producto_destino['product_tmpl_id'][0]
        
        sinc_productos_tmpl_obj = self.env[self.modelo_relacionado('product.template')]
        sinc_productos_tmpl_obj.modificar_destino(conexion, sinc_productos_tmpl_obj.res_model(), product_template_destino_id, {'sinc_id': product_origen.product_tmpl_id.id})


class Sinc_PDV_ProductosTemplate(models.Model):
    _name = 'sinc_pdv.product.template'
    _inherit = 'sinc_pdv.base'

    def res_model(self):
        return 'product.template'

    def campos(self):
        dict = {}
        dict['estandar'] = ['active', 'name', 'default_code', 'image:image_small']
        dict['m2m'] = [['extras_id', 'pos_gt.extra']]
        return dict

    def filtro_base_origen(self):
        return [('company_id', '=', 1), '|', ('active','=',True), ('active','=',False)]


class Sinc_PDV_Impuestos(models.Model):
    _name = 'sinc_pdv.account.tax'
    _inherit = 'sinc_pdv.base'

    def campos(self):
        dict = {}
        return dict

    def res_model(self):
        return 'account.tax'

    def llaves(self):
        return ['name', 'name']


class Sinc_PDV_Pos_Gt_Extra(models.Model):
    _name = 'sinc_pdv.pos_gt.extra'
    _inherit = 'sinc_pdv.base'

    def res_model(self):
        return 'pos_gt.extra'

    def campos(self):
        dict = {}
        dict['estandar'] = ['name', 'type']
        dict['o2m'] = [['products_id', 'pos_gt.extra.line', {'estandar': ['name', 'qty', 'price_extra'], 'm2o': [['product_id', 'product.product']]}]]
        return dict

    def filtro_base_origen(self):
        return [('company_id', '=', 1)]


class Sinc_PDV_Lista_De_Materiales(models.Model):
    _name = 'sinc_pdv.mrp.bom'
    _inherit = 'sinc_pdv.base'

    def res_model(self):
        return 'mrp.bom'

    def campos(self):
        dict = {}
        dict['estandar'] = ['active', 'code', 'product_qty', 'type']
        dict['m2o'] = [['product_tmpl_id', 'product.template']]
        dict['o2m'] = [['bom_line_ids', 'mrp.bom.line', {'estandar': ['product_qty'], 'm2o': [['product_id', 'product.product']]}]]
        return dict

    def filtro_base_origen(self):
        return [('company_id', '=', 1), '|', ('active','=',True), ('active','=',False)]

class Sinc_PDV_Inventario(models.Model):
    _name = 'sinc_pdv.stock.inventory'
    _inherit = 'sinc_pdv.base'

    def res_model(self):
        return 'stock.inventory'

    def campos(self):
        return {}

    def filtro_base_origen(self):
        return [('company_id', '=', 1)]

    def _out_ajuste_inicial(self, db, uid, password, models):
        self._cr.execute("""\
            SELECT location_id, product_id, SUM(qty) as product_qty
            FROM stock_quant
            WHERE location_id IN (SELECT DISTINCT id FROM stock_location WHERE usage='internal')
            GROUP BY location_id, product_id
            """)
        ubicaciones = {}
        for location_id, product_id, product_qty in self._cr.fetchall():
        
            ubicacion_bd_origen = self.env['stock.location'].browse(location_id)
            producto_bd_origen = self.env['product.product'].browse(product_id)
            ubicacion_bd_destino_id = self.buscar_destino(db, uid, password, models, 'stock.location', ['sinc_id', '=', ubicacion_bd_origen.id])
            producto_bd_destino_id = self.buscar_destino(db, uid, password, models, 'product.product', ['sinc_id', '=', producto_bd_origen.id])

            if ubicacion_bd_destino_id and producto_bd_destino_id:
                ubicacion_bd_destino_id = ubicacion_bd_destino_id[0]
                producto_bd_destino_id = producto_bd_destino_id[0]
                if location_id not in ubicaciones:
                    dict = {}
                    dict['name'] = 'Ajuste inicial - ' + ubicacion_bd_origen.name
                    dict['location_id'] = ubicacion_bd_destino_id
                    
                    line_ids = []
                    line_ids.append((0, 0, {
                        'location_id': ubicacion_bd_destino_id,
                        'product_id': producto_bd_destino_id,
                        'product_qty': product_qty,
                    }))
                    dict['line_ids'] = line_ids

                    obj_id = models.execute_kw(db, uid, password, 'stock.inventory', 'create', [dict])
                    ubicaciones[location_id] = obj_id
                else:
                    obj_id = ubicaciones[location_id]
                    
                    line_ids = []
                    line_ids.append((0, 0, {
                        'location_id': ubicacion_bd_destino_id,
                        'product_id': producto_bd_destino_id,
                        'product_qty': product_qty,
                    }))
                    dict['line_ids'] = line_ids

                    models.execute_kw(db, uid, password, 'stock.inventory', 'write', [[obj_id], dict])

    def in_ajuste_inventario(self, conexion, config_id):
        res = False
        ultima_sesion_destino_id = self.buscar_destino(conexion, 'pos.session', [['config_id', '=', config_id], ['sinc_id', '!=', 0], ['state', '=', 'closed']], {'order': 'stop_at desc', 'limit': 1})
        if ultima_sesion_destino_id:
            ultima_sesion_destino = self.leer_destino(conexion, 'pos.session', [ultima_sesion_destino_id])[0]
            
            config_destino = self.leer_destino(conexion, 'pos.config', [config_id])[0]
            config_origen = self.env['pos.config'].search([('id', '=', config_destino['sinc_id'])])
            analytic_account_id = config_origen.analytic_account_id.id
            ubicacion_origen_id = config_origen.stock_location_id.id
            ubicacion_destino_id = config_destino['stock_location_id'][0]

            inventario_destino_id = self.buscar_destino(conexion, 'stock.inventory', [['name', 'not like', 'Ajuste inicial'],['sinc_id', '=', 0],['state', '=', 'done'],['location_id', '=', ubicacion_destino_id],['date', '>', ultima_sesion_destino['stop_at']]], {'order': 'date desc', 'limit': 1})
            if inventario_destino_id:
                inventario_destino = self.leer_destino(conexion, 'stock.inventory', [inventario_destino_id])[0]
                if inventario_destino['sinc_id'] == 0:

                    sinc_ubicaciones_obj = self.env['sinc_pdv.stock.location']

                    ubicacion_destino = self.leer_destino(conexion, sinc_ubicaciones_obj.res_model(), [inventario_destino['location_id'][0]])
                    ubicacion_origen = self.env[sinc_ubicaciones_obj.res_model()].search([('id', '=', ubicacion_destino[0]['sinc_id'])])[0]
                    dict = {}
                    dict['name'] = inventario_destino['name']
                    dict['date'] = inventario_destino['date']
                    dict['accounting_date'] = parser.parse(inventario_destino['date']) - datetime.timedelta(hours=6)
                    dict['location_id'] = ubicacion_origen.id
                    dict['filter'] = 'partial'
                    dict['cuenta_analitica_id'] = analytic_account_id
                    line_ids = []
                    for linea in self.leer_destino(conexion, 'stock.inventory.line', [inventario_destino['line_ids']]):
                        producto_destino = self.leer_destino(conexion, 'product.product', [linea['product_id'][0]])
                        producto_origen = self.env['product.product'].search([('id', '=', producto_destino[0]['sinc_id']), '|', ('active','=',True), ('active','=',False)])[0]

                        line_ids.append((0, 0, {
                            'location_id': ubicacion_origen.id,
                            'product_id': producto_origen.id,
                            'product_qty': linea['product_qty'] if linea['product_qty'] >= 0 else 0,
                        }))
                        dict['line_ids'] = line_ids

                    obj = self.env['stock.inventory'].create(dict)
                    obj.write({'date': inventario_destino['date']})
                    logging.warn('action_start')
                    obj.action_start()
                    logging.warn('action_done')
                    obj.action_done()
                    self.modificar_destino(conexion, 'stock.inventory', inventario_destino['id'], {'sinc_id': obj.id})
                    res = True
        return res

