import os
import sys
import random
import collections

if 'SUMO_HOME' in os.environ:
    sys.path.insert(0, os.path.join(os.environ['SUMO_HOME'], 'tools'))
else:
    sys.exit("Por favor declara la variable de entorno 'SUMO_HOME'")

import traci
import sumolib

# CONFIGURADO PARA ABRIR LA INTERFAZ GRÁFICA POR DEFECTO
SUMO_CMD = ["sumo-gui", "-c", "reto.sumocfg"]
P_SIN = 0.25
T_ATENCION = 120

HOSPITALES_GEO = {
    'VCM':         ({'lon': -78.992923, 'lat': -2.911098, 'tipo': 'publico'}),
    'IESS_JCA':    ({'lon': -78.970118, 'lat': -2.898698, 'tipo': 'publico'}),
    'MILITAR':     ({'lon': -79.003968, 'lat': -2.903146, 'tipo': 'publico'}),
    'MUNI_PAT':    ({'lon': -78.982263, 'lat': -2.866103, 'tipo': 'publico'}),
    'MUNI_VALLE':  ({'lon': -78.961959, 'lat': -2.919522, 'tipo': 'publico'}),
    'MONTE_SINAI': ({'lon': -79.007373, 'lat': -2.908606, 'tipo': 'privado'}),
    'DEL_RIO':     ({'lon': -78.960796, 'lat': -2.892939, 'tipo': 'privado'}),
}

hospitales = {}
accidentes = []
estadisticas_stock = []

def formato_tiempo(step):
    m, s = divmod(step, 60)
    h, m = divmod(m, 60)
    return f"[{h:02d}:{m:02d}:{s:02d}]"

def dibujar_bloque(id_bloque, x, y, color):
    try:
        # Dibuja un cuadrado de 40x40 metros centrado en las coordenadas
        shape = [(x-20, y-20), (x+20, y-20), (x+20, y+20), (x-20, y+20)]
        traci.polygon.add(id_bloque, shape, color, True)
    except Exception:
        pass

def inicializar_hospitales():
    random.seed(42)
    print("\n" + "="*60)
    print("🏥 INICIALIZANDO RED DE HOSPITALES Y FLOTA DE AMBULANCIAS")
    print("="*60)
    
    for hid, info in HOSPITALES_GEO.items():
        arista, pos, carril = traci.simulation.convertRoad(info['lon'], info['lat'], isGeo=True, vClass="emergency")
        stock_ini = random.randint(1, 3) if info['tipo'] == 'publico' else random.randint(0, 1)
        unidades = collections.deque([f"AMB_{hid}_{i}" for i in range(stock_ini)])
        
        hospitales[hid] = {
            'arista': arista, 'pos': pos, 'tipo': info['tipo'],
            'stock_ini': stock_ini, 'unidades': unidades,
            'despachos': 0, 'retornos': 0, 'rechazos': 0, 'ocupado_s': 0
        }
        
        # Color del bloque: Verde (público) o Azul (privado)
        x, y = traci.simulation.convertGeo(info['lon'], info['lat'], fromGeo=True)
        color = (0, 200, 0, 180) if info['tipo'] == 'publico' else (0, 100, 255, 180)
        dibujar_bloque(f"bloque_{hid}", x, y, color)
        
        print(f" [+] Hospital {hid:<12} | Arista: {arista:<15} | Stock: {stock_ini} unid.")

def generar_agenda():
    agenda = []
    for h in range(3):
        for _ in range(5):
            agenda.append(random.randint(max(300, h * 3600), (h + 1) * 3600 - 1))
    return sorted(agenda)

def provocar_accidente(step):
    vehiculos = traci.vehicle.getIDList()
    buses = [v for v in vehiculos if traci.vehicle.getTypeID(v) == "bus" and traci.vehicle.getSpeed(v) > 4 and traci.vehicle.getLanePosition(v) > 60]
    if not buses: return False
    
    bus = random.choice(buses)
    moto = traci.vehicle.getFollower(bus, 80)[0]
    
    if not moto or traci.vehicle.getTypeID(moto) != "moto":
        moto = f"moto_suicida_{step}"
        try:
            ruta_bus = traci.vehicle.getRoute(bus)
            idx = traci.vehicle.getRouteIndex(bus)
            traci.route.add(f"ruta_{moto}", ruta_bus[idx:])
            traci.vehicle.add(moto, f"ruta_{moto}", typeID="moto", departPos=max(0, traci.vehicle.getLanePosition(bus) - 45))
        except: return False

    traci.vehicle.setSpeedMode(moto, 0)
    traci.vehicle.setLaneChangeMode(moto, 0)
    traci.vehicle.setSpeed(moto, 22)
    traci.vehicle.setColor(moto, (255, 165, 0, 255))
    return True

