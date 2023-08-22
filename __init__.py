#namespace is octoprint.plugins.OctoCMM

import octoprint.plugin

#the cmm plugin class
class OctoCMMPlugin(octoprint.plugin.StartupPlugin):
    def on_after_startup(self):
        #runs after octoprint startup
        self._logger.info("Log Test from OctoCMM Plugin!")

__plugin_name__ = "OctoCMM"
__plugin_pythoncompat__ = ">=3.7,<4"
#tells octoprint to instantiate the cmm class
__plugin_implementation__ = OctoCMMPlugin()