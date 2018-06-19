#encoding: utf-8

import logging
import traceback

from ..models import JobType
from .vul import SysVulScanProcessor



class Manager(object):

    def __init__(self, *args, **kwargs):
        self.processors = {
            JobType.SYS_VULSCAN : SysVulScanProcessor()
        }

    def get(self, type):
        return self.processors.get(type, None)