def procesar_colisiones(step):
    for col in traci.simulation.getCollisions():
        if {col.colliderType, col.victimType} == {"bus", "moto"}:
            bus_id = col.collider if col.colliderType == "bus" else col.victim
            moto_id = col.victim if col.victimType == "moto" else col.collider
            
            if not any(a['bus'] == bus_id or a['moto'] == moto_id for a in accidentes):
                arista = traci.vehicle.getRoadID(bus_id)
                if arista.startswith(':'): continue
                
                try: pos = max(0.1, min(col.pos, traci.lane.getLength(f"{arista}_0") - 0.1))
                except: pos = max(0.1, traci.vehicle.getLanePosition(bus_id))
                
                acc = {
                    'id': len(accidentes) + 1, 't_acc': step, 'bus': bus_id, 'moto': moto_id, 'arista': arista, 'pos': pos,
                    'estado': 'espera', 'reintentos': 0, 'amb_id': None, 'h_origen': None,
                    't_despacho': None, 't_llegada': None, 't_fin': None, 'h_retorno': None, 't_retorno': None
                }
                
                for v in (bus_id, moto_id):
                    try:
                        traci.vehicle.setSpeedMode(v, 31)
                        traci.vehicle.setSpeed(v, 0)
                        traci.vehicle.setColor(v, (255, 0, 0, 255))
                    except: pass
                
                try:
                    x, y = traci.vehicle.getPosition(bus_id)
                    dibujar_bloque(f"acc_{acc['id']}", x, y, (255, 0, 0, 200)) # Bloque Rojo de Accidente
                except: pass
                
                print(f"\n{formato_tiempo(step)} 💥 ALERTA: Colisión registrada entre {bus_id} y {moto_id} (Vía: {arista})")
                accidentes.append(acc)

def gestionar_despachos(step):
    for acc in accidentes:
        if acc['estado'] == 'espera' and (step - acc['t_acc']) % 30 == 0:
            mejor_h, menor_tt = None, float('inf')
            for hid, hdata in hospitales.items():
                if hdata['unidades'] and random.random() > P_SIN:
                    ruta = traci.simulation.findRoute(hdata['arista'], acc['arista'], vType="ambulance")
                    if ruta.edges and ruta.travelTime < menor_tt:
                        mejor_h, menor_tt = hid, ruta.travelTime
            
            if mejor_h:
                acc['amb_id'] = hospitales[mejor_h]['unidades'].popleft()
                acc['h_origen'] = mejor_h
                acc['t_despacho'] = step
                acc['estado'] = 'en_camino'
                hospitales[mejor_h]['despachos'] += 1
                
                try:
                    ruta = traci.simulation.findRoute(hospitales[mejor_h]['arista'], acc['arista'], vType="ambulance")
                    traci.route.add(f"ruta_{acc['amb_id']}_{step}", ruta.edges)
                    traci.vehicle.add(acc['amb_id'], f"ruta_{acc['amb_id']}_{step}", typeID="ambulance", departPos=hospitales[mejor_h]['pos'])
                    
                    # MAGIA VISUAL: Seleccionar vehículo para que SUMO-GUI dibuje su ruta en pantalla
                    traci.gui.toggleSelection(acc['amb_id'], 'vehicle')
                except: pass
                
                print(f"{formato_tiempo(step)} 🚑 DESPACHO: Unidad {acc['amb_id']} sale del hospital {mejor_h} hacia la emergencia.")
            else:
                acc['reintentos'] += 1
                for hid in hospitales: hospitales[hid]['rechazos'] += 1

