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

#!/usr/bin/env python3

from typing import Dict, List
from sp_routing import SPRouter

import topo
from id_mapping import IDMapping
from address import Address
from switch_routing_tables import SwitchRoutingTables
from ryu.topology.api import get_link
from ryu.controller.handler import set_ev_cls
from typing import Optional
from ryu.base import app_manager
from ryu.controller import mac_to_port
from ryu.controller import ofp_event
from ryu.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.ofproto import ofproto_v1_3
from ryu.lib.mac import haddr_to_bin
from ryu.lib.packet import packet, ethernet, ether_types
from ryu.lib.packet import ipv4
from ryu.lib.packet import arp

from ryu.topology import event, switches
from ryu.topology.api import get_switch, get_link
from ryu.app.wsgi import ControllerBase


class FTRouter(SPRouter):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    # Topology discovery
    @set_ev_cls(event.EventSwitchEnter)
    def get_topology_data(self, ev):
        super().get_topology_data(ev)
        if (self.initialized):
            self.switch_routing_tables = SwitchRoutingTables(4, self.raw_links, self.id_mapping)

    # @override
    def get_port_of_next_hop(self, dst_ip, src_dpid, dst_dpid):
        """[summary]

        Args:
            dst ([type]): [description]
            src_dpid ([type]): switch dpid, e.g. 17, 21
            dst_dpid ([type]): switch dpid, e.g. 21, 17

        Returns:
            [type]: [description]
        """

        # Check if we can route directly to host
        path_to_host = self.ipv4_dests.get(dst_ip)
        if (path_to_host):
            edge_switch_dpid = path_to_host[0]
            at_correct_edge_switch = edge_switch_dpid == src_dpid
            if (at_correct_edge_switch):
                return path_to_host[1]

        # Otherwise use fat tree routing
        src_node_id = self.id_mapping.get_node_id_from_dpid(src_dpid)
        dst_host_node_id = self.id_mapping.get_node_id_from_ip(dst_ip)
        port_of_next_hop = self.switch_routing_tables.lookup_port(src_node_id, dst_host_node_id)
        
        # self.print_hop(src_dpid, dst_dpid, src_node_id, dst_host_node_id, port_of_next_hop)
        return port_of_next_hop

    def print_hop(self, src_dpid, dst_dpid, src_node_id, dst_host_node_id, port_of_next_hop):
        print("\n-----------HOP------------")

        print("self.ipv4_dests:")
        print(self.ipv4_dests)

        print(f"*** Routing table for {src_node_id}")
        for row in self.switch_routing_tables.prefix_tables[src_node_id]:
            print(f"prefix: {row['prefix']}  - port: {row['port']}")
            print("suffix table:", row['suffix_table'])
            print("***")
        print(f"""
        FROM:
            dpid:\t{src_dpid}
            node_id:\t{src_node_id}
        TO SWITCH:
            dpid:\t{dst_dpid}
        EVENTUAL HOST:
            node_id:\t{dst_host_node_id}
        THROUGH PORT:
            port:\t{port_of_next_hop}
        """)
        print("-----------END HOP------------")
