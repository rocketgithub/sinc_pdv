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

# La clase Sinc_Base contiene funciones comunes de otros objetos. Para no repetir funciones en cada objeto, se definen en esta clase,
# y se hereda de sinc_pdv.base en cada uno de los otros objetos que necesitan de estas funciones.
# Para cada objeto que se va a transferir del servidor origen al servidor destino, se ha definido una clase en este modulo.
# Ejemplo:
# stock.location -> sinc_pdv.stock.location
# Cada una de estas nuevas clases tiene funciones propias, y funciones heredadas de sinc_pdv.base.
class Sinc_Base(models.Model):
    _name = 'sinc_pdv.base'

    def modelo_relacionado(self, res_model):
        return 'sinc_pdv.' + res_model


    # La funcion leer_destino lee uno o varios registros del servidor destino.
    # res_model: modelo del cual se va a leer el registros.
    # ids: lista con ids a leer del modelo.
    def leer_destino(self, conexion, res_model, ids, extras = {}):
        registros = conexion['models'].execute_kw(conexion['database'], conexion['uid'], conexion['password'], res_model, 'read', ids, extras)
        if registros:
            return registros
        else:
            return False

    # La funcion crear_destino crea un registros del servidor destino.
    # res_model: modelo del cual se va a crear el registro.
    # datos: datos para crear el registro.
    def crear_destino(self, conexion, res_model, datos):
        obj_id = conexion['models'].execute_kw(conexion['database'], conexion['uid'], conexion['password'], res_model, 'create', [datos])
        return obj_id

    # La funcion modificar_destino modifica un registros del servidor destino.
    # res_model: modelo del cual se va a modificar el registro.
    # ids: lista con ids a modificar del modelo.
    def modificar_destino(self, conexion, res_model, id, datos):
        conexion['models'].execute_kw(conexion['database'], conexion['uid'], conexion['password'], res_model, 'write', [[id], datos])
        
    # La funcion eliminar_destino elimina uno o varios registros del servidor destino.
    # res_model: modelo del cual se va a leer el registros.
    # ids: lista con ids a eliminar.
    def eliminar_destino(self, conexion, res_model, ids):
        conexion['models'].execute_kw(conexion['database'], conexion['uid'], conexion['password'], res_model, 'unlink', ids)

    # La funcion filtro_buscar_destino devuelve el parametro (filtro) que necesita la funcion sinc_pdv.base.buscar_destino().
    def filtro_buscar_destino(self, conexion, obj):
        filtro = []
        filtro.append([self.llaves()[1], '=', obj[self.llaves()[0]]])
        if 'estandar' in self.campos() and 'active' in self.campos()['estandar']:
           filtro.append(['company_id', '=', 1])
           filtro.append('|')
           filtro.append(['active','=',True])
           filtro.append(['active','=',False])
        return filtro

    # La funcion buscar_destino devuelve un array de ids, como resultado de una busqueda en el servidor destino.
    # res_model: modelo del cual se va a leer el registros.
    # filtro: el filtro que se necesita aplicar al search en la busqueda.
    # extras (opcional): diccionario con variables extras para la busqueda. Ejemplo: {'order': 'date desc', 'limit': 1} 
    @api.multi
    def buscar_destino(self, conexion, res_model, filtro, extras = {}):
        ids = conexion['models'].execute_kw(conexion['database'], conexion['uid'], conexion['password'], res_model, 'search', [filtro], extras)
        if ids:
            return ids
        else:
            return False

    # La funcion eliminar_destino elimina uno o varios registros del servidor destino.
    # res_model: modelo del cual se va a leer el registros.
    # ids: lista con ids a eliminar.
    def ejecutar_funcion_destino(self, conexion, res_model, funcion, id):
        conexion['models'].execute_kw(conexion['database'], conexion['uid'], conexion['password'], res_model, funcion, [[id]])

    # Para crear o modificar un registro en el servidor destino, se necesita pasar como parametro un diccionario con los campos y 
    # valores del registro a crear o modificar. La funcion preparar_diccionario devuelve ese diccionario que se necesita para
    # crear o modificar un registro en el servidor destino.
    # obj: el objeto que se quiere crear o modificar en el servidor destino.
    def preparar_diccionario(self, conexion, obj, campos, registro_modificar ={}):
        dict = {}

        if 'estandar' in campos:
            dict = self.preparar_campos_estandar(conexion, obj, campos)

        if 'm2o' in campos:
            m2o_dict = self.preparar_campos_m2o(conexion, obj, campos)
            for campo in m2o_dict:
                dict[campo] = m2o_dict[campo]

        if 'm2m' in campos:
            m2m_dict = self.preparar_campos_m2m(conexion, obj, campos, registro_modificar)
            for campo in m2m_dict:
                dict[campo] = m2m_dict[campo]

        if 'o2m' in campos:
            o2m_dict = self.preparar_campos_o2m(conexion, obj, campos, registro_modificar)
            for campo in o2m_dict:
                dict[campo] = o2m_dict[campo]

        dict[self.llaves()[1]] = obj[self.llaves()[0]]

        return dict

    def preparar_campos_estandar(self, conexion, obj, campos):
        dict = {}
        if 'estandar' in campos.keys():
            for campo in campos['estandar']:
                if campo.find(':') == -1:
                    dict[campo] = obj[campo]
                else:
                    campo_origen, campo_destino = campo.split(':')
                    dict[campo_origen] = obj[campo_destino]
        return dict

    # En el objeto que se desea copiar o modificar al servidor destino, pueden existir variables tipo One2many.
    # La funcion preparar_campos_m2o devuelve un diccionario con los campos Many2one del objeto que se quiere copiar o modificar al 
    # servidor destino. Esta funcion es utilizada por la funcion sinc_pdv.base.preparar_diccionario()
    # obj: el objeto que se quiere crear o modificar en el servidor destino.
    def preparar_campos_m2o(self, conexion, obj, campos):
        dict = {}
        if 'm2o' in campos.keys():
            for campo in campos['m2o']:
                if obj[campo[0]]:
                    sinc_obj = self.env[self.modelo_relacionado(campo[1])]
                    id = self.buscar_destino(conexion, sinc_obj.res_model(), sinc_obj.filtro_buscar_destino(conexion, obj[campo[0]]))
                    if id:
                        dict[campo[0]] = id[0]
        return dict

    def preparar_campos_o2m(self, conexion, obj, campos, registro_modificar):
        dict = {}
        if 'o2m' in campos.keys():
            for campo in campos['o2m']:
                lineas = []
                if obj[campo[0]]:
                    if registro_modificar != {}:
                        for id in registro_modificar[campo[0]]:
                            lineas.append((2, id, False))

                    for line in obj[campo[0]]:
                        dict_tempo = {}
                        agregar_linea = True
                        for estandar in campo[2]['estandar']:
                            dict_tempo[estandar] = line[estandar]
                            
                        for m2o in campo[2]['m2o']:
                            sinc_obj = self.env[self.modelo_relacionado(m2o[1])]
                            id = self.buscar_destino(conexion, sinc_obj.res_model(), sinc_obj.filtro_buscar_destino(conexion, line[m2o[0]]))
                            if id:
                                dict_tempo[m2o[0]] = id[0]
                            else:
                                agregar_linea = False
                        if agregar_linea:
                            lineas.append((0, 0, dict_tempo))
                    dict[campo[0]] = lineas
        return dict


    def preparar_campos_m2m(self, conexion, obj, campos, registro_modificar):
        dict = {}
        if 'm2m' in campos.keys():
            for campo in campos['m2m']:
                if obj[campo[0]]:
                    sinc_obj = self.env[self.modelo_relacionado(campo[1])]

                    ids = []
                    if registro_modificar != {}:
                        for id in registro_modificar[campo[0]]:
                            ids.append((3, id, False))

                    for line in obj[campo[0]]:
                        id = self.buscar_destino(conexion, sinc_obj.res_model(), sinc_obj.filtro_buscar_destino(conexion, line))
                        if id:
                            ids.append((4, id[0]))
                    dict[campo[0]] = ids
        return dict
    

    # La funcion transferir revisa si el objeto que se quiere trasladar al servidor destino ya existe en el destino.
    # Si no existe, copia el objeto al servidor destino. Si existe, modifica el objeto en el servidor destino.
    # obj: el objeto que se quiere crear o modificar en el servidor destino.
    @api.multi
    def transferir(self, conexion, obj):
        status = {}
        obj_id = self.buscar_destino(conexion, self.res_model(), self.filtro_buscar_destino(conexion, obj))
        if not obj_id:
            logging.warn('CREAR')
            obj_dict = self.preparar_diccionario(conexion, obj, self.campos())
            nuevo_obj_destino_id = self.crear_destino(conexion, self.res_model(), obj_dict)
            status['funcion'] = 'crear'
            status['obj_id'] = nuevo_obj_destino_id
        else:
            logging.warn('MODIFICAR')
            obj_destino_id = obj_id[0]
            registro_modificar = {}
            if 'o2m' in self.campos().keys() or 'm2m' in self.campos().keys():
                registro_modificar = self.leer_destino(conexion, self.res_model(), [obj_destino_id])[0]

            obj_dict = self.preparar_diccionario(conexion, obj, self.campos(), registro_modificar)
            self.modificar_destino(conexion, self.res_model(), obj_destino_id, obj_dict)
            status['funcion'] = 'modificar'
            status['obj_id'] = obj_destino_id
        return status

    # La funcion llaves() devuelve los campos que van a ser utilizados como llave para sincronizar objetos entre el origen y destino.
    # La funcion retorna una lista. En la posicion 0 retorna la llave del origen, y en la posicion 1 retorna la llave del destino.
    def llaves(self):
        return ['id', 'sinc_id']

