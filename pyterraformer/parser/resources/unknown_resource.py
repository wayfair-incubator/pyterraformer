from pyterraformer.parser.resources.resource_object import ResourceObject


class UnknownResource(ResourceObject):
    def __init__(self, id, rtype, text, attributes):
        self._type = str(rtype).replace('"', "")
        ResourceObject.__init__(self, rtype, id, text, attributes)
