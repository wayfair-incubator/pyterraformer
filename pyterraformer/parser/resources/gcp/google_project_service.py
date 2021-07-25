from pyterraformer.parser.resources.resource_object import ResourceObject


class GoogleProjectService(ResourceObject):

    REQUIRED_ATTRIBUTES = ["project", "service"]
    _type = "google_project_service"

    def __init__(self, id, rtype, text, attributes=None):

        ResourceObject.__init__(self, rtype, id, text, attributes)
