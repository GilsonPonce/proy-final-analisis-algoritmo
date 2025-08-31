#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Verbose: Ruta robusta con datos embebidos y estados aleatorios (habilitada/cerrada),
# con retroalimentación clara paso a paso para el usuario.
# Autores: Estrella Galarza, Mite Guillen, Ponce Briones, Suárez Herrera, Vilema Lazo

import random
import heapq
import argparse
from dataclasses import dataclass
from typing import Dict, List, Tuple, Optional, Set

# =====================
# Parámetros por defecto
# =====================
DEF_SEED = 42
DEF_P_CERRADA = 0.02
SRC_DEFAULT = "b"
DST_DEFAULT = "g"

@dataclass(frozen=True)
class Edge:
    u: str; v: str; a: float; b: float; estado: str = "habilitada"

class Graph:
    def __init__(self):
        self.adj: Dict[str, List[Edge]] = {}
    def add(self,u,v,a,b,estado="habilitada"):
        self.adj.setdefault(u,[]); self.adj.setdefault(v,[])
        self.adj[u].append(Edge(u,v,a,b,estado))
    def vertices(self) -> List[str]: return list(self.adj.keys())
    def edges(self) -> List[Edge]: return [e for edges in self.adj.values() for e in edges]
    def preprocesar(self) -> "Graph":
        Gp = Graph()
        for e in self.edges():
            if e.estado == "cerrada":
                continue
            Gp.add(e.u, e.v, e.a, e.b, "habilitada")
        return Gp

def build_user_graph_with_random_states(seed: int, p_cerrada: float) -> Graph:
    # Datos embebidos del usuario (dirigido)
    edges = [
        ("a","b",5,20),
        ("b","c",12,35),
        ("c","d",8,25),
        ("d","e",15,40),
        ("e","f",3,18),
        ("f","g",10,30),
        ("g","h",7,22),
        ("h","a",20,45),
        ("a","c",6,28),
        ("b","d",11,33),
        ("c","e",9,27),
        ("d","f",14,38),
        ("e","g",4,19),
        ("f","h",13,36),
    ]
    random.seed(seed)
    G = Graph()
    for u,v,a,b in edges:
        estado = "cerrada" if random.random() < p_cerrada else "habilitada"
        G.add(u,v,a,b,estado)
    return G

# ------------------ Algoritmos ------------------
def dijkstra_worst(G: Graph, s: str, t: str) -> Tuple[float,float,List[str]]:
    dist = {v: float('inf') for v in G.vertices()}
    prev = {v: None for v in G.vertices()}
    dist[s] = 0.0; pq=[(0.0,s)]
    while pq:
        d,u = heapq.heappop(pq)
        if d!=dist[u]: continue
        if u==t: break
        for e in G.adj.get(u,[]):
            nd = d + e.b
            if nd < dist[e.v]:
                dist[e.v]=nd; prev[e.v]=u; heapq.heappush(pq,(nd,e.v))
    if dist.get(t, float('inf')) == float('inf'):
        return float('inf'), float('inf'), []
    # reconstruir path
    path=[]; v=t
    while v is not None: path.append(v); v=prev[v]
    path.reverse()
    # computar A,B
    A=B=0.0
    for i in range(len(path)-1):
        u,v = path[i], path[i+1]
        e = next(e for e in G.adj[u] if e.v==v)
        A += e.a; B += e.b
    return A,B,path

def dominated(cand: Tuple[float,float], labels: List[Tuple[float,float]]) -> bool:
    A,B = cand
    for (A2,B2) in labels:
        if (B2<=B and A2<=A) and (B2<B or A2<A):
            return True
    return False

def interval_dijkstra_minmax(G: Graph, s: str, t: str):
    Gp = G.preprocesar()
    A0,B0,path0 = dijkstra_worst(Gp,s,t)
    UB_B, UB_A = B0, A0
    L = {v:[] for v in Gp.vertices()}
    pred: Dict[Tuple[str,float,float], Tuple[str,float,float]] = {}
    heap=[(0.0,0.0,s,0.0,0.0)]  # (B,A,node,A,B)
    L[s].append((0.0,0.0))
    while heap:
        Bp,Ap,u,Au,Bu = heapq.heappop(heap)
        if (Au,Bu) not in L[u]: continue
        if u==t:
            return {"best_path": reconstruct(pred,s,t,(Au,Bu)), "best_A":Au, "best_B":Bu,
                    "baseline":{"path":path0,"A":A0,"B":B0}}
        for e in Gp.adj.get(u,[]):
            candA, candB = Au+e.a, Bu+e.b
            # poda: permite empates con la línea base
            if (candB>UB_B) or (candB==UB_B and candA>UB_A): continue
            if dominated((candA,candB), L[e.v]): continue
            # quitar dominadas por cand
            L[e.v] = [(A2,B2) for (A2,B2) in L[e.v] if not ((B2>=candB and A2>=candA) and (B2>candB or A2>candA))]
            L[e.v].append((candA,candB))
            pred[(e.v,candA,candB)] = (u,Au,Bu)
            heapq.heappush(heap, (candB,candA,e.v,candA,candB))
    return {"best_path":[], "best_A":float('inf'), "best_B":float('inf'),
            "baseline":{"path":path0,"A":A0,"B":B0}}

def reconstruct(pred, s, t, lab):
    path=[t]; node,A,B = t, lab[0], lab[1]
    while not (node==s and A==0.0 and B==0.0):
        if (node,A,B) not in pred: break
        (u,Au,Bu) = pred[(node,A,B)]
        node,A,B=u,Au,Bu; path.append(node)
    path.reverse(); return path

