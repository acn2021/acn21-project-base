# Copyright 2021 Lin Wang

# This code is part of the Advanced Computer Networks course at VU 
# Amsterdam.

# Licensed under the Apache License, Version 2.0 (the "License"); you may not
# use this file except in compliance with the License. You may obtain a copy
# of the License at
#   http://www.apache.org/licenses/LICENSE-2.0
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

#!/usr/bin/env python3

# A dirty workaround to import topo.py from lab2

import os
import subprocess
import time
from id_mapping import IDMapping

import mininet
import mininet.clean
from mininet.net import Mininet
from mininet.cli import CLI
from mininet.log import lg, info
from mininet.link import TCLink
from mininet.node import Node, OVSKernelSwitch, RemoteController
from mininet.topo import Topo
from mininet.util import waitListening, custom

import topo

class FattreeNet(Topo):
    """
    Create a fat-tree network in Mininet
    """

    def __init__(self, ft_topo):
        
        Topo.__init__(self)

        # TODO: please complete the network generation logic here
        BANDWIDTH = "15"
        LATENCY = "5ms"
        self.topo = ft_topo
        self.id_mapping = IDMapping(self.topo)

        self._create_topology(BANDWIDTH, LATENCY)

    def _create_topology(self, link_bw, link_delay):
        """Converts self.topo into a Mininet topology, by adding topo.servers, topo.switches
        and the edges per switch using the Mininet API.

        Args:
            link_bw (str): the bandwidth of each link, e.g. "15"
            link_delay (str): the delay/latency of each link, e.g. "5ms
        """
        print("^^^^^^^^^^^^^^^^^ Setting up the topology ^^^^^^^^^^^^^^")

        # Add hosts
        for server in self.topo.servers:
            mininet_server_id = self.id_mapping.get_mininet_id(server.id) # h1, h2, h3, .. h15
            self.addHost(mininet_server_id)

        links_to_add = []
        for switch in self.topo.switches:
            # Add switch
            mininet_switch_id = self.id_mapping.get_mininet_id(switch.id) # s16, s17, .. s35

            self.addSwitch(mininet_switch_id)

            """ Add links to intermediate `links_to_add` list, so we can first add 
            all switches and check on duplicate links and to avoid errors being 
            thrown on attempting to create links on switches that are not added via `addSwitch` yet.
            """
            for edge in switch.edges:
                other_node = edge.lnode if switch.id != edge.lnode.id else edge.rnode
                
                if other_node == switch: # links with self, ignore
                    continue

                # Ensure that no duplicate links are added, but in reverse order
                # e.g. (1, 2) and (2, 1) should not both be added
                if other_node.id < switch.id:
                    first_node_ip = other_node.id 
                    second_node_ip = switch.id
                else:
                    first_node_ip = switch.id
                    second_node_ip = other_node.id

                to_add = (first_node_ip, second_node_ip)

                if to_add not in links_to_add:
                    links_to_add.append(to_add)

        print(self.id_mapping)

        # Now that all hosts and switches are added to the topo, add links 
        # from `links_to_add` to the mininet topo links
        for link in links_to_add:
            print("link:")
            print(link)
            mininet_node_id_1 = self.id_mapping.get_mininet_id(link[0]) # e.g. h0, s16
            mininet_node_id_2 = self.id_mapping.get_mininet_id(link[1]) # e.g. h0, s16
            self.addLink(
                node1=mininet_node_id_1,
                node2=mininet_node_id_2,
                bw=link_bw,
                delay=link_delay
            )


    """ Example pair input
        link:
        ('10.0.0.1', '10.0.2.1')
        link:
        ('10.0.1.1', '10.0.2.1')
        link:
        ('10.0.2.1', '10.4.1.1')
        link:
        ('10.0.2.1', '10.4.1.2')
        link:
        ('10.0.0.1', '10.0.0.2')
        link:
        ('10.0.0.1', '10.0.0.3')
    """
    def _determine_ports(self, node_id_1, node_id_2):
        pass


def make_mininet_instance(graph_topo):

    net_topo = FattreeNet(graph_topo)

    net = Mininet(topo=net_topo, controller=None, autoSetMacs=True)
    net.addController('c0', controller=RemoteController, ip="127.0.0.1", port=6653)
    return net


def run(graph_topo):
    
    # Run the Mininet CLI with a given topology
    lg.setLogLevel('info')
    mininet.clean.cleanup()
    net = make_mininet_instance(graph_topo)

    info('*** Starting network ***\n')
    net.start()
    info('*** Running CLI ***\n')
    CLI(net)
    info('*** Stopping network ***\n')
    net.stop()


ft_topo = topo.Fattree(4)
run(ft_topo)
