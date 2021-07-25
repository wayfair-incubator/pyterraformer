from pyterraformer.parser.resources.resource_object import ResourceObject


class GooglePubsubTopicIamMember(ResourceObject):
    _type = "google_pubsub_topic_iam_member"

    def __init__(self, id, rtype, text, attributes=None):

        ResourceObject.__init__(self, rtype, id, text, attributes)
