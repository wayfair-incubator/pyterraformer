from pyterraformer.parser.resources.resource_object import ResourceObject


class GoogleBigqueryTable(ResourceObject):
    _type = "google_bigquery_table"

    def __init__(self, id, rtype, text, attributes=None):
        ResourceObject.__init__(self, rtype, id, text, attributes)
