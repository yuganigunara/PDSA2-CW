from collections import defaultdict, deque
from typing import Dict, List, Tuple

CapacityMap = Dict[Tuple[str, str], int]


def _build_residual(capacities: CapacityMap):
    residual = defaultdict(dict)
    for (u, v), cap in capacities.items():
        residual[u][v] = cap
        residual[v].setdefault(u, 0)
    return residual


def ford_fulkerson_max_flow(capacities: CapacityMap, source: str, sink: str) -> int:
    residual = _build_residual(capacities)
    max_flow = 0

    while True:
        parent = {source: None}
        stack = [source]

        while stack and sink not in parent:
            u = stack.pop()
            for v, cap in residual[u].items():
                if cap > 0 and v not in parent:
                    parent[v] = u
                    stack.append(v)

        if sink not in parent:
            break

        path_flow = float("inf")
        v = sink
        while v != source:
            u = parent[v]
            path_flow = min(path_flow, residual[u][v])
            v = u

        v = sink
        while v != source:
            u = parent[v]
            residual[u][v] -= path_flow
            residual[v][u] += path_flow
            v = u

        max_flow += path_flow

    return int(max_flow)


def edmonds_karp_max_flow(capacities: CapacityMap, source: str, sink: str) -> int:
    residual = _build_residual(capacities)
    max_flow = 0

    while True:
        parent = {source: None}
        queue = deque([source])

        while queue and sink not in parent:
            u = queue.popleft()
            for v, cap in residual[u].items():
                if cap > 0 and v not in parent:
                    parent[v] = u
                    queue.append(v)

        if sink not in parent:
            break

        path_flow = float("inf")
        v = sink
        while v != source:
            u = parent[v]
            path_flow = min(path_flow, residual[u][v])
            v = u

        v = sink
        while v != source:
            u = parent[v]
            residual[u][v] -= path_flow
            residual[v][u] += path_flow
            v = u

        max_flow += path_flow

    return int(max_flow)


def capacities_from_edge_list(edge_caps: List[Tuple[str, str, int]]) -> CapacityMap:
    return {(u, v): cap for u, v, cap in edge_caps}
