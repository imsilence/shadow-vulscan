#encoding: utf-8

import json

from datetime import datetime

class AsDictMixin(object):
    def as_dict(self):
        result = {}
        for key, value in self.__dict__.items():
            if value is None or isinstance(value, (int, float, bool)):
                result[key] = value
            elif isinstance(value, datetime):
                result[key] = value.strftime('%Y-%m-%d %H:%M:%S')
            elif isinstance(value, (list, tuple, dict)):
                result[key] = value
            elif isinstance(value, str):
                try:
                    result[key] = json.loads(value)
                except BaseException as e:
                    result[key] = value

        return result

    def as_dict_string(self):
        result = {}
        for key, value in self.__dict__.items():
            if value is None or isinstance(value, (int, float, bool, str)):
                result[key] = value
            elif isinstance(value, datetime):
                result[key] = value.strftime('%Y-%m-%d %H:%M:%S')
            elif isinstance(value, (list, tuple, dict)):
                result[key] = json.dumps(value)
            elif isinstance(value, bytes):
                result[key] = value.decode()

        return result

    def __str__(self):
        return json.dumps(self.as_dict())
