# Copyright 2020 Lin Wang

# This code is part of the Advanced Computer Networks (2020) course at Vrije 
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

from kruskal import kruskal

import topo
from id_mapping import IDMapping

class SPRouter(app_manager.RyuApp):

    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]
    NUMBER_OF_PORTS_PER_SWITCH = 4

    def __init__(self, *args, **kwargs):
        super(SPRouter, self).__init__(*args, **kwargs)
        self.topo_net = topo.Fattree(self.NUMBER_OF_PORTS_PER_SWITCH)
        self.mac_to_port = {}
        self.flood_ports_switches = dict()
        self.initialized = False
        self.edge_switches = []
        self.ipv4_dests = dict()
        self.custom_topo = None
        self.raw_links = []
        self.id_mapping = IDMapping(self.topo_net)

    # Topology discovery
    @set_ev_cls(event.EventSwitchEnter)
    def get_topology_data(self, ev):

        # Switches and links in the network
        switches = get_switch(self, None)
        links = get_link(self, None)
        switches = [switch.dp.id for switch in switches]
        links = [(link.src.dpid, link.dst.dpid, {'port': link.src.port_no}) for link in links]
        self.raw_links = links

        num_edge_links = self.topo_net.num_ports**2
        total_num_ports = self.topo_net.num_ports * len(self.topo_net.switches)
        has_required_number_of_links = (len(links) == total_num_ports - num_edge_links)

        if self.initialized or not has_required_number_of_links:
            return

        def find_edge_switches(switches, links):
            edge_switches = []
            for switch in switches:
                occupied_ports = []
                outgoing = 0
                for link in links:
                    if link[0] == switch:
                        outgoing += 1
                        occupied_ports.append(link[2]["port"])
                if outgoing == int(self.topo_net.num_ports/2):
                    edge_switches.append((switch, occupied_ports.copy()))
                occupied_ports.clear()
            return edge_switches

        self.edge_switches = find_edge_switches(switches, links)

        def add_edges_to_mst(mst):
            self.custom_topo = topo.MininetTopology(switches, links)
            extra_edges = []
            for edge in links:
                for other in mst:
                    a, b, _ = edge
                    c, d, _ = other
                    if (a,b) == (d, c):
                        extra_edges.append(edge)
            return mst + extra_edges

        # Get Minimal Spanning Tree
        mst = kruskal(switches, links)
        mst = add_edges_to_mst(mst)
            
        # mst will be used for flooding, not the full network. Not forgetting edge-switches.

        # Initializing the flooding of the ports.
        for switch in switches:
            self.flood_ports_switches[str(switch)] = []
        
        for edge in mst:
            self.flood_ports_switches[str(edge[0])].append(edge[2])
        
        # Find open ports in the edge-switches to also flood.
        for pair in self.edge_switches:
            switch, ports_used = pair
            for i in range(1, self.topo_net.num_ports+1):
                if i not in ports_used and {'port': i} not in self.flood_ports_switches[str(switch)]:
                    self.flood_ports_switches[str(switch)].append({'port': i})

        self.initialized = True
        # for link in self.raw_links:
        #     src_node_id = self.id_mapping.get_node_id_from_dpid(link[0])
        #     dst_node_id = self.id_mapping.get_node_id_from_dpid(link[1])
        #     port = link[2]['port']
        #     print(f"src: {src_node_id} - dst: {dst_node_id} - port: {port}")
        print("Controller initialized")

    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def switch_features_handler(self, ev):
        datapath = ev.msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        # Install entry-miss flow entry
        match = parser.OFPMatch()
        actions = [parser.OFPActionOutput(ofproto.OFPP_CONTROLLER,
                                          ofproto.OFPCML_NO_BUFFER)]
        self.add_flow(datapath, 0, match, actions)

    def get_next_hop_dpid(self, src_dpid: str, dst_dpid: str) -> Optional[int]:
        """Obtain a path (in this cast using a shortest path algorithm) from 
        the source dpid to the destination dpid.

        Args:
            src_dpid (str): dpid of source
            dst_dpid (str): dpid of destination

        Returns:
            [type]: [description]
        """
        path = self._construct_shortest_path(src_dpid, dst_dpid)
        print("path:")
        print(path)
        if len(path) == 0:
            return None
        return path[1]

    def _get_flooding_ports(self, dpid, port_in):
        flood_ports = []
        raw = self.flood_ports_switches[str(dpid)]
        for port in raw:
            flood_ports.append(port["port"])
        if port_in in flood_ports:
            flood_ports.remove(port_in)
        return flood_ports

    def _construct_shortest_path(self, src_dpid, dst_dpid):
        """Path as list of ids to follow
        """
        if src_dpid == dst_dpid:
            return []
        src = None
        dst = None
        for switch in self.custom_topo.switches:
            if switch.id == src_dpid:
                src = switch
            if switch.id == dst_dpid:
                dst = switch
        tp = topo.Paths(self.custom_topo)
        path = tp.construct_path(src, dst)
        path = [x.id for x in path]
        return path

    # Add a flow entry to the flow-table
    def add_flow(self, datapath, priority, match, actions):
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        # Construct flow_mod message and send it
        inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS, actions)]
        mod = parser.OFPFlowMod(datapath=datapath, priority=priority,
                                match=match, instructions=inst)
        datapath.send_msg(mod)

    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def _packet_in_handler(self, ev):
        msg = ev.msg
        datapath = msg.datapath
        dpid = datapath.id
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        in_port = msg.match['in_port']

        pkt = packet.Packet(msg.data)
        eth = pkt.get_protocols(ethernet.ethernet)[0]

        dst_ip = eth.dst
        src = eth.src

        dpid = datapath.id
        self.mac_to_port.setdefault(dpid, {})

        # Parsing the data into a packet
        pkt = packet.Packet(msg.data)

        # Whether request/response is ARP or IP
        arp_pkt = pkt.get_protocol(arp.arp)
        ip_pkt = pkt.get_protocol(ipv4.ipv4)

        # LLDP protocol for the Ryu controller, a.k.a. not needed
        if not arp_pkt and not ip_pkt or eth.ethertype == ether_types.ETH_TYPE_LLDP:
            return

        if arp_pkt:
            src = arp_pkt.src_ip
            dst_ip = arp_pkt.dst_ip
        else:
            src = ip_pkt.src
            dst_ip = ip_pkt.dst

        print(f"FROM: {src} TO: {dst_ip}")

        ##### Shortest Path Routing #####

        # Add to IP table
        if not src in self.ipv4_dests:
            self.ipv4_dests[src] = (dpid, in_port)
        
        # Find next switch to be reached and add to flowtable of the switch
        destination_can_be_reached = dst_ip in self.ipv4_dests
        if destination_can_be_reached: # Can reach destination
            # Calculate path between dpids
            src_dpid = dpid
            dst_dpid = self.ipv4_dests[dst_ip][0]

            out_port = self.get_port_of_next_hop(dst_ip, src_dpid, dst_dpid)

            # Add flow from src IP to dst IP when at this switch
            match = parser.OFPMatch(in_port=in_port, ipv4_dst=dst_ip, ipv4_src=src)
            actions = [parser.OFPActionOutput(out_port)]
            print(f"Adding flow, dst: {dst_ip} - src: {src} - in_port: {in_port} - out_port: {out_port}")
            self.add_flow(datapath, 1, match, actions)

            data = msg.data
            out = parser.OFPPacketOut(datapath=datapath, buffer_id=msg.buffer_id,
                                  in_port=in_port, actions=actions, data=data)
            datapath.send_msg(out) 
            return
        else:
            ##### Flooding using mst (Minimal Spanning Tree) #####
            
            # Do flooding 
            actions = []
            out_ports = self._get_flooding_ports(dpid, in_port)
            for port in out_ports:
                # print(f"flood_port for sw {dpid}: {port}")
                actions.append(parser.OFPActionOutput(port))

            match = parser.OFPMatch(in_port=in_port, ipv4_dst=dst_ip, ipv4_src=src)
        
            data = None
            if msg.buffer_id == ofproto.OFP_NO_BUFFER:
                data = msg.data

            out = parser.OFPPacketOut(datapath=datapath, buffer_id=msg.buffer_id,
                                    in_port=in_port, actions=actions, data=data)
            datapath.send_msg(out)

    def get_port_of_next_hop(self, dst_ip, src_dpid, dst_dpid):
        next_hop_dpid = self.get_next_hop_dpid(src_dpid, dst_dpid)
        
        src_node_id = self.id_mapping.get_node_id_from_dpid(src_dpid)
        dst_node_id = self.id_mapping.get_node_id_from_dpid(dst_dpid)

        # Determine out_port
        if next_hop_dpid is None:
                # At destination switch, do lookup of port to destination IP/server
            out_port = self.ipv4_dests[dst_ip][1]
        else:
                # Not at destination switch yet, find port of next hop
            dst_dpid = next_hop_dpid
            out_port = self._get_out_port(src_dpid, dst_dpid)

        print(f"next hop from sw {src_node_id} to sw {dst_node_id} via port {out_port}")
        return out_port


    def _get_out_port(self, src_dpid, dst_dpid):
        """Returns the port in src_dpid that leads to dst_dpid
        """
        for link in self.raw_links:
            if link[0] == src_dpid and link[1] == dst_dpid:
                return link[2]['port']