import dns.resolver
import rrdtool
from ftplib import FTP
from datetime import timedelta
import  datetime
import sys
import os
import time
import threading
from pyftpdlib.authorizers import DummyAuthorizer
from pyftpdlib.handlers import FTPHandler
from pyftpdlib.servers import FTPServer
from getSNMP import consultaSNMP
from getSNMP import consultaSNMPWalk
import httplib2
import paramiko
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter

comunidadSNMP = "comunidadSNMP"
hostSNMP = "192.168.100.10"

def MonitorearRendimientoAgente(ip, comunidad):
    RAMLoad = StorageLoad = 0.0
    numeroRam = numeroAlamacenamiento = CPULoads = ''
    CPUs= []
    RRA = []
    DS = []

    while(True):
        estadoDelAgente = str(consultaSNMP( comunidad, ip, '1.3.6.1.2.1.1.1.0'))

        if( estadoDelAgente.split( )[0] != "No" ):
            if(len(DS) == 0 and len(RRA) == 0):
                CPUs =  consultaSNMPWalk(comunidad, ip, '1.3.6.1.2.1.25.3.3.1.2')
                DS.append("DS:RAM:GAUGE:600:U:U")
                RRA.append("RRA:AVERAGE:0.5:1:60")
                DS.append("DS:Storage:GAUGE:600:U:U")
                RRA.append("RRA:AVERAGE:0.5:1:60")
                for cpu in CPUs:
                    DS.append("DS:CPU" + cpu +":GAUGE:600:U:U")
                    RRA.append("RRA:AVERAGE:0.5:1:60")
                crearRRDsMonitoreo(DS,RRA)

            if( numeroAlamacenamiento == '' ):
                consultaSistemaOperativo = str(consultaSNMP(comunidad, ip, '1.3.6.1.2.1.1.1.0'))

            entidad = "Physical Memory" #Memoria RAM
            if( numeroRam == ''):
                numeroRam = consultaSNMPWalk(comunidad, ip,'1.3.6.1.2.1.25.2.3.1.3', entidad)
            TotalRAM = consultaSNMP(comunidad, ip, '1.3.6.1.2.1.25.2.3.1.5.' + numeroRam)
            UsoRAM = consultaSNMP(comunidad, ip, '1.3.6.1.2.1.25.2.3.1.6.' + numeroRam)
            RAMLoad = str(int(UsoRAM) * 100 / int( TotalRAM ))

            if( numeroAlamacenamiento == ''):
                if (consultaSistemaOperativo == 'Linux'):
                    entidad = "/" #Almacenamiento
                else:
                    entidad = "c:" #Almacenamiento
                numeroAlamacenamiento = consultaSNMPWalk(comunidad, ip,'1.3.6.1.2.1.25.2.3.1.3', entidad, consultaSistemaOperativo != 'Linux')
            TotalStorage = consultaSNMP(comunidad, ip, '1.3.6.1.2.1.25.2.3.1.5.' + numeroAlamacenamiento)
            UsoStorage = consultaSNMP(comunidad, ip, '1.3.6.1.2.1.25.2.3.1.6.' + numeroAlamacenamiento)
            StorageLoad = str(int(UsoStorage) * 100 / int(TotalStorage))

            if(len(CPUs) == 0):
                CPUs =  consultaSNMPWalk(comunidad, ip, '1.3.6.1.2.1.25.3.3.1.2')
            
            CPULoads = ''
            for cpu in CPUs:
                if( cpu != CPUs[len(CPUs) - 1] ):
                    CPULoads += consultaSNMP(comunidad, ip, '1.3.6.1.2.1.25.3.3.1.2.' + cpu)+":"
                else:
                    CPULoads += consultaSNMP(comunidad, ip, '1.3.6.1.2.1.25.3.3.1.2.' + cpu)
            
            valor =  "N:" + RAMLoad + ':' + StorageLoad + ':' + CPULoads            
            rrdtool.update("RRDsAgentes/monitoreo.rrd", valor)
            rrdtool.dump('RRDsAgentes/monitoreo.rrd', 'RRDsAgentes/monitoreo.xml')
            time.sleep(1)

