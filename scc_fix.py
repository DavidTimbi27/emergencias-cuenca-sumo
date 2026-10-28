import os, sys
sys.path.append(os.path.join(os.environ.get('SUMO_HOME', '/usr/share/sumo'), 'tools'))
import sumolib

net = sumolib.net.readNet('cuenca_ciudad.net.xml')
edges = [e for e in net.getEdges() if e.allows('passenger')]
ids = {e.getID() for e in edges}

def alcanza(ini, sig):
    vistos, pila = {ini}, [ini]
    while pila:
        e = pila.pop()
        for n in sig(e):
            if n not in vistos and n.getID() in ids:
                vistos.add(n); pila.append(n)
    return vistos

pend, mejor = set(edges), set()
while pend:
    e = next(iter(pend))
    scc = alcanza(e, lambda x: x.getOutgoing()) & alcanza(e, lambda x: x.getIncoming())
    if len(scc) > len(mejor):
        mejor = scc
    pend -= scc

quitar = sorted(ids - {e.getID() for e in mejor})
with open('fuera_scc.txt', 'w') as f:
    f.write(' '.join(quitar))
print(f"Aristas de autos: {len(ids)} | componente principal: {len(mejor)} | a quitar: {len(quitar)}")
