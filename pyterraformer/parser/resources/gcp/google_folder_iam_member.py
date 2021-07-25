from pyterraformer.parser.resources.resource_object import ResourceObject


class GoogleFolderIamMember(ResourceObject):

    _type = "google_folder_iam_member"
    REQUIRED_ATTRIBUTES = ["folder", "role", "member"]

    def __init__(self, id, rtype, text, attributes=None):

        ResourceObject.__init__(self, rtype, id, text, attributes)
