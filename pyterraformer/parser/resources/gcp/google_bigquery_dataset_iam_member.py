from pyterraformer.parser.resources.resource_object import ResourceObject


class GoogleBigqueryDatasetIamMember(ResourceObject):

    _type = "google_bigquery_dataset_iam_member"
    REQUIRED_ATTRIBUTES = ["dataset_id", "role", "member"]

    def __init__(self, id, rtype, text, attributes=None):

        ResourceObject.__init__(self, rtype, id, text, attributes)
