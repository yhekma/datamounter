from dlib.datamounter_helpers import load_struct

class TestMounter(object):
    @classmethod
    def setup_class(cls):
        cls.struct = load_struct('bla.json')

    @classmethod
    def teardown_class(cls):
        pass