from typing import Optional
from address import Address

class PortPool:
    """Holds a list of free ports for a pod node. Can return a valid free port
    according to the fat tree port numbering, i.e. upstream ports are roughly the 
    first half of k ports [1, 2], downstream (subnet) ports are second half k ports [3, 4], 
    for k = 4.

    Note: DOES NOT WORK ON CORE SWITCHES AS A SRC
    """
    def __init__(self, k) -> None:
        self._port_pool = {}
        self.k = k

    def get_free_port(self, addr_src: Address, addr_dst: Address) -> Optional[int]:
        """Returns the free ports for the switch addr_src, taking into account
        the destination for picking a port number. See class description for port
        picking logic, or check test_port_pool.py for examples.

        Args:
            addr_src (Address): addr of switch to pick a port for
            addr_dst (Address): destination of the link connected to the port
                being picked

        Returns:
            Optional[int]: A free port.
        """

        k = self.k

        # From host to edge
        if (addr_src.is_host_address(k)):
            return self._take(addr_src, "host")

        is_upstream: bool = (addr_dst.is_core_address()
            or (addr_src.is_edge_node_address(k) and addr_dst.is_aggr_node_address(k)))
        if (is_upstream): # From aggr to core or from pod node to pod node
            # Return port 3 or 4 for k=4
            return self._take(addr_src, "upstream_range")
        else: # From aggr to edge
            return self._take(addr_src, "downstream_range")


    # Take free port from port pool
    def _take(self, addr_src: Address, type):
        k = self.k
        raw_src = addr_src.raw
        # Check if port pool has been setup, if not create
        if (not self._port_pool.get(raw_src)):
            # Fill port pool
            self._port_pool[raw_src] = {
                "downstream_range": [x for x in range(1, int(k/2) + 1)],  # 1, 2 for k=4
                "upstream_range" : [x for x in range(int(k/2) + 1, k + 1)],  # 3, 4 for k=4
                "host": [1] # Host only has one link/port to edge node
            }
        available_ports = self._port_pool[raw_src][type] # Get correct type
        if (not available_ports): # If none in pool for type
            return None
        free_port = available_ports.pop(0) # Remove first from pool
        self._port_pool[raw_src][type] = available_ports # Update remaining pool
        return free_port

