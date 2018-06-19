#encoding: utf-8
import logging
import traceback
import importlib
import os

logger = logging.getLogger(__name__)

NIL = lambda *args, **kwargs: None

class BaseExecutor(object):

    def __init__(self, plugin_pkg):
        self.plugins = self.init_plugins(plugin_pkg)
        self.plugin_configs = {}
        self.plugin_infos = {}


    def init_plugins(self, plugin_pkg):
        plugins = {}
        pkg_name = 'schedule.executor.{0}'.format(plugin_pkg)
        pkg = importlib.import_module(pkg_name)
        paths = getattr(pkg, '__path__', [])
        for path in paths:
            for name in os.listdir(path):
                if name in ('.', '..'):
                    continue

                modname, _, suffix = name.rpartition('.')
                if suffix not in ('py', 'pyc', ) or modname in ('__init__'):
                    continue

                name = '{0}.{1}'.format(pkg_name, modname)
                module = importlib.import_module(name)
                importlib.reload(module)
                plugins[modname] = module

        return plugins


    def init(self, job):
        pass


    def filter(self, name, plugin, job):
        return False


    def get_plugin_config(self, name):
        return self.plugin_configs.get(name)


    def get_plugin_info(self, name):
        return self.plugin_infos.get(name)


    def run(self, job):
        rt = {}
        job_params = job.get('job_params', {})
        plugins = self.plugins

        logger.debug('executor job: %s, use plugins: %s', job, plugins)

        for name, plugin in plugins.items():
            if self.filter(name, plugin, job):
                logger.debug('plugin not use: %s', name)
                continue

            run = getattr(plugin, 'run', None)
            if run is None:
                logger.error('plugin not found run method: %s', name)
                continue

            getattr(plugin, 'init', NIL)()
            try:
                plugin_info = self.get_plugin_info(name)
                plugin_config = self.get_plugin_config(name)
                logger.debug('run %s plugin, job_params:%s, plugin_info:%s, plugin_config: %s', name, job_params, plugin_info, plugin_config)
                for key, value in run(job_params, plugin_info, plugin_config):
                    if value is None:
                        continue
                    logger.debug('plugin %s is reback result, [%s]: %s', name, key, value)
                    rt.setdefault(key, {'key' : key})
                    rt[key].update(value)
            except BaseException as e:
                logger.error(e)
                logger.error(traceback.format_exc())
            finally:
                getattr(plugin, 'destory', NIL)()

        return list(rt.values())


    def destory(self):
        self.plugins = {}
        return True