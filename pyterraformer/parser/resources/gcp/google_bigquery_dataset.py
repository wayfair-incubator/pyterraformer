from pyterraformer.parser.resources.resource_object import ResourceObject


class GoogleBigqueryDataset(ResourceObject):
    _type = "google_bigquery_dataset"

    def __init__(self, id, rtype, text, attributes=None):
        ResourceObject.__init__(self, rtype, id, text, attributes)
