from pyterraformer.parser.resources.resource_object import ResourceObject


class GoogleComputeFirewall(ResourceObject):

    _type = "google_compute_firewall"
    REQUIRED_ATTRIBUTES = [
        "name",
        "network",
        "allow",
        "direction",
        "priority",
        "source_tags",
        "target_tags",
    ]

    def __init__(self, id, rtype, text, attributes=None):
        ResourceObject.__init__(self, rtype, id, text, attributes)
