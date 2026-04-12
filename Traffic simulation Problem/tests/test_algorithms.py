from app.algorithms import edmonds_karp_max_flow, ford_fulkerson_max_flow


def test_algorithms_return_same_for_known_graph():
    capacities = {
        ("A", "B"): 10,
        ("A", "C"): 10,
        ("A", "D"): 5,
        ("B", "E"): 8,
        ("B", "F"): 4,
        ("C", "E"): 2,
        ("C", "F"): 8,
        ("D", "F"): 5,
        ("D", "H"): 4,
        ("E", "G"): 10,
        ("E", "H"): 3,
        ("F", "G"): 6,
        ("F", "H"): 8,
        ("G", "T"): 10,
        ("H", "T"): 10,
    }

    ff = ford_fulkerson_max_flow(capacities, "A", "T")
    ek = edmonds_karp_max_flow(capacities, "A", "T")

    assert ff == 20
    assert ek == 20


def test_zero_capacity_graph_returns_zero():
    capacities = {
        ("A", "B"): 0,
        ("B", "T"): 0,
    }

    ff = ford_fulkerson_max_flow(capacities, "A", "T")
    ek = edmonds_karp_max_flow(capacities, "A", "T")

    assert ff == 0
    assert ek == 0
