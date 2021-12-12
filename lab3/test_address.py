import unittest
from ft_routing import Address

class TestAddress(unittest.TestCase):

    def test_matches(self):
        assert Address("10.3.1.1").matches(Address("10.3.0.0/16")) # True
        assert not Address("10.2.1.1").matches(Address("10.3.0.0/16")) # False
        assert not Address("10.3.1.1").matches(Address("10.3.0.0/24")) # False
        assert Address("10.3.1.1").matches(Address("10.3.1.0/24")) # True

        # Illustrating the argument "mode":
        assert Address("10.5.6.7").matches(Address("10.1.2.3/8")) # True
        assert not Address("10.5.6.7").matches(Address("10.1.2.3/8"), mode="right-handed") # False
        assert Address("10.5.6.3").matches(Address("10.1.2.3/8"), mode="right-handed") # True
        assert Address("10.0.2.1/12").matches(Address("10.0.1.2/16")) # True
       
        assert not Address("10.1.2.1/16").matches(Address("10.0.1.2/16")) # False
        assert not Address("10.3.2.1").matches(Address("10.0.0.0/16")) # False
        assert not Address("10.3.2.1").matches(Address("10.1.0.0/16")) # False
        assert not Address("10.3.2.1").matches(Address("10.2.0.0/16")) # False
        assert Address("10.3.2.1").matches(Address("10.3.0.0/16")) # True
        assert not Address("10.0.3.1").matches(Address("10.3.0.0/16")) # False
        assert Address("10.0.2.1").matches(Address("0.0.0.1/8"), mode="right-handed")
        assert not Address("10.0.2.1").matches(Address("0.0.0.2/8"), mode="right-handed")
        assert not Address("10.0.2.2").matches(Address("0.0.0.1/8"), mode="right-handed")

    def test_is_host_address(self):
        k = 4
        assert Address("10.0.0.2").is_host_address(k)
        assert Address("10.0.0.3").is_host_address(k)
        assert Address("10.0.1.2").is_host_address(k)
        assert Address("10.0.1.3").is_host_address(k)
        assert not Address("10.4.1.3").is_host_address(k)
        assert not Address("10.0.0.1").is_host_address(k)
        assert not Address("10.0.1.1").is_host_address(k)

    def test_is_pod_address(self):
        k = 4
        assert Address("10.0.0.1").is_pod_address(k)
        assert Address("10.0.1.1").is_pod_address(k)
        assert Address("10.0.2.1").is_pod_address(k)
        assert Address("10.0.3.1").is_pod_address(k)
        assert Address("10.3.3.1").is_pod_address(k)
        assert not Address("10.0.0.2").is_pod_address(k)
        assert not Address("10.4.0.1").is_pod_address(k)

    def test_is_edge_address(self):
        k = 4
        assert Address("10.0.0.1").is_edge_node_address(k)
        assert Address("10.0.1.1").is_edge_node_address(k)
        assert not Address("10.0.2.1").is_edge_node_address(k)
        assert not Address("10.0.3.1").is_edge_node_address(k)

    def test_is_aggr_address(self):
        k = 4
        assert Address("10.0.2.1").is_aggr_node_address(k)
        assert Address("10.0.3.1").is_aggr_node_address(k)
        assert not Address("10.0.0.1").is_aggr_node_address(k)
        assert not Address("10.0.1.1").is_aggr_node_address(k)

if __name__ == '__main__':
    unittest.main()
