from pyterraformer.parser.resources.resource_object import ResourceObject
from typing import List


class GoogleComputeSubnetworkIamMember(ResourceObject):

    _type = "google_compute_subnetwork_iam_member"
    REQUIRED_ATTRIBUTES: List[str] = []

    def __init__(self, id, rtype, text, attributes=None):

        ResourceObject.__init__(self, rtype, id, text, attributes)