# ------------------ Utilidades de explicación ------------------
def reachability(G: Graph, s: str) -> Set[str]:
    vis=set([s]); stack=[s]
    while stack:
        u=stack.pop()
        for e in G.adj.get(u,[]):
            v=e.v
            if v not in vis:
                vis.add(v); stack.append(v)
    return vis

def summarize_graph_states(G: Graph) -> Dict[str,int]:
    total=len(G.edges()); closed=sum(1 for e in G.edges() if e.estado=="cerrada")
    open_=total-closed
    return {"total": total, "habilitadas": open_, "cerradas": closed}

def explain_pipeline(G: Graph, s: str, t: str):
    print("1) Generación de estados aleatorios")
    summary = summarize_graph_states(G)
    print(f"   - Aristas totales: {summary['total']} | habilitadas: {summary['habilitadas']} | cerradas: {summary['cerradas']}")
    print("   - Lista (u -> v [a,b] estado):")
    for e in G.edges():
        print(f"     • {e.u} -> {e.v}  [{e.a}, {e.b}]  estado={e.estado}")
    # Preproceso
    print("\n2) Preprocesamiento (se eliminan 'cerradas')")
    Gp = G.preprocesar()
    sum2 = summarize_graph_states(Gp)
    print(f"   - Aristas utilizables: {sum2['habilitadas']} (todas habilitadas tras preprocesar)")
    # Alcanzabilidad
    print("\n3) Alcanzabilidad desde el origen")
    vis = reachability(Gp, s)
    if t in vis:
        print(f"   - El destino '{t}' es alcanzable desde '{s}' con las aristas habilitadas.")
    else:
        print(f"   - El destino '{t}' NO es alcanzable desde '{s}'. No existirá ruta.")
    return Gp

def compare_paths(base, robust):
    path0, A0, B0 = base["path"], base["A"], base["B"]
    pathR, AR, BR = robust["path"], robust["A"], robust["B"]
    if not pathR:
        print("   - No se encontró ruta robusta (Min–Max).")
        return
    print("\n5) Comparación Línea base vs. Ruta robusta (criterio Min–Max)")
    print(f"   - Línea base  : {path0} | A_base={A0} | B_base={B0}")
    print(f"   - Ruta robusta: {pathR} | A*={AR} | B*={BR}")
    dA = AR - A0; dB = BR - B0
    tagA = "igual" if dA==0 else ("mejor (↓)" if dA<0 else "peor (↑)")
    tagB = "igual" if dB==0 else ("mejor (↓)" if dB<0 else "peor (↑)")
    print(f"   - Diferencias : ΔA={dA} ({tagA}), ΔB={dB} ({tagB})")
    if BR < B0 or (BR==B0 and AR < A0):
        print("   - La ruta robusta **mejora** o **iguala** la línea base según el criterio Min–Max.")
    else:
        print("   - La ruta robusta coincide con la línea base (no había alternativa mejor bajo Min–Max).")

def main():
    ap = argparse.ArgumentParser(description="Interval shortest path con retroalimentación detallada.")
    ap.add_argument("--seed", type=int, default=DEF_SEED, help="semilla para cerrar/habilitar aristas")
    ap.add_argument("--p", type=float, default=DEF_P_CERRADA, help="probabilidad de marcar una arista como cerrada (0..1)")
    ap.add_argument("--src", type=str, default=SRC_DEFAULT, help="nodo origen")
    ap.add_argument("--dst", type=str, default=DST_DEFAULT, help="nodo destino")
    args = ap.parse_args()

    # 0) Construcción
    G = build_user_graph_with_random_states(seed=args.seed, p_cerrada=args.p)

    print("=== ESCENARIO ===")
    print(f"Semilla={args.seed}  Probabilidad_cierre={args.p:.2f}  Origen={args.src}  Destino={args.dst}")

    # 1–3) Explicación del pipeline + preprocesado
    Gp = explain_pipeline(G, args.src, args.dst)

    # 4) Cálculos
    print("\n4) Cálculo de rutas")
    A0,B0,path0 = dijkstra_worst(Gp, args.src, args.dst)
    base = {"path": path0, "A": A0, "B": B0}
    if not path0:
        print("   - No existe ruta de línea base (no hay camino con aristas habilitadas).")
        print("\n6) Resumen final\n   Resultado: **INFACTIBLE** por cierres. Intenta bajar --p o cambiar la semilla --seed.\n")
        return
    robust = interval_dijkstra_minmax(G, args.src, args.dst)  # usa poda por baseline
    print(f"   - Ruta de línea base encontrada: {path0} (A={A0}, B={B0})")
    print("   - Ejecutando algoritmo robusto (label-setting Min–Max) con poda por línea base...")
    if robust['best_path']:
        print(f"   - Ruta robusta encontrada           : {robust['best_path']} (A*={robust['best_A']}, B*={robust['best_B']})")
    else:
        print("   - No se encontró ruta robusta.")

    # 5) Comparación
    compare_paths(base, {"path": robust["best_path"], "A": robust["best_A"], "B": robust["best_B"]})

    # 6) Resumen final
    print("\n6) Resumen final")
    if robust["best_path"]:
        concl = "mejor o igual que la línea base" if (robust["best_B"] < base["B"] or (robust["best_B"]==base["B"] and robust["best_A"]<=base["A"])) else "igual o peor que la línea base"
        print(f"   - Ruta final (robusta): {robust['best_path']}  con (A*={robust['best_A']}, B*={robust['best_B']}).")
        print(f"   - Conclusión: La solución robusta es {concl} bajo el criterio Min–Max (minimizar B y, en empate, A).")
    else:
        print("   - No hay ruta robusta; la instancia es infactible con los cierres actuales.")

if __name__ == "__main__":
    main()
