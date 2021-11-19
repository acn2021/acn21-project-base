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

import sys
import random
import queue
import argparse
from enum import Enum, auto

# Class for an edge in the graph
class Edge:
    def __init__(self):
        self.lnode = None
        self.rnode = None
    
    def remove(self):
        self.lnode.edges.remove(self)
        self.rnode.edges.remove(self)
        self.lnode = None
        self.rnode = None

# Class for a node in the graph
class Node:
    def __init__(self, id, type):
        self.edges = []
        self.id = id
        self.type: NodeType = type

    # Add an edge connected to another node
    def add_edge(self, node):
        edge = Edge()
        edge.lnode = self
        edge.rnode = node
        self.edges.append(edge)
        node.edges.append(edge)
        return edge

    # Remove an edge from the node
    def remove_edge(self, edge):
        self.edges.remove(edge)

    # Decide if another node is a neighbor
    def is_neighbor(self, node):
        for edge in self.edges:
            if edge.lnode == node or edge.rnode == node:
                return True
        return False

class NodeType(Enum):
    SWITCH = auto()
    SERVER = auto()

class FattreeType(Enum):
    CORE_SWITCH = auto()
    AGGREGATE_SWITCH = auto()
    EDGE_SWITCH = auto()
    HOST = auto()

class FattreeNode(Node):
    # def __init__(self, id, type):
    #     super().__init__(id, type)
    def __init__(self, id, type, ft_type: FattreeType):
        super().__init__(id, type)
        self.ft_type = ft_type

    def edges_to_str(self) -> str:
        result = ""
        for edge in self.edges:
            lnode: FattreeNode = edge.lnode
            rnode: FattreeNode = edge.rnode
            other_node = lnode if self != lnode else rnode
            result += f"neighbor: {other_node.id}, {other_node.ft_type}\n"
        return result

class Jellyfish:

    def __init__(self, num_servers, num_switches, num_ports):
        self.servers = []
        self.switches = []
        self.generate(num_servers, num_switches, num_ports)

    # TODO: code for generating the jellyfish topology
    def generate(self, num_servers, num_switches, num_ports):
        pass

