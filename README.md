# Interval Shortest Path con estados aleatorios (Min–Max)

Script en Python para calcular rutas más cortas en un **grafo dirigido con pesos por intervalos** \([a,b]\) y **aristas con estado** (`habilitada`/`cerrada`). Integra:

- **Línea base**: Dijkstra con \(w=b\) (minimiza el **peor caso**).
- **Ruta robusta**: *Interval‑Dijkstra* (label‑setting **Min–Max**), prioriza **B** y en empate **A**.\
- **Preprocesamiento**: elimina aristas `cerrada` antes de calcular rutas.
- **Retroalimentación**: imprime paso a paso el estado del grafo, alcanzabilidad y comparación **inicial vs. final**.

---

## ¿Qué hace? (resumen corto)
1. **Genera** estados aleatorios para las aristas del dataset (nodos `a`…`h`).  
2. **Preprocesa** el grafo filtrando las aristas `cerrada`.  
3. **Calcula** la **línea base** (Dijkstra con `b`) y la usa como **cota de poda**.  
4. **Resuelve** la **ruta robusta** con etiquetas no dominadas \([A,B]\).  
5. **Compara** *línea base vs. robusta* y entrega un **resumen final** claro.

---

## Uso rápido
```bash
python3 interval_user_dataset_random_states_verbose.py \
  --seed 42 \        # semilla para reproducir estados
  --p 0.25 \         # prob. de cerrar una arista (0..1)
  --src a \          # nodo origen
  --dst h            # nodo destino
```

**Salida**: lista de aristas con estado, alcanzabilidad, ruta **base** (`A_base`, `B_base`), ruta **robusta** (`A*`, `B*`) y conclusión.

---

## Algoritmos integrados
- **Dijkstra (w=b)** — sirve como **línea base** y **cota superior (UB)** del peor caso.  
- **Interval‑Dijkstra (label‑setting Min–Max)** — mantiene, por nodo, **etiquetas no dominadas** \([A,B]\).  
  - **Dominancia:** \([A_1,B_1]\) domina a \([A_2,B_2]\) si \(B_1 \le B_2\) y \(A_1 \le A_2\) con al menos una estricta.  
  - **Poda por línea base:** descarta candidatos con \(B>B_{\text{base}}\) o \((B=B_{\text{base}} \land A>A_{\text{base}})\).

---

## Dataset embebido
Aristas dirigidas entre `a…h` con intervalos \([a,b]\) (tiempos):
`(a,b,[5,20])`, `(b,c,[12,35])`, `(c,d,[8,25])`, `(d,e,[15,40])`, `(e,f,[3,18])`,
`(f,g,[10,30])`, `(g,h,[7,22])`, `(h,a,[20,45])`, `(a,c,[6,28])`,
`(b,d,[11,33])`, `(c,e,[9,27])`, `(d,f,[14,38])`, `(e,g,[4,19])`, `(f,h,[13,36])`.

---

## Pruebas en consola

### Caso A — **Infactible** por cierres
Comando:
```bash
python3 interval_user_dataset_random_states_verbose.py --seed 42 --p 0.30 --src b --dst g
```
Salida (resumen):
- **Aristas**: 14 totales; por ejemplo, 3 **cerradas**.  
- **Alcanzabilidad**: `g` **no es alcanzable** desde `b`.  
- **Cálculo**: *no existe ruta de línea base*.  
- **Resumen final**: **INFACTIBLE**. Recomendación: bajar `--p` o cambiar `--seed`.

> Esto muestra que si los cierres bloquean todos los caminos `b→…→g`, no habrá solución.

### Caso B — **Solución encontrada (base = robusta)**
Comando:
```bash
python3 interval_user_dataset_random_states_verbose.py --seed 42 --p 0.02 --src b --dst g
```
Salida:
- **Aristas**: 14 totales; **0 cerradas**.  
- **Alcanzabilidad**: `g` es alcanzable desde `b`.  
- **Línea base**: ruta `['b','c','e','g']` con `A_base=25.0`, `B_base=81.0`.  
- **Robusta (Min–Max)**: misma ruta `['b','c','e','g']` con `A*=25.0`, `B*=81.0`.  
- **Diferencias**: `ΔA=0.0`, `ΔB=0.0` → **coinciden**.  
- **Conclusión**: la solución robusta es **mejor o igual** que la línea base (en este caso, igual).

> Aquí no hay cierres, por lo que la ruta que minimiza el peor caso coincide con la robusta.

---

## Salida
- Si **no hay ruta base**, el problema es **infactible** con los cierres actuales.  
- Si hay rutas alternativas, la robusta puede **mejorar** \(B\) o, a igualdad de \(B\), bajar \(A\).  
- Si no hay incertidumbre efectiva (o cierres), base y robusta pueden **coincidir**.

---

## Complejidad (orientativa)
- **Dijkstra (base):** \(O(m\\log n)\).  
- **Interval‑Dijkstra (robusta):** \(O(K\\log K + m\\cdot\\bar{D})\), con \(K\) = nº de etiquetas generadas.


> Sugerencia: para experimentos, cambia `--seed` y `--p`. Si deseas fijar manualmente qué aristas están cerradas, puedo agregarte una opción `--closed a->c b->d ...`.
