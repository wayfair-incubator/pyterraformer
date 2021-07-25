from pyterraformer.executor.state_providers.base_provider import BaseStateProvider



class GCSStateProvider(BaseStateProvider):

    def __init__(self, bucket:str, ):