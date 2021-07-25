from pyterraformer.parser.resources.resource_object import ResourceObject

"""        project=name,
        description=f"This is standalone, non-peered VPC for the {project.name_root} project.",
        auth_create_subnetworks=False,"""


class GoogleComputeNetwork(ResourceObject):

    _type = "google_compute_network"
    REQUIRED_ATTRIBUTES = ["name", "description", "auto_create_subnetworks"]

    def __init__(self, id, rtype, text, attributes=None):
        ResourceObject.__init__(self, rtype, id, text, attributes)
