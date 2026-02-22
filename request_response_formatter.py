from behave.formatter.base import Formatter


class RequestResponseFormatter(Formatter):
    """Silent formatter: keeps Behave structural output hidden.

    Test diagnostics are emitted directly by step print() calls
    (request/response/validation blocks).
    """

    def feature(self, feature):
        return None

    def background(self, background):
        return None

    def scenario(self, scenario):
        return None

    def step(self, step):
        return None

    def match(self, match):
        return None

    def result(self, result):
        return None

    def eof(self):
        return None

    def close(self):
        return None
