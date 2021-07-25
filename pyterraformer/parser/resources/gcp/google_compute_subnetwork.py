from pyterraformer.parser.resources.resource_object import ResourceObject


class GoogleComputeSubnetwork(ResourceObject):

    _type = "google_compute_subnetwork"
    REQUIRED_ATTRIBUTES = ["name", "ip_cidr_range", "region", "network", "private_ip_google_access"]

    def __init__(self, id, rtype, text, attributes=None):
        ResourceObject.__init__(self, rtype, id, text, attributes)
