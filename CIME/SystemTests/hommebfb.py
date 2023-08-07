from CIME.SystemTests.hommebaseclass import HommeBase


class HOMMEBFB(HommeBase):
    def __init__(self, case, **kwargs):
        HommeBase.__init__(self, case, **kwargs)
        self.cmakesuffix = "-bfb"
