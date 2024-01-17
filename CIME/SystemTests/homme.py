from CIME.SystemTests.hommebaseclass import HommeBase


class HOMME(HommeBase):
    def __init__(self, case, **kwargs):
        HommeBase.__init__(self, case, **kwargs)
        self.cmakesuffix = ""
