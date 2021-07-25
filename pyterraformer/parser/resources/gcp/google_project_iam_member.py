from pyterraformer.parser.resources.resource_object import ResourceObject


class GoogleProjectIamMember(ResourceObject):

    _type = "google_project_iam_member"
    REQUIRED_ATTRIBUTES = ["project", "role", "member"]

    def __init__(self, id, rtype, text, attributes=None):

        ResourceObject.__init__(self, rtype, id, text, attributes)
