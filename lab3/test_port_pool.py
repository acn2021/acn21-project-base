import unittest
from port_pool import PortPool
from address import Address

class TestPortPool(unittest.TestCase):

    def test_host(self):
        pool = PortPool(4)
        assert pool.get_free_port(Address("10.0.0.2"), Address("10.0.0.1")) == 1
        assert pool.get_free_port(Address("10.0.0.2"), Address("10.0.0.1")) == None
        assert pool.get_free_port(Address("10.0.0.3"), Address("10.0.0.1")) == 1
    
    def test_edge_upstream(self):
        pool = PortPool(4)
        assert pool.get_free_port(Address("10.0.0.1"), Address("10.0.2.1")) == 3
        assert pool.get_free_port(Address("10.0.0.1"), Address("10.0.3.1")) == 4
        assert pool.get_free_port(Address("10.0.0.1"), Address("10.0.3.1")) == None
    
    def test_edge_downstream(self):
        pool = PortPool(4)
        assert pool.get_free_port(Address("10.0.0.1"), Address("10.0.0.2")) == 1
        assert pool.get_free_port(Address("10.0.0.1"), Address("10.0.0.3")) == 2
        assert pool.get_free_port(Address("10.0.0.1"), Address("10.0.0.4")) == None

    def test_aggr_upstream(self):
        pool = PortPool(4)
        assert pool.get_free_port(Address("10.0.2.1"), Address("10.4.1.1")) == 3
        assert pool.get_free_port(Address("10.0.2.1"), Address("10.4.1.2")) == 4
        assert pool.get_free_port(Address("10.0.2.1"), Address("10.4.1.2")) == None

    def test_aggr_downstream(self):
        pool = PortPool(4)
        assert pool.get_free_port(Address("10.0.2.1"), Address("10.0.0.1")) == 1
        assert pool.get_free_port(Address("10.0.2.1"), Address("10.0.1.1")) == 2
        assert pool.get_free_port(Address("10.0.2.1"), Address("10.0.1.1")) == None

    def test_aggr_mix(self):
        pool = PortPool(4)
        assert pool.get_free_port(Address("10.0.2.1"), Address("10.0.0.1")) == 1
        assert pool.get_free_port(Address("10.0.2.1"), Address("10.4.1.2")) == 3
        assert pool.get_free_port(Address("10.0.2.1"), Address("10.4.1.1")) == 4
        assert pool.get_free_port(Address("10.0.2.1"), Address("10.0.1.1")) == 2
        assert pool.get_free_port(Address("10.0.2.1"), Address("10.0.1.1")) == None
        assert pool.get_free_port(Address("10.0.2.1"), Address("10.4.1.1")) == None

if __name__ == '__main__':
    unittest.main()
