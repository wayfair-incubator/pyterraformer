from pyterraformer.parser.resources.resource_object import ResourceObject


class GoogleProjectIamAuditConfig(ResourceObject):

    _type = "google_project_iam_audit_config"
    REQUIRED_ATTRIBUTES = ["project", "service"]

    def __init__(self, id, rtype, text, attributes=None):

        ResourceObject.__init__(self, rtype, id, text, attributes)
