from pyterraformer.parser.resources.resource_object import ResourceObject


class GoogleServiceAccountIamMember(ResourceObject):

    _type = "google_service_account_iam_member"
    REQUIRED_ATTRIBUTES = ["service_account_id", "role", "member"]

    def __init__(self, id, rtype, text, attributes=None):

        ResourceObject.__init__(self, rtype, id, text, attributes)
