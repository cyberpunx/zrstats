# /usr/bin/env python3
# -*. coding: utf-8 -*-

"""Lector es un script, componente de ZR_Stats cuyo fin es meramente leer y procesar los archivos rpt generados por Arma 3
y escupir un diccionario con la información de asistencia y estadísticas que capture"""


# imports
import re
from collections import defaultdict
import datetime
import os
import sys
# from django.conf import settings

# globals
fecha_rpt = []
rpt_mision_data = []
# funciones


def leer_rpt(data):
    """Lee y ordena el contenido del archivo RPT.
Retorna un diccionario de formato: {jugador: [[fecha, hora, evento]]}

Nótese que para funcionar correctamente, es necesario un eventhandler que agregre ZRASISTENCIA al RPT.
    """
# Lectura de la palabra clave en el archivo RPT.
    rpt_total = []
    with open(data, 'r') as f:
        s = "\n"
        f = f.readlines()
        l = s.join(f)
        rpt = re.findall('^.*"ZRASISTENCIA.*$', l, re.M) # busca en el rpt todos los eventos de ZRASISTENCIA
        rpt_mision_data = re.findall('^.*"ZRSTATS.*$', l, re.M) # busca en el rpt todos los eventos de ZRSTATS

        global fecha_rpt
        fecha_rpt = f[5].split(" ")
        fecha_rpt = fecha_rpt[3]
        #fecha_rpt = fecha_rpt.replace('/', ':')

# Error y matar proceso en caso de que no existan resultados en el RPT
        if not rpt:
            print("No se encontraron eventos en el archivo RPT,")
            print("probablemente no está presente el EH para registrar stats.")
            print("Procure instalar el archivo initServer que proveemos en nuestro repo.")
            os.system("pause")
            sys.exit()

# Comienza el parseo de data
        for element in rpt:
            rpt = element.split(" ")

            if rpt[1] == "":
                rpt.pop(1)

            rpt[0] = rpt[0].replace(",", "")
            rpt.pop(2)

            t = rpt[1].split(":")
            hora = int(t[0])
            minuto = t[1]
            segundo = t[2]

# Esta parte hardcodea la hora de Miami, quizás considerar una forma de automatizar diferentes horarios?
#TODO asegurarse que la hora no falle, ¿Cambia la hora en Venezuela durante el año?¿Cambia la hora en Miami?
            hora = hora + 4
            if hora >= 24:
                hora = abs(24 - hora)
                fecha = rpt[0].split("/")
                year = fecha[0]
                month = fecha[1]
                day = int(fecha[2])
                day = day + 1
                fecha = str(year)+"/"+str(month)+"/"+str(day)
                rpt[0] = fecha

            nt = str(hora) + ":" + minuto + ":" + segundo
            rpt[1] = nt
            rpt_total.append(rpt)

            if len(rpt) == 5:
                rpt[2] = rpt[2]+rpt[3]
                rpt.pop(3)
# todos los resultados en un diccionario, aún sin calcular.
    sessions = defaultdict(list)
    for event in rpt_total:
        sessions[event[2]].append(event)

    for y in sessions.values():
        eventos = int(len(y))
        contador = 0

        while contador != eventos:
            y[contador].pop(2)
            contador += 1

    # Armo un diccionario con las sesiones y la info de mision
    rpt_dict = {}
    rpt_dict['asistencia'] = sessions

    # Parseo los campos de la info de mision (campos con ZRSTATS)
    mission_data = []
    for campo in rpt_mision_data:
        aux = campo.split("\"", 1)[1]
        aux2 = aux.split(":")[1]
        aux2 = aux2.split("\"", 1)[0]
        mission_data.append(aux2)


    rpt_dict['info_mision'] = mission_data

    return rpt_dict


