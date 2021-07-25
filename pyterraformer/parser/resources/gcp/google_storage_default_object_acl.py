from pyterraformer.parser.resources.resource_object import ResourceObject


class GoogleStorageDefaultObjectACL(ResourceObject):
    _type = "google_storage_default_object_acl"

    def __init__(self, id, rtype, text, attributes=None):

        ResourceObject.__init__(self, rtype, id, text, attributes)
