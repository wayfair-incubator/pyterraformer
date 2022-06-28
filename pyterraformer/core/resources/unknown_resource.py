from pyterraformer.core.resources.resource_object import ResourceObject


class GenericResource(ResourceObject):
    """This resource represents an object that is parsed
    from a terraform file but there is no matching provider library
    to provide type hinting and auto completion"""

    def __init__(self, tf_id, rtype, text, attributes):
        self._type = str(rtype).replace('"', "")
        ResourceObject.__init__(self, rtype, tf_id, text, attributes)
