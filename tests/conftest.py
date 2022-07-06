from pytest import fixture
from pyterraformer import HumanSerializer


@fixture(scope='session')
def human_serializer():
    yield HumanSerializer()