def crearRRDsMonitoreo(DS,RRA):
    print("Creando rrds")
    ret = rrdtool.create("RRDsAgentes/monitoreo.rrd",
                        "--start",'N',
                        "--step",'3',
                        DS,
                        RRA)
    rrdtool.dump( 'RRDsAgentes/monitoreo.rrd', 'RRDsAgentes/monitoreo.xml' )

    if ret:
        print ( rrdtool.error() )

def Graficar(nombre, titulo, label, dato):
    ultimo=rrdtool.last( "RRDsAgentes/monitoreo.rrd" )        
    tiempo_inicial = ultimo
    ret2 = rrdtool.graphv( "Graficas/" + nombre + ".png",
                    "--start",str(tiempo_inicial - 180),
                    "--title",titulo,
                    "--vertical-label=" + label,
                    '--lower-limit', '0',
                    '--upper-limit', '100',
                    "DEF:carga=RRDsAgentes/monitoreo.rrd:" + dato +":AVERAGE",
                    "VDEF:cargaMAX=carga,MAXIMUM",
                    "VDEF:cargaMIN=carga,MINIMUM",
                    "VDEF:cargaLAST=carga,LAST",
                    "AREA:carga#00FF00:Carga del CPU",
                    "GPRINT:cargaMIN:%6.2lf %SMIN",
                    "GPRINT:cargaMAX:%6.2lf %SMAX",
                    "GPRINT:cargaLAST:%6.2lf %SACTUAL"
        )

def ServidorFTP(host, port):
    authorizer = DummyAuthorizer()
    authorizer.add_user("user", "12345", "/archivos/ftps", perm="elradfmw")
    authorizer.add_anonymous("/archivos/ftps", perm="elradfmw")

    handler = FTPHandler
    handler.authorizer = authorizer

    server = FTPServer((host, port), handler)
    server.serve_forever()

def SensorSSH(host, puerto, usernameSSH, passwordSSH):
    inicio = int(round(time.time() * 1000))
    try:
        datos=dict( hostname = host, port = puerto, username = usernameSSH, password = passwordSSH)
        ssh_client=paramiko.SSHClient()
        ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh_client.connect(**datos)
        response = ssh_client.exec_command('ls')
        NumeroConexiones = str( response[0] ).split(";")[1].split(" ")[1]
        EstadoServidorSsh = "Up"
        TraficoRecibido = consultaSNMP( comunidadSNMP , hostSNMP, '1.3.6.1.2.1.2.2.1.10.1')
        TraficoEnviado = consultaSNMP( comunidadSNMP , hostSNMP,'1.3.6.1.2.1.2.2.1.16.1')
    except:
        EstadoServidorSsh = "Down"
        NumeroConexiones = "0"
        TraficoRecibido = "0"
        TraficoEnviado = "0"
    tiempo = ( int(round(time.time() * 1000)) - inicio)
    if( tiempo > 1000):
        total = str( tiempo / 1000) + "s"
    else:
        total = str( tiempo ) + "ms"
    return EstadoServidorSsh, NumeroConexiones, TraficoEnviado, TraficoRecibido, total

#thread_read = threading.Thread(target = ServidorFTP, args=["127.0.0.1", 8080,])
#thread_read.start()
thread_read = threading.Thread(target = MonitorearRendimientoAgente, args=[hostSNMP, comunidadSNMP,])
thread_read.start()
time.sleep(4)

#os.system("clear")

def SensorHTTP(host, puerto):
    inicio = int(round(time.time() * 1000))
    try:
        conn = httplib2.Http("")        
        (resp_headers, content) = conn.request("http://" + host + ":" + puerto , "GET")
        EstadoServidorHTTP = "Up"
        BytesRecibidos = str( resp_headers[ 'content-length' ] )
        AnchoBanda = consultaSNMP( comunidadSNMP, hostSNMP, '1.3.6.1.2.1.2.2.1.5.1')
        # print('response status: %s' % resp_headers.status)
    except :        
        EstadoServidorHTTP = "Down"
        BytesRecibidos = "0"
        AnchoBanda = "0"
    tiempo = ( int(round(time.time() * 1000)) - inicio)
    if( tiempo > 1000):
        total = str( tiempo / 1000) + "s"
    else:
        total = str( tiempo ) + "ms"        
    return EstadoServidorHTTP, BytesRecibidos, AnchoBanda, total

