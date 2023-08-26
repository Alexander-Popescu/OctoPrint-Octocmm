import octoprint.plugin
from flask import jsonify
import os
import datetime
import requests
import re

class OctoCmmPlugin(octoprint.plugin.StartupPlugin,
                    octoprint.plugin.TemplatePlugin,
                    octoprint.plugin.SettingsPlugin,
                    octoprint.plugin.AssetPlugin,
                    octoprint.plugin.SimpleApiPlugin):


    def on_after_startup(self):
        self._logger.info("OctoCmm loaded!")
        self.cmmState = "Idle"
        self.lastProbedPoint = [0,0,0]
        self.APIKEY = self._settings.global_get(["api","key"])
        self.m114_parse = False
        self.ok_response = False

        
    def get_settings_defaults(self):
        return dict(
            probing_mode="default",
            output_file_name="output.csv",
            noWrite='False'
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
                status="CMM is Busy",
                result=f"CMM State: {self.cmmState}, LastProbedPosition: {self.lastProbedPoint}"
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
                result=f"CMM State: {self.cmmState}, LastProbedPosition: {self.lastProbedPoint}"
            ))

        else:
            return jsonify(dict(
                status="error, unknown command"
            ))

    def Run_CMM_Probing(self):
        if not self._printer.is_operational():
            self._logger.info("Printer is not connected, cannot run probing")
            return

        probing_mode = self._settings.get(["probing_mode"])
        output_file_name = self._settings.get(["output_file_name"])

        self.lastProbedPoint[0] += 1
        # Code for running CMM probing
        self._logger.info(f"Running Run_CMM_Probing function with probing mode {probing_mode} and output file name {output_file_name}")
        self._logger.info(f"lastProbedPoint {self.lastProbedPoint}")
        pass

    def Probe_Current_Position(self):
        output_file_name = self._settings.get(["output_file_name"])

        #check if printer connected
        if not self._printer.is_operational():
            self._logger.info("Printer is not connected, cannot probe current position")
            return

        # Code for probing current position
        self._logger.info(f"Running Probe_Current_Position function with output file name {output_file_name}")

        #run probe command and wait for it to finish completely
        self.ok_response = False
        self._printer.commands("G38.2")
        while not self.ok_response:
            pass

        headPos = self.Get_Head_Position()
        #headposition calls m114, which is parsed by the parsing function and that writes it to the file, so we are done here
        self._logger.info(f"Head Position: {headPos}")
        pass

    def Get_Head_Position(self):
        #send single gcode to printer with requests
        # url = "/api/printer/command"
        # payload = {"command": "M114"}
        # headers = {
        #  'Content-Type': 'application/json',
        #  'X-Api-Key': self.APIKEY
        #   }
        # response = requests.post(url, json=payload, headers=headers)

        #send using simpleapiplugin
        self.m114_parse = False
        self._printer.commands("M114 R")

        #then ideally it will be picked up and parsed by the gcode recieve hook

        #wait for response
        while not self.m114_parse:
            pass
        
        #since the parsing function updated the lastprobedpoint to what it detected, we can return it here
        return self.lastProbedPoint

    
    def Write_To_File(self, x_value, y_value, z_value):
        #if noWrite mode is on, return
        if self._settings.get(["noWrite"]) == True:
            self._logger.info("noWrite mode is on, not writing to file")
            return
        output_file_name = "OctoCMM_{}".format(self._settings.get(["output_file_name"]))
        #check if file exists, if not create one
        if not os.path.exists(output_file_name):
            self._logger.info(f"File {output_file_name} does not exist, creating it now, directory: {os.getcwd()}")
            open(output_file_name, 'x')
            #write header line
            with open(output_file_name, 'a') as f:
                f.write("File Generated By OctoCMM, each entry is an x,y,z coordinate pair for a position recorded as the surface of the part, then the time the data was recorded\n")
                f.write("X,Y,Z,Time\n")
                f.close()
        
        #write data to file
        self._logger.info(f"Writing data to file {output_file_name}, in {os.getcwd()}")
        with open(output_file_name, 'a') as f:
            write_var = f"{x_value},{y_value},{z_value},{datetime.datetime.now().strftime('%H:%M:%S')}\n"
            f.write(write_var)
            f.close()

    def parse_gcode_responses(self, comm, line, *args, **kwargs):
        #checks for M114 response
        pattern = r"ok X:\d+\.\d{1,2} Y:\d+\.\d{1,2} Z:\d+\.\d{1,2} E:\d+\.\d{1,2} Count: A:\d+ B:\d+ C:\d+"
        if re.match(pattern, line):
            #parse line for x,y,z values
            self._logger.info(f"Received M114 response: {line}")
            self.parse_m114_response(line)
            return line
        else:
            #check if the entire response just says ok
            pattern = r"ok"
            if re.match(pattern, line):
                self.ok_response = True
                return line
            else:
                return line

    def parse_m114_response(self, line):
        x_value = re.search(r"X:(\d+\.\d{1,2})", line).group(1)
        y_value = re.search(r"Y:(\d+\.\d{1,2})", line).group(1)
        z_value = re.search(r"Z:(\d+\.\d{1,2})", line).group(1)
        self._logger.info(f"X: {x_value}, Y: {y_value}, Z: {z_value}")
        self.Write_To_File(x_value, y_value, z_value)
        self.lastProbedPoint = [x_value, y_value, z_value]
        self._logger.info(f"lastProbedPoint from parse_m114 {self.lastProbedPoint}")
        self.m114_parse = True

    def get_assets(self):
        return dict(
            js=["js/OctoCMM.js"]
        )

__plugin_name__ = "OctoCmm"
__plugin_pythoncompat__ = ">=3.7,<4"
#IMPORTANT: Make sure the marlin firmware has M114_REALTIME enabled and G38_PROBE_TARGET with the BLtouch probe defined

def __plugin_load__():
	global __plugin_implementation__
	__plugin_implementation__ = OctoCmmPlugin()

	global __plugin_hooks__
	__plugin_hooks__ = {
		"octoprint.comm.protocol.gcode.received": __plugin_implementation__.parse_gcode_responses
	}