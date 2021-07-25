from pyterraformer.parser.resources.resource_object import ResourceObject


class GoogleProjectIamBinding(ResourceObject):

    _type = "google_project_iam_binding"
    REQUIRED_ATTRIBUTES = ["project", "role", "members"]

    def __init__(self, id, rtype, text, attributes=None):

        ResourceObject.__init__(self, rtype, id, text, attributes)
