from pyterraformer.parser.resources.resource_object import ResourceObject


class GoogleComputeDisk(ResourceObject):
    _type = "google_compute_disk"
    REQUIRED_ATTRIBUTES = ["name"]
    PRIORITY_ATTRIBUTES = ["type", "zone", "image"]

    def __init__(self, id, rtype, text, attributes=None):
        ResourceObject.__init__(self, rtype, id, text, attributes)

    @classmethod
    def create(cls, id, **kwargs):
        kwargs["name"] = kwargs.get("name") or id
        return super().create(id, **kwargs)
