# Copyright 2021 Misha Rigot

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
import sys


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