from pysnmp.hlapi import *

def consultaSNMP(comunidad, host, oid, var = False):
    errorIndication, errorStatus, errorIndex, varBinds = next(
        getCmd(SnmpEngine(),
               CommunityData(comunidad),
               UdpTransportTarget((host, 161)),
               ContextData(),
               ObjectType(ObjectIdentity(oid))))

    if errorIndication:
        resultado = errorIndication
    elif errorStatus:
        print('%s at %s' % (errorStatus.prettyPrint(),
                            errorIndex and varBinds[int(errorIndex) - 1][0] or '?'))
    else:
        for varBind in varBinds:
            varB = (' = '.join([x.prettyPrint() for x in varBind]))
            if(var):
                resultado = varB
            else:
                resultado = varB.split()[2]
    return resultado

def consultaSNMPWalk(comunidad, host, oid, entidad = "", ES_UN_DISCO = False):
    resultado = []
    for (errorIndication, 
         errorStatus, 
         errorIndex,
         varBinds) in nextCmd(SnmpEngine(),
                              CommunityData( comunidad ),
                              UdpTransportTarget((host, 161)),
                              ContextData(),
                              ObjectType(ObjectIdentity(oid)),
                              lexicographicMode=False):
        if errorIndication:
            resultado.append(errorIndication)
        elif errorStatus:
            print('%s at %s' % (errorStatus.prettyPrint(),
                                errorIndex and varBinds[int(errorIndex) - 1][0] or '?'))
        else:
            for varBind in varBinds:
                varB = (' = '.join([x.prettyPrint() for x in varBind]))
                mibRes = varB.split(".")
                res = mibRes[len(mibRes) - 1 ].split(" = ")[0]
                
                if( entidad.lower() == mibRes[len(mibRes) - 1 ].split(" = ")[1].lower() ):
                    return res
                
                if( ES_UN_DISCO ):
                    descripcion = mibRes[len(mibRes) - 1 ].lower().split(" = ")[1]
                    disco = descripcion.split( entidad.lower() )
                    if( len(disco) > 1):
                        return res

                resultado.append( res )
    return resultado