def calculo_tiempo(data_total):
    """Lee en todas las sesiones de juego que registra el RPT y suma el tiempo total de juego, luego lo compara con el tiempo que debería haber estado activo y 
    revela si su stats es válida o no, además de haber atraso lo acusa al final.

Retorna una lista de diccionarios de formato resultado_reporte = [dic_mision, dic_jugador]
dic_mision  = {'fecha:'%y-%m-%d', 'tipo_mision':'OFICIAL', 'nombre_mision':'nombre', 'campana':'--', 'editor':'editor'}                                                   
dic_jugador = {'nombre':'x', 'rango':'y', 'asistencia':'z', 'tiempo_sesion':'%h:%m:%s', 'requiere_atencion':'bool'}                                                   
"""
    global fecha_rpt

    resultado_reporte = []
    dic_mision = {}

    # Tomando datos de misión desde el reporte
    mision_info = data_total['info_mision']
    dic_mision['fecha'] = fecha_rpt
    # TODO leer esta data desde el reporte/generar data en el reporte con KDM

    for campo in mision_info:
        clave = campo.split()[0]  # extraigo el campo, ej "NOMBRE_CAMPA"
        valor = campo.split(clave, 1)[1]  # extraigo el valor, ej "Regreso Al Infierno"

        if clave == "NOMBRE_MISION":
            dic_mision['NOMBRE_MISION'] = valor

        if clave == "DESC_MISION":
            dic_mision['DESC_MISION'] = valor

        if clave == "AUTOR_MISION":
            dic_mision['AUTOR_MISION'] = valor

        if clave == "TIPO_MISION":
            dic_mision['TIPO_MISION'] = valor

        if clave == "NOMBRE_CAMPA":
            dic_mision['NOMBRE_CAMPA'] = valor

        if clave == "ES_OFICIAL":
            dic_mision['ES_OFICIAL'] = valor

        if clave == "MAPA_MISION":
            dic_mision['MAPA_MISION'] = valor

    resultado_reporte.append(dic_mision)

    data_asistencia = data_total['asistencia']
    for x, y in data_asistencia.items():
        eventos = int(len(y))
        contador = 0
        total_time = datetime.timedelta(hours=0, minutes=0, seconds=0)

        hora_ingreso = y[0][1]
        hora_ingreso = hora_ingreso.split(":")
        segundo_ingreso = int(hora_ingreso[2])
        minuto_ingreso = int(hora_ingreso[1])
        hora_ingreso = int(hora_ingreso[0])

        hora_ingreso = datetime.timedelta(
            hours=hora_ingreso, minutes=minuto_ingreso, seconds=segundo_ingreso)
        if hora_ingreso > datetime.timedelta(hours=21, minutes=15, seconds=0): # HORA INICIO MISION 21hs
            atrasado = True
        else:
            atrasado = False

        while contador != eventos:
            try:
                date_in = y[contador][0].split("/")
                year_in = int(date_in[0])
                month_in = int(date_in[1])
                day_in = int(date_in[2])
                time_in = y[contador][1].split(":")
                hour_in = int(time_in[0])
                minute_in = int(time_in[1])
                second_in = int(time_in[2])
            except IndexError:
                print("ERROR: No encontré conexión de " + x + "\n")
                break
            try:
                date_out = y[contador+1][0].split("/")
                year_out = int(date_out[0])
                month_out = int(date_out[1])
                day_out = int(date_out[2])
                time_out = y[contador+1][1].split(":")
                hour_out = int(time_out[0])
                minute_out = int(time_out[1])
                second_out = int(time_out[2])
            except IndexError:
                print("ERROR: No encontré desconexión de " +
                      x + ".\n¿Seguirá conectado?\n")

                # asumo tiempo total basado en el ingreso y el fin de la mision
                hora_fin_mision = datetime.timedelta(hours=23, minutes=0, seconds=0)
                ingreso = datetime.timedelta(hours=hour_in, minutes=minute_in, seconds=0)
                total_time = hora_fin_mision - ingreso
            try:
                in_time = datetime.datetime(
                    year_in, month_in, day_in, hour_in, minute_in, second_in)
                out_time = datetime.datetime(
                    year_out, month_out, day_out, hour_out, minute_out, second_out)

                duration_time = abs(out_time - in_time)
                total_time = duration_time + total_time
            except:
                pass
            contador += 2

        tiempo_asistencia = datetime.timedelta(hours=1, minutes=20) # TIEMPO MINIMO REQUERIDO PARA ASISTENCIA
        tiempo_minimo = datetime.timedelta(minutes=30)
        requiere_atencion = "False"

        if total_time >= tiempo_asistencia:
            asistencia = "Asiste"
            if atrasado:
                asistencia = "Tarde"
        elif total_time <= tiempo_asistencia and total_time > tiempo_minimo:
            requiere_atencion = "True"
        else:
            asistencia = "Falta"
            requiere_atencion = "True"

        nombre = x.split(".")
        rango = nombre[0]
        nombre = nombre.pop(1)

        dic_jugador = {}
        dic_jugador['nombre'] = nombre
        dic_jugador['rango'] = rango
        dic_jugador['asistencia'] = asistencia
        dic_jugador['tiempo_sesion'] = str(total_time)
        dic_jugador['requiere_atencion'] = requiere_atencion
        resultado_reporte.append(dic_jugador)

    return resultado_reporte


def main(upload):
    """Launcher."""
    rptdata = leer_rpt(upload)
    resultado_asistencia = calculo_tiempo(rptdata)

    return resultado_asistencia


def local_debug():
    archivo_prueba = os.path.dirname(
        os.path.realpath(__file__)) + '\\transformed.rpt'
    rptdata = leer_rpt(archivo_prueba)
    resultado_asistencia = calculo_tiempo(rptdata)

    print(resultado_asistencia)


if __name__ == '__main__':
    local_debug()
