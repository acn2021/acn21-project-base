/* -*- P4_16 -*- */
#include <core.p4>
#include <v1model.p4>

const bit<16> TYPE_IPV4 = 0x800;

/*************************************************************************
*********************** H E A D E R S  ***********************************
*************************************************************************/

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

struct metadata {
    /* empty */
}

// Define struct with two headers (unordered items)
struct headers {
    /* TODO */
    ethernet_t ethernet;
    ipv4_t ipv4;
}

/*************************************************************************
*********************** P A R S E R  ***********************************
*************************************************************************/

parser MyParser(packet_in packet, // The incoming packet
                out headers hdr, // The headers defined above as a struct
                inout metadata meta,
                inout standard_metadata_t standard_metadata) {

    state start {
        // Go to next state parse_ethernet
        transition parse_ethernet;
    }

    state parse_ethernet {
        // TODO
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
        // dstAddr and port are coming from the forwarding table?
        /* TODO */

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
    /* 
    Define a match-action table that matches on the destination IP address 
    (or prefix) and forwards the packet to the output port based on a forwarding 
    table that will be supplied by the control plane. 
    
    This forwarding table  is in our case supplied as json files called 
    topo/s*-runtime.json.
    */
    table ipv4_lpm {
        /* TODO */
        key = {
            hdr.ipv4.dstAddr: lpm; // from core.p4
        }
        actions = {
            ipv4_forward;
            drop;
            NoAction; // from core.p4
        }
        size = 1024;
        default_action = NoAction();
    }
    
    apply {
        if (hdr.ipv4.isValid()) {
            ipv4_lpm.apply();
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
    }
}

/*************************************************************************
*************   C H E C K S U M    C O M P U T A T I O N   **************
*************************************************************************/

control MyComputeChecksum(inout headers  hdr, inout metadata meta) {
    apply {
        // docs @ https://github.com/p4lang/p4c/blob/37cd30ee9dc79c65b057a1aa168b961d7aba4701/p4include/v1model.p4#L461-L505
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
    }
}

/*************************************************************************
***********************  D E P A R S E R  *******************************
*************************************************************************/

control MyDeparser(packet_out packet, in headers hdr) {
    apply {
        // Emit ethernet frame
        packet.emit(hdr.ethernet);
        // Emit IPv4 packet
        packet.emit(hdr.ipv4);
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
