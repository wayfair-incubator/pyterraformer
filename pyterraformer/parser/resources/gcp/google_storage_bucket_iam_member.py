from pyterraformer.parser.resources.resource_object import ResourceObject


class GoogleStorageBucketIamMember(ResourceObject):
    _type = "google_storage_bucket_iam_member"
    REQUIRED_ATTRIBUTES = ["bucket", "role", "member"]

    def __init__(self, id, rtype, text, attributes=None):

        ResourceObject.__init__(self, rtype, id, text, attributes)

    @classmethod
    def create(cls, id, bucket, role, member, **kwargs):
        # kwargs['force_destroy'] = kwargs.get('force_destroy') or force_destroy
        kwargs["bucket"] = bucket
        kwargs["role"] = role
        kwargs["member"] = member
        return super().create(id, **kwargs)
