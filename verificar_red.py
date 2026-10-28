import os, sys
sys.path.append(os.path.join(os.environ.get('SUMO_HOME', '/usr/share/sumo'), 'tools'))
import sumolib

net = sumolib.net.readNet('cuenca_ciudad.net.xml')

# --- Un solo componente (fuertemente conexo, solo aristas de autos) ---
edges = [e for e in net.getEdges() if e.allows('passenger')]
def alcanza(inicio, siguientes):
    vistos, pila = {inicio}, [inicio]
    while pila:
        e = pila.pop()
        for n in siguientes(e):
            if n not in vistos and n.allows('passenger'):
                vistos.add(n); pila.append(n)
    return vistos
ini = edges[0]
fwd = alcanza(ini, lambda e: e.getOutgoing())
bwd = alcanza(ini, lambda e: e.getIncoming())
scc = fwd & bwd
print(f"Aristas (autos): {len(edges)} | en el componente principal: {len(scc)}")
print("COMPONENTE UNICO: OK" if len(scc) == len(edges) else "COMPONENTE UNICO: REVISAR")

# --- Hospitales (tabla 4.5) ---
H = {
 'VCM':        (-78.992923, -2.911098),
 'IESS_JCA':   (-78.970118, -2.898698),
 'MILITAR':    (-79.003968, -2.903146),
 'MUNI_PAT':   (-78.982263, -2.866103),
 'MUNI_VALLE': (-78.961959, -2.919522),
 'MONTE_SINAI':(-79.007373, -2.908606),
 'DEL_RIO':    (-78.960796, -2.892939),
}
print(f"\n{'hospital':12s} {'arista':22s} {'dist(m)':>8s}  calle")
for h, (lon, lat) in H.items():
    x, y = net.convertLonLat2XY(lon, lat)
    cand = [(d, e) for e, d in net.getNeighboringEdges(x, y, 400) if e.allows('emergency')]
    if not cand:
        print(f"{h:12s} SIN ARISTA a menos de 400 m  <-- REVISAR"); continue
    d, e = min(cand, key=lambda t: t[0])
    estado = 'OK' if d < 200 else 'REVISAR (>200 m)'
    print(f"{h:12s} {e.getID():22s} {d:8.1f}  {e.getName()}  {estado}")
