import random
import json
import os


def generate_erdos_renyi_graph(num_nodes, edge_probability):
    graph = {i: [] for i in range(num_nodes)}
    for i in range(num_nodes):
        for j in range(i + 1, num_nodes):
            if random.random() < edge_probability:
                graph[i].append(j)
                graph[j].append(i)
    return graph


def generate_sparse_graph(num_nodes, num_edges):
    edges = set()
    while len(edges) < num_edges:
        u = random.randint(0, num_nodes - 1)
        v = random.randint(0, num_nodes - 1)
        if u != v:
            edges.add((min(u, v), max(u, v)))
    graph = {i: [] for i in range(num_nodes)}
    for u, v in edges:
        graph[u].append(v)
        graph[v].append(u)
    return graph


def generate_sparse_graph_with_dense_nodes(num_nodes, num_edges_base, 
                                           num_dense_nodes, edge_probability_dense):
    graph = generate_sparse_graph(num_nodes, num_edges_base)
    dense_nodes = random.sample(range(num_nodes), num_dense_nodes)
    for node in dense_nodes:
        edge_set = set(graph[node])
        for other_node in range(num_nodes):
            if other_node != node and other_node not in edge_set:
                if random.random() < edge_probability_dense:
                    graph[node].append(other_node)
                    graph[other_node].append(node)
    return graph


def to_edge_sets(graphs):
    n = len(graphs[0])
    edge_sets = []
    for graph in graphs:
        edge_set = set()
        for u in range(n):
            for v in graph[u]:
                if u < v:
                    edge_set.add((u, v))
        edge_sets.append(list(edge_set))
    return {"n": n, "edge_sets": edge_sets}


def save_to_json(data, filename):
    with open(filename, "w") as f:
        json.dump(data, f)


if __name__ == "__main__":
    os.makedirs("inputs", exist_ok=True)
    
    # graphs1: relatively dense random graphs
    save_to_json(to_edge_sets([generate_erdos_renyi_graph(1000, 0.08) for _ in range(5)]), 
                 "inputs/graphs1.json")

    # graphs2: really dense random graphs
    save_to_json(to_edge_sets([generate_erdos_renyi_graph(200, 0.3) for _ in range(5)]), 
                 "inputs/graphs2.json")
    
    # graphs3: sparse random graphs
    save_to_json(to_edge_sets([generate_sparse_graph(100_000, 500_000) for _ in range(5)]), 
                 "inputs/graphs3.json")
    
    # graphs4: sparse random graphs with some dense nodes
    save_to_json(to_edge_sets([generate_sparse_graph_with_dense_nodes(100_000, 250_000, 100, 0.1) for _ in range(5)]), 
                 "inputs/graphs4.json")