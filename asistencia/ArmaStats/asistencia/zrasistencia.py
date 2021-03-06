#/usr/bin/env python3
# -*. coding: utf-8 -*-

"""ZRAsistencia es un módulo de ZRStats, su función es leer un archivo RPT y entregar un reporte de asistencia 
que posteriormente será comparado con una base de datos en ZRStats."""


#imports
import re
from collections import defaultdict
import datetime
import os
import sys
# descomentar en caso de web app
#from django.conf import settings

# variables globales
global debug
debug = False

global ruta
if debug:
    ruta = "rutastrix"
else:
    ruta = "data4.rpt"

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
        rpt = re.findall('^.*"ZRASISTENCIA.*$', l, re.M)

        global fecha_rpt
        fecha_rpt = f[5].split(" ")
        fecha_rpt = fecha_rpt[3]

# Error y matar proceso en caso de que no existan resultados en el RPT
        if not rpt:
            print("No se encontraron eventos en el archivo RPT,")
            print("probablemente no está presente el EH para registrar asistencia.")
            print("Procure instalar el archivo initServer que proveemos en nuestro repo.")
            os.system("pause")
            sys.exit()

# Comienza el parseo de data        
        for element in rpt:
            rpt = element.split(" ")
            
            if rpt[1]=="":
                rpt.pop(1)

            rpt[0] = rpt[0].replace(",", "")
            rpt.pop(2)

            t = rpt[1].split(":")
            hora = int(t[0])
            minuto = t[1]
            segundo = t[2]

# Esta parte hardcodea la hora de Miami, quizás considerar una forma de automatizar diferentes horarios?
            hora = hora + 4
            if hora >= 24:
                hora = abs(24- hora)
                fecha = rpt[0].split("/")
                year = fecha[0]
                month = fecha[1]
                day = int(fecha[2])
                day = day + 1
                fecha = str(year)+"/"+str(month)+"/"+str(day)
                rpt[0] = fecha

            nt =str(hora) + ":" + minuto + ":" + segundo
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
    
    return sessions

def calculo_tiempo(data_total):
    """Lee en todas las sesiones de juego que registra el RPT y suma el tiempo total de juego, luego lo compara con el tiempo que debería haber estado activo y 
    revela si su asistencia es válida o no, además de haber atraso lo acusa al final.

Retorna un diccionario de formato tt = {jugador: [rango, asistencia, requiere atencion, tiempo de sesion]}"""

    tt = {}
    
    for x, y in data_total.items():
        eventos = int(len(y))
        contador = 0
        total_time = datetime.timedelta(hours=0, minutes=0, seconds=0)

        hora_ingreso = y[0][1]
        hora_ingreso = hora_ingreso.split(":")
        segundo_ingreso = int(hora_ingreso[2])
        minuto_ingreso  = int(hora_ingreso[1])
        hora_ingreso    = int(hora_ingreso[0])

        hora_ingreso = datetime.timedelta(hours=hora_ingreso, minutes= minuto_ingreso, seconds= segundo_ingreso)
        if hora_ingreso > datetime.timedelta(hours=21, minutes=15, seconds=0):
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
                print("ERROR: No encontré desconexión de " + x + ".\n¿Seguirá conectado?\n")
            try:
                in_time = datetime.datetime(year_in, month_in, day_in, hour_in, minute_in, second_in)
                out_time = datetime.datetime(year_out, month_out, day_out, hour_out, minute_out, second_out)

                duration_time = abs(out_time - in_time)
                total_time = duration_time + total_time
            except:
                pass
            contador +=2

        tiempo_asistencia = datetime.timedelta(hours=1, minutes=20)
        tiempo_minimo     = datetime.timedelta(minutes=30)
        requiere_atencion = "False"

        if total_time >= tiempo_asistencia:
            asistencia = "asiste"
            if atrasado:
                asistencia = "atrasado"
        elif total_time <= tiempo_asistencia and total_time > tiempo_minimo:
            requiere_atencion = "true"
        else:
            asistencia = "falta"
            requiere_atencion = "true"
        
        nombre = x.split(".")
        rango = nombre[0]
        nombre = nombre.pop(1)

        tt.setdefault(nombre, []).append(rango)
        tt.setdefault(nombre, []).append(asistencia)
        tt.setdefault(nombre, []).append(requiere_atencion)
        tt.setdefault(nombre, []).append("tiempo de sesión: "+ str(total_time))
            
    return tt

def main():
    """Launcher."""
    rptdata    = leer_rpt(ruta)
    resultado_asistencia = calculo_tiempo(rptdata)
    print (fecha_rpt)
    print(resultado_asistencia)

if __name__ == "__main__":
    main()