def SensorFTP(host,port):
    inicio = int(round(time.time() * 1000))
    try:
        ftp = FTP('')
        ftp.connect(host, port)
        ftp.login()
        files = ftp.nlst()
        descargas=""
        for j in range(len(files)):        
            fhandle = open(files[j], 'wb')
            ftp.retrbinary('RETR ' + files[j], fhandle.write)
            fhandle.close()
            descargas = descargas + files[j] + ", "
        EstadoServidorFtp = "Up"
        RespuestaFTP = descargas
    except:
        EstadoServidorFtp = "Down"
        RespuestaFTP = "--"
    tiempo = ( int(round(time.time() * 1000)) - inicio)
    if( tiempo > 1000):
        total = str( tiempo / 1000) + "s"
    else:
        total = str( tiempo ) + "ms"
    return EstadoServidorFtp, RespuestaFTP, total

def SensorDNS(dominio):
    inicio = int(round(time.time() * 1000))
    try:
        name = dominio
        for qtype in 'A', 'AAAA', 'MX', 'NS', 'TXT', 'SOA':
            answer = dns.resolver.query(name,qtype, raise_on_no_answer=False)
            if answer.rrset is not None:            
                continue #print(answer.rrset)
        EstadoServidorDNS = "Up"
    except:
        EstadoServidorDNS = "Down"    

    tiempo = ( int(round(time.time() * 1000)) - inicio)
    if( tiempo > 1000):
        total = str( tiempo / 1000) + "s"
    else:
        total = str( tiempo ) + "ms"
    return EstadoServidorDNS, total

