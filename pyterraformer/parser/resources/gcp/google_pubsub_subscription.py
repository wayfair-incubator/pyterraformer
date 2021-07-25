from pyterraformer.parser.resources.resource_object import ResourceObject


class GooglePubsubSubscription(ResourceObject):
    _type = "google_pubsub_subscription"
    REQUIRED_ATTRIBUTES = ["name", "topic", "labels", "project"]

    def __init__(self, id, rtype, text, attributes=None):

        ResourceObject.__init__(self, rtype, id, text, attributes)

    @classmethod
    def create(cls, id, **kwargs):
        # kwargs['force_destroy'] = kwargs.get('force_destroy') or force_destroy
        kwargs["name"] = kwargs.get("name") or id
        return super().create(id, **kwargs)
