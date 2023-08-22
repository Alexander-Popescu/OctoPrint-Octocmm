import octoprint.plugin

class OctoCMMPlugin(octoprint.plugin.StartupPlugin,
                    octoprint.plugin.TemplatePlugin):
    def on_after_startup(self):
        self._logger.info("Console Log from OctoCMM plugin!")

__plugin_name__ = "OctoCMM"
__plugin_pythoncompat__ = ">=3.7,<4"
__plugin_implementation__ = OctoCMMPlugin()