class Fattree:
    """Fattree topology.
    core switches:                  (k/2)^2
    pods:                           k
    layers per pod:                 2
    n switches per pod:             k
    n switches per layer per pod:   k/2
    n edges aggr -> edge:           k/2
    n edges aggr -> core:           k/2 ?

    """

    class Pod:
        def __init__(self, aggr_switches, edge_switches):
            self.aggr_switches: list[FattreeNode] = aggr_switches
            self.edge_switches: list[FattreeNode] = edge_switches

        def __str__(self) -> str:
            result = "===============\nPod:\n===============\n"
            result += "---------------\nAggregate switches:\n---------------\n"
            for aggr_switch in self.aggr_switches:
                aggr_switch: FattreeNode
                result += (
                    f"aggr_sw id: {aggr_switch.id}"
                    + f"\nnumber of links/edges: {len(aggr_switch.edges)}"
                    + f"\n\nlinks:\n{aggr_switch.edges_to_str()}\n")
            result += "---------------\nEdge switches:\n---------------\n"
            for edge_switch in self.edge_switches:
                edge_switch: FattreeNode
                result += (
                    f"edge_sw id: {edge_switch.id}"
                    + f"\nnumber of links/edges: {len(edge_switch.edges)}"
                    + f"\n\nlinks:\n{edge_switch.edges_to_str()}\n")
            return result


    def __init__(self, num_ports: int):
        if (num_ports % 2 != 0 or not (num_ports >= 2) ):
            raise ValueError("num_ports should be an even number starting from 2")
        self.num_ports = num_ports
        self.servers: list[FattreeNode] = []
        self.switches: list[FattreeNode] = []
        
        self.pods: list[self.Pod] = []
        self.core_switches: list[FattreeNode] = []
    
        self.generate(num_ports)

    def generate(self, num_ports: int):
        k = num_ports

        # Create pods and hosts, i.e. aggr and edge layers and hosts, with links
        for pod_number in range(k):
            aggr_switches: list[FattreeNode] = []
            edge_switches: list[FattreeNode] = []
            for switch_id in range(int(k/2)):
                # Create aggr and edge switches per pod
                aggr_switch = FattreeNode(f"10.{pod_number}.{int(switch_id + k/2)}.1", NodeType.SWITCH, FattreeType.AGGREGATE_SWITCH)
                edge_switch = FattreeNode(f"10.{pod_number}.{switch_id}.1", NodeType.SWITCH, FattreeType.EDGE_SWITCH)
                for host_id in range(int(k/2)):
                    # Connect edge switches to hosts/servers
                    server = FattreeNode(f"10.{pod_number}.{switch_id}.{host_id + 2}", NodeType.SERVER, FattreeType.HOST)
                    edge_switch.add_edge(server)
                    self.servers.append(server)
                aggr_switches.append(aggr_switch)
                edge_switches.append(edge_switch)
                self.switches.append(aggr_switch)
                self.switches.append(edge_switch)

            # Add edges between switches in pod (fully connected)
            for aggr_switch in aggr_switches:
                for edge_switch in edge_switches:
                    aggr_switch.add_edge(edge_switch)
            
            pod = self.Pod(aggr_switches, edge_switches)
            self.pods.append(pod)


        # Create core switches
        for host_id in range(int(k/2)):
            for switch_id in range(int(k/2)):
                core_switch = FattreeNode(f"10.{k}.{host_id + 1}.{switch_id + 1}", NodeType.SWITCH, FattreeType.CORE_SWITCH)
                self.core_switches.append(core_switch)
                self.switches.append(core_switch)


        print(f"servers/hosts: {len(self.servers)}")
        print(f"core switches: {len(self.core_switches)}")
            
        # Add edges between core switches and pods (aggr switches)
        for pod in self.pods:
            pod: self.Pod
            core_index = 0
            for aggr_sw in pod.aggr_switches:
                for _ in range(int(self.num_ports/2)):
                    self.core_switches[core_index].add_edge(aggr_sw)
                    core_index += 1

        self._verify()


    def _verify(self):
        """Verify that the implementation is correct. Should be run after running self.generate().
        """
        assert len(self.core_switches) == int(pow((self.num_ports / 2), 2))
        assert len(self.pods) == self.num_ports
        
        for pod in self.pods:
            print(pod)
        
        # Verify per pod
        for pod in self.pods:
            pod: self.Pod
            assert len(pod.aggr_switches) == self.num_ports / 2
            assert len(pod.edge_switches) == self.num_ports / 2

            # Verify per aggregation switch
            for aggr_switch in pod.aggr_switches:
                assert len(aggr_switch.edges) == self.num_ports

                edges_from_aggrsw_to_edgesw = 0
                edges_from_aggrsw_to_coresw = 0
                # Verify per edge
                for edge_i in aggr_switch.edges:
                    edge_i: Edge
                    other_node: FattreeNode = edge_i.lnode if edge_i.lnode.ft_type != FattreeType.AGGREGATE_SWITCH else edge_i.rnode
                    if (other_node.ft_type == FattreeType.CORE_SWITCH):
                        edges_from_aggrsw_to_coresw += 1
                    elif (other_node.ft_type == FattreeType.EDGE_SWITCH):
                        edges_from_aggrsw_to_edgesw += 1

                assert edges_from_aggrsw_to_edgesw == self.num_ports/2
                assert edges_from_aggrsw_to_coresw == self.num_ports/2
            
            # Verify per edge switch
            for edge_switch in pod.edge_switches:
                assert len(edge_switch.edges) == self.num_ports
                
                edges_from_edgesw_to_host = 0
                edges_from_edgesw_to_aggrsw = 0
                # Verify per edge
                for edge_i in edge_switch.edges:
                    edge_i: Edge
                    other_node: FattreeNode = edge_i.lnode if edge_i.lnode.ft_type != FattreeType.EDGE_SWITCH else edge_i.rnode
                    if (other_node.ft_type == FattreeType.AGGREGATE_SWITCH):
                        edges_from_edgesw_to_aggrsw += 1
                    elif (other_node.ft_type == FattreeType.HOST):
                        edges_from_edgesw_to_host += 1

                assert edges_from_edgesw_to_host == self.num_ports/2
                assert edges_from_edgesw_to_aggrsw == self.num_ports/2

        # Verify core switches
        for core_switch in self.core_switches:
            core_switch: FattreeNode
            # Verify that a core switch has k edges
            assert len(core_switch.edges) == self.num_ports
            # Verify that each core switch has one port connected to each of k pods
            for i in range(len(core_switch.edges)):
                for j in range(len(core_switch.edges)):
                    if i == j: continue # do not compare to yourself
                    pod_node_i = core_switch.edges[i].lnode if core_switch.edges[i].lnode.ft_type == FattreeType.AGGREGATE_SWITCH else core_switch.edges[i].rnode
                    pod_node_j = core_switch.edges[j].lnode if core_switch.edges[j].lnode.ft_type == FattreeType.AGGREGATE_SWITCH else core_switch.edges[j].rnode
                    
                    # Only connected to aggregate switches
                    assert pod_node_i.ft_type == FattreeType.AGGREGATE_SWITCH
                    assert pod_node_j.ft_type == FattreeType.AGGREGATE_SWITCH
                    # Compare first two octets of id, e.g. 10.0.x.x or 10.2.x.x. This identifies a pod.
                    pod_id_octets_i = pod_node_i.id.split('.')[0:2]
                    pod_id_octets_j = pod_node_j.id.split('.')[0:2]
                    # print(f"pod_id_octets_i: {pod_id_octets_i}")
                    # print(f"pod_id_octets_j: {pod_id_octets_j}\n")
                    # Each edge of a core switch should have exactly one connection to each pod
                    assert pod_id_octets_i != pod_id_octets_j

        print("Successfully verified Fat-tree topology!")

########################################
######### Command line parsing #########
########################################

parser = argparse.ArgumentParser(description='Create topologies')
parser.add_argument('topology',
                    help='which topology to create, either "fattree" or "f" or "jellyfish" or "j"')
parser.add_argument('--ports', default=8, help="number of ports on a switch")

args = parser.parse_args()
is_fat_tree = args.topology == "f" or args.topology == "fattree"
is_jellyfish = args.topology == "j" or args.topology == "jellyfish"
if (is_fat_tree):
    Fattree(int(args.ports))
elif (is_jellyfish):
    # raise NotImplementedError("Jellyfish is not implemented yet")
    Jellyfish(16, 20, 4)
else:
    raise ValueError(f"Argument {args.topology} is invalid, choose 'fattree' or 'jellyfish' ")
