import octoprint.plugin

class OctoCMMPlugin(octoprint.plugin.StartupPlugin,
                    octoprint.plugin.TemplatePlugin,
                    octoprint.plugin.SettingsPlugin,
                    octoprint.plugin.AssetPlugin):
    def on_after_startup(self):
        #runs after plugin startup
        self._logger.info("OctoCMM Plugin! (URL: %s)" % self._settings.get(["url"]))

    def get_settings_defaults(self):
        #this is where you can define default setting values
        return dict(url="https://en.wikipedia.org/wiki/Hello_world")
    
    def get_template_configs(self):
        return [
            dict(type="navbar", custom_bindings=False),
            dict(type="settings", custom_bindings=False)
        ]
    def get_assets(self):
        return dict(
            js=["js/OctoCMM.js"]
        )

__plugin_name__ = "OctoCMM"
__plugin_pythoncompat__ = ">=3.7,<4"
__plugin_implementation__ = OctoCMMPlugin()