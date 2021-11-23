# Copyright 2021 Lin Wang

# This code is part of the Advanced Computer Networks course at Vrije
# Universiteit Amsterdam.

# Licensed under the Apache License, Version 2.0 (the "License"); you may not
# use this file except in compliance with the License. You may obtain a copy
# of the License at

#   http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

from typing import Sequence
from topo import Node
import topo
import sys
import pandas as pd
import matplotlib.pyplot as plt


# Same setup for Jellyfish and Fattree
num_servers = 686
num_switches = 245
num_ports = 14

# num_servers = 16
# num_switches = 20
# num_ports = 4

ft_topo = topo.Fattree(num_ports)
jf_topo = topo.Jellyfish(num_servers, num_switches, num_ports)

# TODO: code for reproducing Figure 1(c) in the jellyfish paper

def dijkstra(graph: Sequence[Node], origin_node: Node):
    """Calculate the shortest path between all possible pairs between origin_node and all other
    nodes in the graph.

    Args:
        graph (Sequence[Node]): The graph to search for shortest path pairs. origin_node should be in this graph.
        origin_node (Node): Node to start from, i.e. the node that is always part of each pair

    Returns:
        dict: Keys are the destination from the origin_node. Values are the node object and the distance in hops. 
            Example: {"10.0.0.1": {"node": .., "dist": 2}, ...}
    """
    visited = {}
    unvisited = {}

    # init unvisited
    for node in graph:
        unvisited[node.id] = {"node": node, "dist": sys.maxsize}
    unvisited[origin_node.id] = {"node": origin_node, "dist": 0}

    while (len(unvisited) != 0):
        min_key = min(unvisited, key=lambda key: unvisited[key]["dist"])

        # Move current node from unvisited to visited
        visited[min_key] = unvisited[min_key]
        unvisited.pop(min_key)

        neighbor = visited[min_key]["node"]
        dist = visited[min_key]["dist"]
        # Update edges' dists
        for edge in neighbor.edges:
            # Find the DijkNode in unvisited that corresponds to the neighbor attached to edge
            other_node = edge.lnode if edge.lnode.id != neighbor.id else edge.rnode
        
            unvisited_neighbor = unvisited.get(other_node.id)
            if (unvisited_neighbor is None): continue

            new_dist = dist + 1
            if (new_dist < unvisited_neighbor["dist"]):
                unvisited[other_node.id]["dist"] = new_dist

    return visited


def get_count_per_path(topo):
    """Returns the unique set of pairs per path length.

    Returns:
        dict: {
            [path_length: int]: set(
                    [1.1.1.1, 1.1.1.2], 
                    [1.1.1.1, 1.1.1.3], 
                    ...
                )
            }
    """
    graph = topo.servers + topo.switches

    pairs = {} # in the form ["path_length": "count"]
    for i in range(1, 8):
        pairs[i] = set() # ensure that only unique pairs are registered

    for source_server in topo.servers:
        distances = dijkstra(graph, source_server) # get shortest paths for server
        # format: {"10.0.0.1": {"node": .., "dist": 2}}

        # Add only paths from source_server to another server
        for dest_server in topo.servers:
            if source_server == dest_server: 
                continue
            if distances[dest_server.id]["dist"] < 2:
                continue
            dist = distances[dest_server.id]["dist"]
            pair = ((source_server.id, dest_server.id) 
                if source_server.id < dest_server.id 
                else (dest_server.id, source_server.id))
            pairs[dist].update([pair])
    return {key: len(value) for key, value in pairs.items()}


def get_avg_count_per_path(topo, n_times):
    """Run get_count_per_path n_times and return the average.
    """
    sum_path_lengths = {} # {n_path: n_pairs}

    for _ in range(n_times):
        pairs = get_count_per_path(topo)
        for n_paths, n_pairs in pairs.items():
            if (sum_path_lengths.get(n_paths) is None):
                sum_path_lengths[n_paths] = 0
            sum_path_lengths[n_paths] += n_pairs

    return {key:sum_n_pairs / n_times for key, sum_n_pairs in sum_path_lengths.items()}


def normalize(path_count: dict, total_pairs: int) -> dict:
    """Transform the count to a fraction.

    Args:
        path_count (dict): dict: {[path_length: int]: [count: float]}}
    Returns:
        dict: dict: {[path_length: int]: [fraction: float]}
    """
    result = {}
    for path, count in path_count.items():
        print(f"value / total_pairs: {count} / {total_pairs} = {count / total_pairs}")
        result[path] = count / total_pairs
    return result


# Get list of all server pairs in topology (should be same for both topologies)
# This excludes the pair (x, x), and it also assumes that (x, y) == (y, x)
def get_server_pairs(topology):
    pairlist = []
    for i in range(len(topology.servers)):
        for j in range(i, len(topology.servers)):
            pair = (i, j) if i < j else (j, i)
            if i != j:
                pairlist.append(pair)
    # remove all duplicate pairs
    pairlist = list(dict.fromkeys(pairlist))
    return pairlist


def draw_histogram(jf, ft, axis=[2,3,4,5,6]) :
    print(jf)
    print(ft)
    barwidth = 0.30
    
    fig, ax = plt.subplots()
    ax.bar([x - barwidth/2 for x in axis], jf, barwidth, label="Jellyfish", color="blue", edgecolor="black")
    # drawing hatch first for fattree, then draw edges
    ax.bar([x + barwidth/2 for x in axis], ft, barwidth, label="Fat-tree", color="none", edgecolor="orangered", hatch="xxx", zorder=0)
    ax.bar([x + barwidth/2 for x in axis], ft, barwidth, color="none", edgecolor="black")

    # Here, the axes labels are set.
    ax.set_ylabel("Fraction of Server Pairs")
    ax.set_xlabel("Path length")
    ax.legend(bbox_to_anchor=(0.7, -0.12), ncol=len(axis))
    ticks = range(0, 11)
    ticks = [x / 10 for x in ticks]
    ax.set_yticks(ticks)
    plt.grid(linestyle='dotted')
    fig.tight_layout()
    plt.show()


def to_plt_data(topo_data):
    """Transform the data to be accepted easily by pyplot
    """
    result = []
    for i in range(5):
        i = i + 2 # start at 2, end at 6
        if (topo_data.get(i) is None):
            result.append(0)
        else:
            result.append(topo_data[i])
    return result


def run(ft_topo, jf_topo):
    total_ft_pairs = len(get_server_pairs(ft_topo))
    total_jf_pairs = len(get_server_pairs(jf_topo))

    ft_data = get_count_per_path(ft_topo)
    jf_data = get_avg_count_per_path(jf_topo, 10)

    ft_normalized = normalize(ft_data, total_ft_pairs)
    jf_normalized = normalize(jf_data, total_jf_pairs)

    ft_plottable = to_plt_data(ft_normalized)
    jf_plottable = to_plt_data(jf_normalized)

    draw_histogram(jf_plottable, ft_plottable)

    # (pd.DataFrame
    #     .from_dict(ft_plottable, orient="index")
    #     .to_csv("fattree.csv", header=False))

    # (pd.DataFrame
    #     .from_dict(jf_plottable, orient="index")
    #     .to_csv("jellyfish.csv", header=False))

run(ft_topo, jf_topo)
