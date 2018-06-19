#encoding: utf-8


class ShadowException(Exception):


    def __init__(self, msg, code=None, *args, **kwargs):
        super(ShadowException, self).__init__(*args, **kwargs)
        self.msg = msg
        self.code = code


