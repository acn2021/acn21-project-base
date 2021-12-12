# Usage

To run, for example, routing:

```sh
cd lab4/routing
make

# If you get an error, you can clean up mininet via
make stop # this does sudo mn -c
```

## Quick explanation

The following is a quick explanation of how the files `topology.json`, `s*-runtime.json`
and `routing.p4` relate to each other.

## topo

Topology with IP and MAC addresses are defined in `topology.json`:

```js
    // topology.sjon
    "hosts": {
        "h1": { // host h1
            "ip": "10.0.1.1/24", // define subnet for host
            "mac": "08:00:00:00:01:11", // define mac for host
            "commands": [
                // define default gateway
                // send default to switch 10.0.1.10
                "route add default gw 10.0.1.10 dev eth0", 
                // create arp entry for switch 10.0.1.10 
                // with mac address 08:00:00:00:01:00
                "arp -i eth0 -s 10.0.1.10 08:00:00:00:01:00"
            ]
        },
        //...
```

Forwarding tables are defined in the json files `s*-runtime.json`.

```json
    // s1-runtime.json
    // ...
    "table_entries": [
    // Define default action drop
    {
        "table": "MyIngress.ipv4_lpm",
        "default_action": true,
        "action_name": "MyIngress.drop",
        "action_params": { }
    },
    // Map match to action ipv4_forward
    {
        "table": "MyIngress.ipv4_lpm",
        "match": {
            "hdr.ipv4.dstAddr": ["10.0.3.3", 32] // match on /32
        },
        // action to execute: ipv4_forward function in routing.p4
        "action_name": "MyIngress.ipv4_forward",
        "action_params": {
            "dstAddr": "08:00:00:00:03:33", // destination MAC of HOST
            "port": 1 // port to use to reach the MAC above
        }
    },
    {
        "table": "MyIngress.ipv4_lpm",
        "match": {
            "hdr.ipv4.dstAddr": ["10.0.1.1", 32]
        },
        "action_name": "MyIngress.ipv4_forward",
        "action_params": {
            "dstAddr": "08:00:00:00:01:00", // destination MAC of SWITCH
            "port": 2 // port to use to reach the MAC above
        }
    },
    // ...
```

This control block does the match and action logic and uses the forwarding table
defined in the json above.

```c#
// routing.p4
control MyIngress(inout headers hdr,
                  inout metadata meta,
                  inout standard_metadata_t standard_metadata) {
    

    action drop() {
        //...
    }
    
    // This action is taken on match
    action ipv4_forward(macAddr_t dstAddr, egressSpec_t port) {
        //...
    }

    table ipv4_lpm {
        /* TODO */
        key = {
            hdr.ipv4.dstAddr: lpm; // from core.p4
        }
        // Define actions
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
```