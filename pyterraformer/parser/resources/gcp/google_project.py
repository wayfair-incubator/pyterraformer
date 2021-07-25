from pyterraformer.parser.resources.resource_object import ResourceObject


class GoogleProject(ResourceObject):
    _type = "google_project"
    REQUIRED_ATTRIBUTES = [
        "auto_create_network",
        "billing_account",
        "folder_id",
        "name",
        "project_id",
        "labels",
    ]

    def __init__(self, id, rtype, text, attributes=None):
        ResourceObject.__init__(self, self._type, id, text, attributes)

    @property
    def import_address(self) -> str:
        return self.project_id
