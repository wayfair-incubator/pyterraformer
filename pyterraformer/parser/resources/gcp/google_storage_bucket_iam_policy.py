from pyterraformer.parser.resources.resource_object import ResourceObject


class GoogleStorageBucketIamPolicy(ResourceObject):
    _type = "google_storage_bucket_iam_policy"

    def __init__(self, id, rtype, text, attributes=None):

        ResourceObject.__init__(self, rtype, id, text, attributes)
