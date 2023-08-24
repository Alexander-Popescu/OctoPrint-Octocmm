import octoprint.plugin
from flask import jsonify

class OctoCmmPlugin(octoprint.plugin.StartupPlugin,
                    octoprint.plugin.TemplatePlugin,
                    octoprint.plugin.SettingsPlugin,
                    octoprint.plugin.AssetPlugin,
                    octoprint.plugin.SimpleApiPlugin):


    def on_after_startup(self):
        self._logger.info("OctoCmm loaded!")
        self.cmmState = "Idle"
        self.lastProbedPoint = [0,0,0]

        
    def get_settings_defaults(self):
        return dict(
            probing_mode="default",
            output_file_name="output.txt",
        )

    def get_template_configs(self):
        return [
            dict(type="navbar", custom_bindings=False),
            dict(type="settings", custom_bindings=False),
        ]
    
    def get_template_vars(self):
        return dict(probing_mode=self._settings.get(["probing_mode"]), output_file_name=self._settings.get(["output_file_name"]))

    def get_api_commands(self):
        return dict(
            start_probing=[],
            probe_current_position=[]
        )

    def on_api_get(self, request):
        if self.cmmState != "Idle":
            return jsonify(dict(
                status="CMM is busy",
                result=self.cmmState
            ))
        if request.args.get("command") == "start_probing":
            self._logger.info("start_probing")
            self.cmmState = "FullProbing"
            self._logger.info(f"Current CMM state {self.cmmState}")
            self.Run_CMM_Probing()
            self.cmmState = "Idle"
            return jsonify(dict(
                status="success",
                result="start_probing"
            ))
        elif request.args.get("command") == "probe_current_position":
            self._logger.info("probe_current_position")
            self.cmmState = "SinglePointProbing"
            self._logger.info(f"Current CMM state {self.cmmState}")
            self.Probe_Current_Position()
            self.cmmState = "Idle"
            return jsonify(dict(
                status="success",
                result="probe_current_position"
            ))

        elif request.args.get("command") == "update_vars":
            self._logger.info("update_vars")
            return jsonify(dict(
                status="success",
                result=f"State: {self.cmmState}, LastPos: {self.lastProbedPoint}"
            ))
        else:
            return jsonify(dict(
                status="error, unknown command"
            ))

    def Run_CMM_Probing(self):
        probing_mode = self._settings.get(["probing_mode"])
        output_file_name = self._settings.get(["output_file_name"])

        self.lastProbedPoint[0] += 1
        # Code for running CMM probing
        self._logger.info(f"Running Run_CMM_Probing function with probing mode {probing_mode} and output file name {output_file_name}")
        self._logger.info(f"lastProbedPoint {self.lastProbedPoint}")
        pass

    def Probe_Current_Position(self):
        output_file_name = self._settings.get(["output_file_name"])

        self.lastProbedPoint[1] += 1
        # Code for probing current position
        self._logger.info(f"Running Probe_Current_Position function with output file name {output_file_name}")
        self._logger.info(f"lastProbedPoint {self.lastProbedPoint}")
        pass

    def get_assets(self):
        return dict(
            js=["js/OctoCMM.js"]
        )

__plugin_name__ = "OctoCmm"
__plugin_implementation__ = OctoCmmPlugin()
__plugin_pythoncompat__ = ">=3.7,<4"