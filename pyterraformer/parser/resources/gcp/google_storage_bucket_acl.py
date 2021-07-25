from pyterraformer.parser.resources.resource_object import ResourceObject


class GoogleStorageBucketACL(ResourceObject):
    _type = "google_storage_bucket_acl"

    def __init__(self, id, rtype, text, attributes=None):

        ResourceObject.__init__(self, rtype, id, text, attributes)
