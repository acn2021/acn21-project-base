/* -*- P4_16 -*- */
#include <core.p4>
#include <v1model.p4>

#define TYPE_IPV4 0x0800

#define PROTOCOL_UDP 0x11

/*************************************************************************
*********************** H E A D E R S  ***********************************
*************************************************************************/

/* define packet headers for Ethernet, IPv4, UDP, and RTP */
typedef bit<9>  egressSpec_t;
typedef bit<48> macAddr_t;
typedef bit<32> ip4Addr_t;

// Define ethernet header (ordered items (bits))
header ethernet_t {
    macAddr_t dstAddr;
    macAddr_t srcAddr;
    bit<16>   etherType;
}

// Define IP header (ordered items (bits))
header ipv4_t {
    /* TODO */
    bit<4> version;
    bit<4> ihl;
    bit<8> diffserv;
    bit<16> totalLen;
    bit<16> identification;
    bit<3> flags;
    bit<13> fragOffset;
    bit<8> ttl;
    bit<8> protocol;
    bit<16> hdrChecksum;
    ip4Addr_t srcAddr;
    ip4Addr_t dstAddr;
}

// Define UDP header
header udp_t {
    bit<16> srcPort;
    bit<16> dstPort;
    bit<16> len;
    bit<16> checksum;
}

// Define RTP header

header rtp_t {
    bit<2> version;
    bit<1> padding;
    bit<1> extension;
    bit<4> csrcCount;
    bit<1> marker;
    bit<7> payloadType;
    bit<16> sequenceNum;
    bit<32> timestamp;
    bit<32> ssrc;
    // bit<32> csrc;
}

struct metadata {
    bit<16> length_without_ip_header;
}

// Define struct with two headers (unordered items)
struct headers {
    ethernet_t ethernet;
    ipv4_t ipv4;
    udp_t udp;
    rtp_t rtp;
}

/*************************************************************************
*********************** P A R S E R  ***********************************
*************************************************************************/

parser MyParser(packet_in packet,
                out headers hdr,
                inout metadata meta,
                inout standard_metadata_t standard_metadata) {

    state start {
        // Go to next state parse_ethernet
        transition parse_ethernet;
    }

    state parse_ethernet {
        // Parse the bits in order according to ethernet_t
        packet.extract(hdr.ethernet);
        // Transition based on the value of the etherType ethernet header field
        transition select(hdr.ethernet.etherType) {
            TYPE_IPV4: parse_ipv4; // if etherType is IPv4, parse it
            default: accept; // else simply accept the header
        }
    }

    state parse_ipv4 {
        // Parse the bits in order according to ipv4_t
        packet.extract(hdr.ipv4);

        // Used in the UDP checksum computation
        meta.length_without_ip_header = hdr.ipv4.totalLen - 16w20;

        transition select(hdr.ipv4.protocol) {
            0x11: parse_udp; // if udp, parse it
            // PROTOCOL_UDP: parse_udp;
            default: accept; // else simply accept the header
        }
    }

    state parse_udp {
        packet.extract(hdr.udp);
        transition parse_rtp;
    }

    state parse_rtp {
        packet.extract(hdr.rtp);
        transition accept;
    }
}

/*************************************************************************
************   C H E C K S U M    V E R I F I C A T I O N   *************
*************************************************************************/

control MyVerifyChecksum(inout headers hdr, inout metadata meta) {   
    apply {
        // docs @ https://github.com/p4lang/p4c/blob/37cd30ee9dc79c65b057a1aa168b961d7aba4701/p4include/v1model.p4#L461-L505
        verify_checksum(
            hdr.ipv4.isValid(), 
            {
                hdr.ipv4.version,
                hdr.ipv4.ihl,
                hdr.ipv4.diffserv,
                hdr.ipv4.totalLen,
                hdr.ipv4.identification,
                hdr.ipv4.flags,
                hdr.ipv4.fragOffset,
                hdr.ipv4.ttl,
                hdr.ipv4.protocol,
                hdr.ipv4.srcAddr,
                hdr.ipv4.dstAddr 
            },            
            hdr.ipv4.hdrChecksum, 
            HashAlgorithm.csum16
        );
    }
}


/*************************************************************************
**************  I N G R E S S   P R O C E S S I N G   *******************
*************************************************************************/

