import octoprint.plugin
from flask import jsonify

class OctoCmmPlugin(octoprint.plugin.StartupPlugin,
                    octoprint.plugin.TemplatePlugin,
                    octoprint.plugin.SettingsPlugin,
                    octoprint.plugin.AssetPlugin,
                    octoprint.plugin.SimpleApiPlugin):
    def on_after_startup(self):
        self._logger.info("OctoCmm loaded!")
        
    def get_settings_defaults(self):
        return dict(
            probing_mode="default",
            output_file_name="output.txt"
        )

    def get_template_configs(self):
        return [
            dict(type="navbar", custom_bindings=False),
            dict(type="settings", custom_bindings=False)
        ]

    def get_api_commands(self):
        return dict(
            start_probing=[],
            probe_current_position=[]
        )

    def on_api_get(self, request):
        if request.args.get("command") == "start_probing":
            self._logger.info("start_probing")
            self.Run_CMM_Probing()
            return jsonify(dict(
                status="success",
                result="start_probing"
            ))
        elif request.args.get("command") == "probe_current_position":
            self._logger.info("probe_current_position")
            self.Probe_Current_Position()
            return jsonify(dict(
                status="success",
                result="probe_current_position"
            ))
        else:
            return jsonify(dict(
                status="error, unknown command"
            ))

    # def on_api_command(self, command, data):
    #     self._logger.info("Running on_api_command function")
    #     if command == 'start_probing':
    #         self._logger.info("start_probing")

    def Run_CMM_Probing(self):
        probing_mode = self._settings.get(["probing_mode"])
        output_file_name = self._settings.get(["output_file_name"])
        # Code for running CMM probing
        self._logger.info(f"Running Run_CMM_Probing function with probing mode {probing_mode} and output file name {output_file_name}")
        pass

    def Probe_Current_Position(self):
        output_file_name = self._settings.get(["output_file_name"])
        # Code for probing current position
        self._logger.info(f"Running Probe_Current_Position function with output file name {output_file_name}")
        pass

    def get_assets(self):
        return dict(
            js=["js/OctoCMM.js"]
        )

__plugin_name__ = "OctoCmm"
__plugin_implementation__ = OctoCmmPlugin()
__plugin_pythoncompat__ = ">=3.7,<4"