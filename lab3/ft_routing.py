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
        self.switch_routing_tables = SwitchRoutingTables(4)


    # Topology discovery
    @set_ev_cls(event.EventSwitchEnter)
    def get_topology_data(self, ev):
        super().get_topology_data(ev)
        # links = [(link.src.dpid, link.dst.dpid, {'port': link.src.port_no}) for link in get_link(self, None)]
        # links = []
        self.switch_routing_tables.sync_ports(self.raw_links, self.id_mapping)


    # @override
    def get_port_of_next_hop(self, dst, src_dpid, dst_dpid):
        src_node_id = self.id_mapping.get_node_id_from_dpid(src_dpid)
        dst_node_id = self.id_mapping.get_node_id_from_dpid(dst_dpid)

        self.switch_routing_tables.prefix_tables[src_node_id]
        
        port_of_next_hop = self.switch_routing_tables.lookup_port(src_node_id, dst_node_id)

        return port_of_next_hop
        print(f"Port for next hop: {port}")
        next_hop_dpid = self._get_neighbor_by_port(src_dpid, port)
        return self.id_mapping.get_dpid(next_hop_dpid)

    def _get_neighbor_by_port(self, src_dpid, port):
        print(f"src_dpid {src_dpid}")
        print(f"port: {port}")
        for link in self.raw_links:
            print(link)
            if link[0] == src_dpid and link[2]['port'] == port:
                print(f"result + {link[1]}")
                return link[1]
        # Get fattree node ids
        # src_node_id = self.id_mapper.get_node_id_from_dpid(src_dpid)
        # dst_node_id = self.id_mapper.get_node_id_from_dpid(dst_dpid)

        # src_octets = src_node_id.split(".")
        # dst_octets = dst_node_id.split(".")

        # # Routing for core switch on /16 prefix
        # is_core_switch = src_octets[1] == 4
        # if (is_core_switch):
        #     for (other_dpid, port_no) in self.raw_links[src_dpid]:
        #         # match outgoing link dpid to /16 prefix
        #         other_node_id = self.id_mapper.get_node_id_from_dpid(other_dpid)
        #         other_octets = other_node_id.split(".")
        #         if (dst_octets[1] == other_node_id[1]): # [1] is the second octet, i.e. /16 prefix
        #             return other_dpid
        # else:
        #     pass
        

