#encoding: utf-8

import time
import logging
import traceback

from shadow import redis, REDIS_KEYS

from ..base import BaseExecutor
from vul.models import SysVulPlugin, PluginConfig

logger = logging.getLogger(__name__)

class Executor(BaseExecutor):

    def init(self, job):
        plugins = {}
        plugin_infos = {}
        plugin_configs = {}
        enalbed_plugins = []
        job_params = job.get('job_params', {})
        idents = job_params.get('plugins', [])
        for ident in idents:
            plugin_info = SysVulPlugin.get_by_cache(ident)
            if not plugin_info:
                continue

            plugin_name = ident if plugin_info.type == SysVulPlugin.TYPE_SCRIPT else plugin_info.type
            plugin = self.plugins.get('plugin_{0}'.format(plugin_name), None)
            if not plugin:
                continue

            plugins[ident] = plugin
            plugin_configs[ident] = plugin_info.params_object
            plugin_infos[ident] = plugin_info


        self.plugins = plugins
        self.plugin_configs = plugin_configs
        self.plugin_infos = plugin_infos



    def get_plugin_config(self, name):
        plugin_config = super(Executor, self).get_plugin_config(name)
        logger.info('plugin_config:%s, %s', plugin_config, self.plugin_configs)
        if not plugin_config:
            return plugin_config

        for k, v in plugin_config.items():
            if not(isinstance(v, str) and v.startswith('__') and v.endswith('__')):
                continue

            config = PluginConfig.get_by_cache(v)
            if not config:
                continue
            try:
                plugin_config[k] = config.value_object
                logger.debug('init config from redis, key: %s, value: %s', k, config)
            except BaseException as e:
                logger.exception(e)
                logger.error(traceback.format_exc())

        return plugin_config


    def destory(self):
        super(Executor, self).destory()
        self.plugin_configs = {}
        self.plugin_infos = {}
        return True