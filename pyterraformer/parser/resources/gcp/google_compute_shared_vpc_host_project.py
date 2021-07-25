from pyterraformer.parser.resources.resource_object import ResourceObject


class GoogleComputeVpcHostProject(ResourceObject):

    _type = "google_compute_shared_vpc_host_project"
    REQUIRED_ATTRIBUTES = ["project"]

    def __init__(self, id, rtype, text, attributes=None):
        ResourceObject.__init__(self, rtype, id, text, attributes)
