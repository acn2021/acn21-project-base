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

import copy
from datetime import datetime
from typing import Optional

from ryu.app.wsgi import ControllerBase
from ryu.base import app_manager
from ryu.controller import mac_to_port, ofp_event
from ryu.controller.handler import (CONFIG_DISPATCHER, DEAD_DISPATCHER,
                                    MAIN_DISPATCHER, set_ev_cls)
from ryu.lib.mac import haddr_to_bin
from ryu.lib.packet import arp, ether_types, ethernet, ipv4, packet
from ryu.ofproto import ofproto_v1_3
from ryu.topology import event, switches
from ryu.topology.api import get_link, get_switch

import topo
from id_mapping import IDMapping
from dijkstra import dijkstra


class SPRouter(app_manager.RyuApp):

    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

    def __init__(self, *args, **kwargs):
        super(SPRouter, self).__init__(*args, **kwargs)
        self.topo_net = topo.Fattree(4)
        self.id_mapping = IDMapping(self.topo_net)
        self.mac_to_port = {}

    # Topology discovery
    @set_ev_cls(event.EventSwitchEnter)
    def get_topology_data(self, ev):
        # print("*** Switch has entered topo, running get_topology_data()")

        # Switches and links in the network
        # switches = get_switch(self, None)
        # links = get_link(self, None)

        # The Function get_switch(self, None) outputs the list of switches.
        self.topo_raw_switches = copy.copy(get_switch(self, None))
        # The Function get_link(self, None) outputs the list of links.
        self.topo_raw_links = copy.copy(get_link(self, None))

        # print(" \t" + f"Current Links ({len(self.topo_raw_links)}):")
        # for l in self.topo_raw_links:
        #     print (" \t\t" + str(l))

        # print(" \t" + f"Current Switches ({len(self.topo_raw_switches)}):")
        # for s in self.topo_raw_switches:
        #     print (" \t\t" + str(s))

        switches = [switch.dp.id for switch in self.topo_raw_switches]
        links = [(link.src.dpid, link.dst.dpid, {'port': link.src.port_no}) for link in self.topo_raw_links]
        for sl in switches + links:
            print(sl)


    """
    This event is fired when a switch leaves the topo. i.e. fails.
    """
    @set_ev_cls(event.EventSwitchLeave, [MAIN_DISPATCHER, CONFIG_DISPATCHER, DEAD_DISPATCHER])
    def handler_switch_leave(self, ev):
        print("Switch left topo.")

    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def switch_features_handler(self, ev):
        # print("switch_features_handler called from event: ofp_event.EventOFPSwitchFeatures")
        datapath = ev.msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        # Install entry-miss flow entry
        match = parser.OFPMatch()
        actions = [parser.OFPActionOutput(ofproto.OFPP_CONTROLLER,
                                          ofproto.OFPCML_NO_BUFFER)]
        self.add_flow(datapath, 0, match, actions)

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
        if ev.msg.msg_len < ev.msg.total_len:
            self.logger.debug("packet truncated: only %s of %s bytes",
                              ev.msg.msg_len, ev.msg.total_len)
        msg = ev.msg
        datapath = msg.datapath
        dpid = datapath.id
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        # TODO: handle new packets at the controller

        in_port = msg.match['in_port']

        pkt = packet.Packet(msg.data)
        eth = pkt.get_protocols(ethernet.ethernet)[0]

        if eth.ethertype == ether_types.ETH_TYPE_LLDP:
            # ignore lldp packet
            return

        dst = eth.dst
        src = eth.src

        # If IPv6 multicast, ignore packet
        if (dst.startswith("33:33")):
            return

        

        # *** Algorithm
        # Optional caching:
        # - Check if dijkstra (shorest paths to all nodes) has already been calculated for this switch
        #   - If not, calculate dijkstra (shortest path from this switch to all other nodes)
        
        # - Ping h0 to h1
        # - Not known? ARP is flooded
        # - ARP reply sent by correct host to its neighbor switch. This switch should use
        #  Dijkstra to reach the requesting host h0.
        # - Get the path to the destination from dijkstra
        # - Obtain the next hop
        # - Forward packet to next hop, repeat 
        # - Install flow entry from src to dst mac over the right port

        # *** ARP to obtain IP for hosts
        """
        1. When I do `mininet $ h0 ping h1`, an ARP request is sent to the edge switch. 
        2. This switch broadcasts the ARP request. h1 then replies to its edge switch (the same as the edge switch
        of h0) with its MAC address and IP.
        3. The switch should now forward this ARP reply to the ARP request sender (h0).
        """

        original_dpid = dpid
        dpid = format(datapath.id, "d").zfill(16)
        self.mac_to_port.setdefault(dpid, {})

        # print(
        #     f"{SPRouter.get_time()} - Packet:"
        #     + f"\n\tARP?: {'true' if (eth.ethertype == ether_types.ETH_TYPE_ARP) else 'false'}"
        #     + f"\n\tIP packet - switch: {dpid} ({self.id_mapping.get_node_id(dpid)}) src: {src} dst: {dst} in_port: {in_port}"
        # )

        # Calc dijkstra
        # graph = self.topo_net.servers + self.topo_net.switches
        
        # print(f"dst: {dst}")
        # address_of_dst = self.id_mapping.get_node_id(dst)
        # print(f"address of dst: {address_of_dst}")
        
        # this_switch = self._get_node(dpid)
        # shortest_paths = dijkstra(graph, this_switch)
        # print("shortest paths:")
        # print(shortest_paths)
        # print(self.mac_to_port)

        # # If incoming frame is ARP, instead of IP, simply flood
        if eth.ethertype == ether_types.ETH_TYPE_ARP:
            out_port = self._handle_arp_packet(dpid, pkt, src, dst, in_port, original_dpid, ofproto)
        else:
            out_port = self._handle_packet(dpid, src, dst, in_port)
        
        if out_port is None: # Do not forward packet
            return

        actions = [parser.OFPActionOutput(out_port)]

        # install a flow to avoid packet_in next time
        if out_port != ofproto.OFPP_FLOOD:
            match = parser.OFPMatch(in_port=in_port, eth_dst=dst)
            # verify if we have a valid buffer_id, if yes avoid to send both
            # flow_mod & packet_out
            if msg.buffer_id != ofproto.OFP_NO_BUFFER:
                self.add_flow(datapath, 1, match, actions, msg.buffer_id)
                return
            else:
                self.add_flow(datapath, 1, match, actions)
            print(f"Added flow in_port|dst_mac->out_port = {in_port}|{dst}->{out_port}")
        data = None
        if msg.buffer_id == ofproto.OFP_NO_BUFFER:
            data = msg.data

        out = parser.OFPPacketOut(datapath=datapath, buffer_id=msg.buffer_id,
                                  in_port=in_port, actions=actions, data=data)
        datapath.send_msg(out)

    def _handle_packet(self, dpid, src, dst, in_port):
        # learn a mac address to avoid FLOOD next time.
        self.mac_to_port[dpid][src] = in_port
            # self.logger.info("IP packet in \tsw: %s src: %s dst: %s in_port: %s", dpid, src, dst, in_port)
        if dst in self.mac_to_port[dpid]:
            print(f"(switch: {dpid}) dst {dst} that is in mac_to_port with port {in_port}")
            out_port = self.mac_to_port[dpid][dst]
        else:
                # print("unknown dst, flooding..")
            # out_port = ofproto.OFPP_FLOOD
            out_port = None
        return out_port

    def _handle_arp_packet(self, dpid, pkt, src, dst, in_port, original_dpid, ofproto):
        # print("ARP packet discovered, flooding..")
        
        # Assume arp request
        # if (dst == "ff:ff:ff:ff:ff:ff"):
        #     # out_port = ofproto.OFPP_FLOOD

        #     # Store mac to port mapping
        #     self.mac_to_port[dpid][src] = in_port

        #     # We should never flood on ARPs, because of loops in the topo. 
        #     # We do not need to flood though since we have get_links and dijkstra for discovery.

        #     # Get out port from dijkstra
        #     pkt_arp = pkt.get_protocol(arp.arp)

        #     ip_of_requestor = pkt_arp.src_ip
        #     node_id_of_requestor = self.id_mapping.get_node_id_from_ip(ip_of_requestor)
        #     next_hop = self._get_next_hop_to_dest(original_dpid, node_id_of_requestor)
        #     next_hop_dpid = self.id_mapping.get_dpid(next_hop['node'].id)
        #     port = self._find_port_of_next_hop(original_dpid, next_hop_dpid)

        #     out_port = port or ofproto.OFPP_FLOOD
        # else: # ARP is reply
        #     # Get target IP
        #     pkt_arp = pkt.get_protocol(arp.arp)
        #     print(pkt_arp.__dict__)
        #     if (pkt_arp.opcode == 2): # Verify it is indeed an ARP reply
        #         ip_of_requestor = pkt_arp.src_ip # get IP of host that did ARP request
        #         # mac_of_requestor = pkt_arp.src_mac # get IP of host that did ARP request
        #         node_id_of_requestor = self.id_mapping.get_node_id_from_ip(ip_of_requestor)
                
        #         next_hop = self._get_next_hop_to_dest(original_dpid, node_id_of_requestor)


        #         print(f"next hop node id: {next_hop['node'].id} "
        #             + f"- next hop ip: {self.id_mapping.get_ip(next_hop['node'].id)}")
        #         next_hop_dpid = self.id_mapping.get_dpid(next_hop['node'].id)
        #         # Find port of next hop
        #         port = self._find_port_of_next_hop(original_dpid, next_hop_dpid)

        # out_port = ofproto.OFPP_FLOOD

        # Store mac to port mapping
        self.mac_to_port[dpid][src] = in_port

        # *** A note of ARP flooding:
        # We should never completely flood on ARPs, because of loops in the topo.
        # We can however flood on an edge node that has an ARP packet incoming from the pod.
        # We do not need to flood on the rest of the net,since we have get_links and dijkstra for discovery.

        ip_of_requestor = pkt.get_protocol(arp.arp).src_ip
        node_id_of_requestor = self.id_mapping.get_node_id_from_ip(ip_of_requestor)
        next_hop = self._get_next_hop_to_dest(original_dpid, node_id_of_requestor)
        next_hop_dpid = self.id_mapping.get_dpid(next_hop['node'].id)
        port = self._find_port_of_next_hop(original_dpid, next_hop_dpid)

        out_port = port or ofproto.OFPP_FLOOD
        return out_port

    def _get_next_hop_to_dest(self, dpid_of_this_switch: str, destination_node_id: str) -> dict:
        graph = self.topo_net.servers + self.topo_net.switches
        this_switch = self._get_node(dpid_of_this_switch)
        shortest_paths = dijkstra(graph, this_switch)
        return shortest_paths[destination_node_id]

    def _find_port_of_next_hop(self, src_dpid, dst_dpid) -> Optional[int]:
        # links = [(link.src.dpid, link.dst.dpid, {'port': link.src.port_no}) for link in self.topo_raw_links]
        
        # If link is between switches
        for link in self.topo_raw_links:
            is_correct_src = link.src.dpid == src_dpid
            is_correct_dst = link.dst.dpid == dst_dpid
            if (is_correct_src and is_correct_dst):
                print(f"_find_port_of_next_hop link found:")
                return link.src.port_no

        # If link is between switch and server and it exists in mac_to_port
        x = self.mac_to_port.get(src_dpid)
        out_port = x and x.get(dst_dpid)
        if (out_port):
            return out_port

        src_node_id = self.id_mapping.get_node_id_from_dpid(src_dpid)
        dst_node_id = self.id_mapping.get_node_id_from_dpid(dst_dpid)
        print("Could not find a link from src_dpid:"
        + f"{src_dpid} (node_id:{src_node_id}) to dst_dpid {dst_dpid} (node_id:{dst_node_id})")
        return None

    def _get_node(self, dpid):
        node_id = self.id_mapping.get_node_id_from_dpid(dpid)
        for s in self.topo_net.servers + self.topo_net.switches:
            # print(f"s.id: {s.id} - node_id: {node_id}")
            if (s.id == node_id):
                # print(f"found node: {s.id}")
                return s
        raise Exception(f"Node not found for dpid {dpid}.")

    @staticmethod
    def get_time():
        now = datetime.now()

        current_time = now.strftime("%H:%M:%S")
        return current_time
