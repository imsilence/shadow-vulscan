#encoding: utf-8

from .exceptions import ShadowException

import re


class ValidatorException(ShadowException):
    pass


class ValidatorMixin(object):

    def valid(self):
        has_error = False
        errors = {}
        for key, value in self.__dict__.items():
            func = getattr(self, 'clean_{0}'.format(key), None)
            if func:
                try:
                    setattr(self, key, func())
                except ValidatorException as e:
                    errors[key] = e
                    has_error = True

        func = getattr(self, 'clean', None)
        if func:
            try:
                func()
            except ValidatorException as e:
                errors[key] = e.msg
                has_error = True

        return has_error, errors


class ValidatorUtils(object):

    @staticmethod
    def is_int(value):
        try:
            int(value)
            return True
        except BaseException as e:
            return False


    @staticmethod
    def is_float(value):
        try:
            float(value)
            return True
        except BaseException as e:
            return False


    @staticmethod
    def is_length(value, min=None, max=None):
        length = len(str(value))
        return not(min is not None and min > length or max is not None and max < length)


    @staticmethod
    def is_range(value, min=None, max=None):
        try:
            value = float(value)
            return not(min is not None and min > value or max is not None and max < value)
        except BaseException as e:
            return False


    @staticmethod
    def is_email(value):
        return not not re.match(r'^[a-zA-Z0-9_-]{1,32}@[a-zA-Z0-9_-]{1,32}(\.[a-zA-Z0-9_-]{1,16}){1,2}$', value)


    @staticmethod
    def is_exists(value, elements=None):
        return elements is not None and value in elements

    @staticmethod
    def is_ip(value):
        return True

    @staticmethod
    def is_ip_range(value):
        return True