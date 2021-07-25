from pyterraformer.parser.resources.resource_object import ResourceObject


class GoogleStorageBucket(ResourceObject):
    _type = "google_storage_bucket"
    REQUIRED_ATTRIBUTES = ["name", "project", "location", "labels"]
    PRIORITY_ATTRIBUTES = ["storage_class", "versioning"]
    BLOCK_ATTRIBUTES = ["versioning"]

    def __init__(self, id, rtype, text, attributes=None):

        ResourceObject.__init__(self, rtype, id, text, attributes)

    @classmethod
    def create(cls, id, storage_class="REGIONAL", location="us-central1", **kwargs):
        # kwargs['force_destroy'] = kwargs.get('force_destroy') or force_destroy
        kwargs["location"] = kwargs.get("location") or location
        kwargs["storage_class"] = kwargs.get("storage_class") or storage_class
        kwargs["name"] = kwargs.get("name") or id
        return super().create(id, **kwargs)