control MyIngress(inout headers hdr,
                  inout metadata meta,
                  inout standard_metadata_t standard_metadata) {

    action drop() {
        mark_to_drop(standard_metadata);
    }
    
    /**
    dstAddr:    MAC address of the next hop
    port:       egress port of the next hop
    */
    action ipv4_forward(macAddr_t dstAddr, egressSpec_t port) {
        // dstAddr and port are coming from the forwarding table

        // Set egress port for next hop
        standard_metadata.egress_spec = port;

        // Update ethernet header dest addr with addr of next hop
        hdr.ethernet.dstAddr = dstAddr;

        // Update ethernet header src addr with addr of current switch
        // (i.e. destination of old header will be src of new)
        hdr.ethernet.srcAddr = hdr.ethernet.dstAddr; 

        // decrement TTL by 1
        hdr.ipv4.ttl = hdr.ipv4.ttl - 1;
    }

    // Multicast to group 1, which is defined in s2 and s3-runtime.json
    action multicast() {
        standard_metadata.mcast_grp = 1;
    }

    table debug {
        key = {
            standard_metadata.egress_spec : exact;
            hdr.ipv4.dstAddr : exact;
        }
        actions = { }
    }

    table ipv4_lpm {
        key = {
            hdr.ipv4.dstAddr: lpm; // from core.p4
        }
        actions = {
            ipv4_forward;
            multicast;
            drop;
            NoAction; // from core.p4
        }
        size = 1024;
        default_action = drop();
    }
    
    apply {
        if (hdr.ipv4.isValid()) {
            debug.apply();
            ipv4_lpm.apply();
        }
        if (hdr.udp.isValid()) {
            // Set checksum to 0 (ignore it), since we cannot manage
            // to correctly recompute the UDP checksum, unfortunately..
            hdr.udp.checksum = 0;
        }
    }
}

/*************************************************************************
****************  E G R E S S   P R O C E S S I N G   *******************
*************************************************************************/

control MyEgress(inout headers hdr,
                 inout metadata meta,
                 inout standard_metadata_t standard_metadata) {

    apply {
        // Prune multicast packet to ingress port to preventing loop
        if (standard_metadata.egress_port == standard_metadata.ingress_port) {
            mark_to_drop(standard_metadata);
        }
        if (standard_metadata.egress_port == 3 && standard_metadata.mcast_grp == 1) {
            // Assume we are in s2 and sending to h3 via s3 by multicast
            
            // Rewrite destination ip and mac, so the packet does not get dropped by h3
            hdr.ipv4.dstAddr = 0xA000303; // = 10.0.3.3 (h3) in hex
            hdr.ethernet.dstAddr = 0x080000000333; // = 08:00:00:00:03:00 (s3) in hex
        }
    }
}

/*************************************************************************
*************   C H E C K S U M    C O M P U T A T I O N   **************
*************************************************************************/

control MyComputeChecksum(inout headers hdr, inout metadata meta) {
    apply {
        // docs @ https://github.com/p4lang/p4c/blob/37cd30ee9dc79c65b057a1aa168b961d7aba4701/p4include/v1model.p4#L461-L505
        // Update the IP checksum
        update_checksum(
            hdr.ipv4.isValid(),
            {
                hdr.ipv4.version,
                hdr.ipv4.ihl,
                hdr.ipv4.diffserv,
                hdr.ipv4.totalLen,
                hdr.ipv4.identification,
                hdr.ipv4.flags,
                hdr.ipv4.fragOffset,
                hdr.ipv4.ttl,
                hdr.ipv4.protocol,
                hdr.ipv4.srcAddr,
                hdr.ipv4.dstAddr 
            },
            hdr.ipv4.hdrChecksum,
            HashAlgorithm.csum16
        );

        // TODO: Correctly recompute the UDP checksum
        // The field `meta.length_without_ip_header` is probably not correct?

        // Update the UDP checksum, including payload
        // update_checksum_with_payload(
        //     hdr.udp.isValid(),
        //     {
        //         // IP pseudo header
        //         hdr.ipv4.srcAddr,
        //         hdr.ipv4.dstAddr,
        //         8w0,
        //         hdr.ipv4.protocol,
        //         meta.length_without_ip_header, // not sure if correct
        //         // UDP header
        //         hdr.udp.srcPort,
        //         hdr.udp.dstPort,
        //         hdr.udp.len
        //     },
        //     hdr.udp.checksum,
        //     HashAlgorithm.csum16
        // );
    }
}

/*************************************************************************
***********************  D E P A R S E R  *******************************
*************************************************************************/

control MyDeparser(packet_out packet, in headers hdr) {
    apply {
        packet.emit(hdr.ethernet);
        packet.emit(hdr.ipv4);
        packet.emit(hdr.udp);
        packet.emit(hdr.rtp);
    }
}

/*************************************************************************
***********************  S W I T C H  *******************************
*************************************************************************/

V1Switch(
    MyParser(),
    MyVerifyChecksum(),
    MyIngress(),
    MyEgress(),
    MyComputeChecksum(),
    MyDeparser()
) main;
