from pyterraformer.parser.resources.resource_object import ResourceObject


class GooglePubsubSubscriptionIamMember(ResourceObject):
    _type = "google_pubsub_subscription_iam_member"

    def __init__(self, id, rtype, text, attributes=None):

        ResourceObject.__init__(self, rtype, id, text, attributes)
