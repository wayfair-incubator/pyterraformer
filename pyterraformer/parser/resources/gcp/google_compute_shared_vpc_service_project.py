from pyterraformer.parser.resources.resource_object import ResourceObject


class GoogleComputeSharedVPCServiceProject(ResourceObject):

    _type = "google_compute_shared_vpc_service_project"
    REQUIRED_ATTRIBUTES = ["host_project", "service_project"]

    def __init__(self, id, rtype, text, attributes=None):
        ResourceObject.__init__(self, rtype, id, text, attributes)