def MonitorearServidores(generarReporte = False):
    if( generarReporte):
        print("Monitoreando FTP ...")
    EstadoServidorFTP, RespuestaFTP, TiempoFTP = SensorFTP("192.168.100.10",8080)
    #print(EstadoServidorFTP)
    
    if( generarReporte):
        print("Monitoreando SSH ...")
    EstadoServidorSSH, NumeroConexiones, TraficoEnviado, TraficoRecibido, TiempoSSH = SensorSSH("192.168.100.10", "22", "aldom7673", "aldom7673")
    #print(EstadoServidorSSH)

    if( generarReporte):
        print("Monitoreando HTTP ...")
    EstadoServidorHTTP, BytesRecibidos, AnchoBanda, TiempoHTTP = SensorHTTP("192.168.100.10","80")
    #print(EstadoServidorHTTP)

    dominio = 'ns1.midominio.com'
    if( generarReporte):
        print("Monitoreando DNS ...")
    EstadoServidorDNS, TiempoDNS = SensorDNS( dominio)
    #print(EstadoServidorDNS)
    
    if( generarReporte):
        print("Monitoreo terminado")
    
    if( generarReporte):
        print("Generando reporte ...")
        nombreArchivo = "ReporteRendimiento"
        documento = canvas.Canvas("Reportes/" + nombreArchivo + ".pdf")

        consultaSistemaOperativo = str(consultaSNMP(comunidadSNMP, hostSNMP, '1.3.6.1.2.1.1.1.0'))
        if (consultaSistemaOperativo == 'Linux'):
            sistemaOperativo = "Linux"
        else:
            sistemaOperativo = "Windows"

        ultimoInicio = str(consultaSNMP(comunidadSNMP, hostSNMP, '1.3.6.1.2.1.1.3.0'))
        if(not ultimoInicio.isdigit()):
            ultimoInicio = "0"
        tiempoInicio = timedelta(seconds = int( int(ultimoInicio)/100 ) )

        numeroDePuertos = str(consultaSNMP(comunidadSNMP, hostSNMP, '1.3.6.1.2.1.2.1.0'))

        encabezado = documento.beginText(40, 800) 
        encabezado.textLine( "Equipo: Peers                                                                           " + "Fecha de elaboración: " + str(datetime.datetime.now()).split(" ")[0] )
        encabezado.textLine( "")
        encabezado.textLine( "Autores: Ámbar Desire Martell Fuentes" )
        encabezado.textLine( "              Aldo Daniel Mendoza Morales" )
        encabezado.textLine( "")
        encabezado.textLine( "Nombre del Sistema Operativo " + sistemaOperativo )
        encabezado.textLine( "Tiempo de actividad: "  + str(tiempoInicio))
        encabezado.textLine( "Numero de interfaces: "  + numeroDePuertos)
        documento.drawImage("SistemasOperativos/logo" + sistemaOperativo + ".png", 400, 690, 100, 100)
        documento.drawText( encabezado )

        Graficar("cargaCPU", "Carga de CPU", "Carga", "CPU196608")
        Graficar("discoDuro", "Uso de disco duro", "Uso", "Storage")
        Graficar("memoriaRAM", "Uso de memoria RAM", "Memoria", "RAM")
    
        texto = documento.beginText(40, 680)
        texto.textLine( "Grafica 1. Informacion grafica del CPU ")
        documento.drawText(texto)
        documento.drawImage("Graficas/cargaCPU.png", 40, 500)

        texto = documento.beginText(40, 480)
        texto.textLine( "")
        texto.textLine( "Grafica 2. Informacion grafica de uso de memoria RAM")
        documento.drawText(texto)
        documento.drawImage("Graficas/memoriaRAM.png", 40, 290)

        texto = documento.beginText(40, 280)
        texto.textLine( "")
        texto.textLine( "Grafica 3. Informacion grafica de uso de disco duro")
        documento.drawText(texto)
        documento.drawImage("Graficas/discoDuro.png", 40, 90)
        
        documento.showPage()

        TServidorFTP = documento.beginText(40, 800)
        TServidorFTP.textLine( "" )
        TServidorFTP.textLine( "Supervisión FTP" )
        TServidorFTP.textLine( "" )
        TServidorFTP.textLine( "Estado del servidor: " +  EstadoServidorFTP  )
        TServidorFTP.textLine( "Respuesta del servidor: " +  RespuestaFTP   )
        TServidorFTP.textLine( "Tiempo de respuesta del servidor: " +  TiempoFTP )
        documento.drawText(TServidorFTP)

        TServidorHTTP = documento.beginText(40, 715)
        TServidorHTTP.textLine( "" )
        TServidorHTTP.textLine( "Supervisión HTTP" )
        TServidorHTTP.textLine( "" )
        TServidorHTTP.textLine( "Estado del servidor: " + EstadoServidorHTTP )
        TServidorHTTP.textLine( "Bytes recibidos: " +  BytesRecibidos )
        TServidorHTTP.textLine( "Ancho de banda: " +  AnchoBanda )
        TServidorHTTP.textLine( "Tiempo de respuesta del servidor: " +  TiempoHTTP )
        documento.drawText(TServidorHTTP)

        TServidorDNS = documento.beginText(40, 615)
        TServidorDNS.textLine( "" )
        TServidorDNS.textLine( "Supervisión DNS" )
        TServidorDNS.textLine( "" )
        TServidorDNS.textLine( "Dominio: " +  dominio  )
        TServidorDNS.textLine( "Estado del servidor: " +  EstadoServidorDNS  )
        TServidorDNS.textLine( "Tiempo de respuesta del servidor: " +  TiempoDNS )
        documento.drawText(TServidorDNS)

        TServidorSSH = documento.beginText(40, 525)
        TServidorSSH.textLine( "" )
        TServidorSSH.textLine( "Supervisión de acceso remoto (SSH)" )
        TServidorSSH.textLine( "" )
        TServidorSSH.textLine( "Estado del servidor: " +  EstadoServidorSSH )
        TServidorSSH.textLine( "Trafico enviado: " +  TraficoEnviado )
        TServidorSSH.textLine( "Trafico recibido: " +  TraficoRecibido )
        TServidorSSH.textLine( "Numero de conexiones: " +  NumeroConexiones )
        TServidorSSH.textLine( "Tiempo de respuesta del servidor: " +  TiempoSSH )
        documento.drawText(TServidorSSH)
        documento.save()

        print("Reporte generado")

while(True):
    os.system("clear")
    print("Administracion de rendimiento")
    print("1. Generar reporte de rendimiento")
    print("2. Generar reporte de rendimiento con simulacion de varias conexiones")
    print("3. Salir")

    opcion = input("Opcion: ")
    if( opcion == "1"):
        MonitorearServidores(True)
    elif( opcion == "2"):
        print("Trabando en ello ..")
        hilos = []
        for i in range(0,10):
            hilos.append(threading.Thread(target = MonitorearServidores, args=[False,]))
            hilos[i].start()
        MonitorearServidores(True)  
    elif( opcion == "3"):
        exit(0)
    else: 
        input("Opcion no valida, pulsa enter para continuar")
    
    