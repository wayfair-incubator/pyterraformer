from pyterraformer.parser.resources.resource_object import ResourceObject


class GoogleAccessContextManagerServicePerimeter(ResourceObject):
    _type = "google_access_context_manager_service_perimeter"
    REQUIRED_ATTRIBUTES = ["parent", "name", "title"]

    def __init__(self, id, rtype, text, attributes=None):
        ResourceObject.__init__(self, rtype, id, text, attributes)
