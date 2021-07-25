from pyterraformer.parser.resources.resource_object import ResourceObject
from typing import List


class GoogleComputeProjectMetadata(ResourceObject):

    _type = "google_compute_project_metadata"
    REQUIRED_ATTRIBUTES: List[str] = []

    def __init__(self, id, rtype, text, attributes=None):

        ResourceObject.__init__(self, rtype, id, text, attributes)
