from pysnmp.hlapi import *
from getSNMP import consultaSNMP
from getSNMP import consultaSNMPWalk
import time

host = "127.0.0.1"
version = "1"
comunidad = "comunidadSNMP"
puerto = 161

# hrProcessorLoad	 = "1.3.6.1.2.1.25.3.3.1.2"
# Ejecutar res = consultaSNMPWalk() y ejecutar hrProcessorLoad + res[i] 
# para obtener la carga de cada procesador

# CPUs =  consultaSNMPWalk(comunidad,host,'1.3.6.1.2.1.25.3.3.1.2')
# while(True):
#     for cpu in CPUs:
#         print( cpu + ":  " + consultaSNMP(comunidad, host, '1.3.6.1.2.1.25.3.3.1.2.' + cpu) )
#     time.sleep(5)

# hrStorageTable = "1.3.6.1.2.1.25.2.3.1"
entidad = "Physical Memory"
# Ejecutar res = consultaSNMPWalk(hrStorageTable + ".3"), entidad) para obtener el numero de la entidad 
# especificada y ejecutar hrStorageTable + ".6" + res para obtener el uso de la RAM

res = consultaSNMPWalk(comunidad,host,'1.3.6.1.2.1.25.2.3.1.3', entidad)
#RAM = consultaSNMP(comunidad, host,'1.3.6.1.2.1.25.2.3.1.3.6.' + res)
while(True):
    print( "RAM :  " + consultaSNMP(comunidad, host,'1.3.6.1.2.1.25.2.3.1.6.' + res) )
    time.sleep(5)

# hrStorageTable = "1.3.6.1.2.1.25.2.3.1.3"
#entidad = "C:" # "/" 
# Ejecutar res = consultaSNMPWalk(..., entidad) para obtener el numero la entidad especificada,
# (si es un disco en Windows, especificarlo enviando al final una bandera en True) y ejecutar
# hrStorageTable + ".5" + res para obtener el uso de disco 