def gestionar_ambulancias(step):
    llegadas = traci.simulation.getArrivedIDList()
    
    for acc in accidentes:
        if acc['estado'] == 'en_camino':
            if acc['amb_id'] not in traci.vehicle.getIDList():
                if acc['amb_id'] in llegadas:
                    acc['t_llegada'] = step
                    acc['estado'] = 'atendiendo'
                continue
            
            if step % 60 == 0:
                try: traci.vehicle.rerouteTraveltime(acc['amb_id'])
                except: pass
            
            try: d = traci.simulation.getDistanceRoad(traci.vehicle.getRoadID(acc['amb_id']), traci.vehicle.getLanePosition(acc['amb_id']), acc['arista'], acc['pos'], isDriving=True)
            except: d = -1
            
            vel = traci.vehicle.getSpeed(acc['amb_id'])
            if (d >= 0 and d <= 50) or (traci.vehicle.getRoadID(acc['amb_id']) == acc['arista']) or (d >= 0 and d <= 300 and vel < 1 and traci.vehicle.getWaitingTime(acc['amb_id']) >= 30):
                acc['t_llegada'] = step
                acc['estado'] = 'atendiendo'
                try: traci.vehicle.setSpeed(acc['amb_id'], 0)
                except: pass
                print(f"{formato_tiempo(step)} 📍 LLEGADA: Unidad {acc['amb_id']} en la escena. Iniciando {T_ATENCION}s de atención médica.")
                
        elif acc['estado'] == 'atendiendo' and (step - acc['t_llegada']) >= T_ATENCION:
            for v in (acc['bus'], acc['moto']):
                try: traci.vehicle.remove(v, 0)
                except: pass
            try: traci.polygon.remove(f"acc_{acc['id']}")
            except: pass
            
            mejor_h, menor_tt = None, float('inf')
            for hid, hdata in hospitales.items():
                ruta = traci.simulation.findRoute(acc['arista'], hdata['arista'], vType="ambulance")
                if ruta.edges and ruta.travelTime < menor_tt:
                    mejor_h, menor_tt = hid, ruta.travelTime
            
            acc['h_retorno'] = mejor_h if mejor_h else acc['h_origen']
            acc['t_fin'] = step
            acc['estado'] = 'retorno'
            
            if acc['amb_id'] in traci.vehicle.getIDList():
                try:
                    traci.vehicle.setSpeedMode(acc['amb_id'], 31)
                    traci.vehicle.setLaneChangeMode(acc['amb_id'], 1621)
                    traci.vehicle.setSpeed(acc['amb_id'], -1)
                    traci.vehicle.changeTarget(acc['amb_id'], hospitales[acc['h_retorno']]['arista'])
                    traci.gui.toggleSelection(acc['amb_id'], 'vehicle') # Trazar ruta de retorno
                except: pass
            print(f"{formato_tiempo(step)} 🔄 RETORNO: Atención finalizada. Unidad {acc['amb_id']} traslada a pacientes al {acc['h_retorno']}.")
            
        elif acc['estado'] == 'retorno':
            if acc['amb_id'] in llegadas:
                acc['t_retorno'] = step
                acc['estado'] = 'cerrado'
                hospitales[acc['h_retorno']]['unidades'].append(acc['amb_id'])
                hospitales[acc['h_retorno']]['retornos'] += 1
                hospitales[acc['h_origen']]['ocupado_s'] += (acc['t_retorno'] - acc['t_despacho'])
                print(f"{formato_tiempo(step)} ✅ COMPLETADO: Unidad {acc['amb_id']} disponible en la base del {acc['h_retorno']}.")

def guardar_estadisticas():
    print("\n" + "="*60)
    print("💾 GUARDANDO ESTADÍSTICAS Y RESULTADOS EN CSV...")
    with open("accidentes.csv", "w") as f:
        f.write("id,t_acc,estado,espera_s,h_origen,h_retorno,t_despacho,t_llegada,t_fin,t_retorno\n")
        for a in accidentes:
            espera = a['t_despacho'] - a['t_acc'] if a['t_despacho'] else -1
            f.write(f"{a['id']},{a['t_acc']},{a['estado']},{espera},{a['h_origen']},{a['h_retorno']},{a['t_despacho']},{a['t_llegada']},{a['t_fin']},{a['t_retorno']}\n")

    with open("hospitales.csv", "w") as f:
        f.write("hospital,tipo,stock_ini,stock_fin,despachos,retornos,rechazos,ocupado_s,utilizacion\n")
        for hid, h in hospitales.items():
            util = h['ocupado_s'] / (10800 * h['stock_ini']) if h['stock_ini'] > 0 else "n/a"
            f.write(f"{hid},{h['tipo']},{h['stock_ini']},{len(h['unidades'])},{h['despachos']},{h['retornos']},{h['rechazos']},{h['ocupado_s']},{util}\n")

    with open("stock.csv", "w") as f:
        f.write("step," + ",".join(hospitales.keys()) + "\n")
        for row in estadisticas_stock:
            f.write(",".join(map(str, row)) + "\n")
    print("✅ Archivos CSV generados correctamente.")
    print("="*60 + "\n")

def run():
    print("Iniciando conexión con TraCI...")
    traci.start(SUMO_CMD)
    inicializar_hospitales()
    agenda = generar_agenda()
    
    print("\n⏳ Iniciando Simulación de Cuenca (12600 pasos)...")
    step = 0
    while traci.simulation.getMinExpectedNumber() > 0 and step <= 12600:
        traci.simulationStep()
        
        if agenda and step >= agenda[0]:
            if provocar_accidente(step):
                agenda.pop(0)
            else:
                agenda[0] += 60 

        procesar_colisiones(step)
        gestionar_despachos(step)
        gestionar_ambulancias(step)
        
        if step % 60 == 0:
            estadisticas_stock.append([step] + [len(h['unidades']) for h in hospitales.values()])
            
        step += 1

    guardar_estadisticas()
    traci.close()
    sys.stdout.flush()

if __name__ == "__main__":
    run()
