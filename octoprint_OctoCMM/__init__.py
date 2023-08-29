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
        #state used to indicate to the frontend
        self.cmmState = "Idle"
        #also frontend variable
        self.lastProbedPoint = [0,0,0]
        #internal most recent headposition location
        self.headpos = [0,0,0,0,0,0]
        #api key for sending commands to printer
        self.APIKEY = self._settings.global_get(["api","key"])
        #flags for certain gcodes since we have to parse manually
        self.m114_parse = False
        self.g30_response = False
        self.ok_response = False

        
    def get_settings_defaults(self):
        #settings used internally and configurable in the settings tab of octoprint
        return dict(
            probing_mode="default",
            output_file_name="output.csv",
            noWrite='False',
            maxPartHeight=50,#in millimeters
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
        #using get requests to do things because post wouldnt work for some reason

        #check if cmm is open to commands
        if self.cmmState != "Idle":
            return jsonify(dict(
                status="CMM is Busy",
                result=f"CMM State: {self.cmmState}, LastProbedPosition: {self.lastProbedPoint}"
            ))

        #runs overall probing function
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
            
        #runs single point probing function
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

        #updates frontend with variable valuess
        elif request.args.get("command") == "update_vars":
            self._logger.info("update_vars")
            return jsonify(dict(
                status="success",
                result=f"CMM State: {self.cmmState}, LastProbedPosition: {self.lastProbedPoint}, Probing Mode: {self._settings.get(['probing_mode'])}, Output File Name: {self._settings.get(['output_file_name'])}, noWrite: {self._settings.get(['noWrite'])}, maxPartHeight: {self._settings.get(['maxPartHeight'])}"
            ))

        elif request.args.get("command") == "home_printer":
            self._logger.info("home_printer")
            self.cmmState = "Homing"
            self._logger.info(f"Current CMM state {self.cmmState}")
            self.home_printer()
            self.cmmState = "Idle"
            return jsonify(dict(
                status="success",
                result="home_printer"
            ))

        else:
            return jsonify(dict(
                status="error, unknown command"
            ))

    def home_printer(self):
        self.ok_response = False
        self._logger.info("Homing Printer funtion called")
        self._printer.commands("G28")
        while not self.ok_response:
            pass

        #move printer up to slide in part
        self.ok_response = False
        self._printer.commands(f"G1 {maxPartHeight + 50}")
        while not self.ok_response:
            pass
        return

    def Run_CMM_Probing(self):
        #get settings
        output_file_name = self._settings.get(["output_file_name"])
        probing_mode = self._settings.get(["probing_mode"])
        noWrite = self._settings.get(["noWrite"])
        maxPartHeight = self._settings.get(["maxPartHeight"])

        #check if printer connected
        if not self._printer.is_operational():
            self._logger.info("Printer is not connected, cannot run probing")
            return

        self._logger.info(f"Running Run_CMM_Probing function with probing mode {probing_mode} and output file name {output_file_name}")
        self._logger.info(f"lastProbedPoint {self.lastProbedPoint}")

        #check z height of printhead, wait to move if not there
        CurrentHeadPosition = self.Get_Head_Position()
        if CurrentHeadPosition[2] != maxPartHeight + 25:
            self._logger.info(f"Head is not at max part height, moving to max part height {maxPartHeight}")
            self.ok_response = False
            self._printer.commands(f"G1 Z{maxPartHeight + 25}")
            while not self.ok_response:
                pass
        
        if probing_mode == 'default':
            #run default probing routine
            self._logger.info("Running default probing routine")
            self.Run_Default_Probing()
        else:
            #run custom probing routine
            self._logger.info("Not Default, looking for custom probing routine")
    
        return

    def Probe_Current_Position(self):
        #get settings
        output_file_name = self._settings.get(["output_file_name"])
        probing_mode = self._settings.get(["probing_mode"])
        noWrite = self._settings.get(["noWrite"])
        maxPartHeight = self._settings.get(["maxPartHeight"])

        #check if printer connected
        if not self._printer.is_operational():
            self._logger.info("Printer is not connected, cannot probe current position")
            return

        self._logger.info(f"Running Probe_Current_Position function with output file name {output_file_name}, probing mode {probing_mode}, and noWrite mode {noWrite}, with max part height {maxPartHeight}")

        #check z height of printhead, wait to move if not there
        CurrentHeadPosition = self.Get_Head_Position()
        if CurrentHeadPosition[2] != maxPartHeight + 25:
            self._logger.info(f"Head is not at max part height, moving to max part height {maxPartHeight}")
            self.ok_response = False
            self._printer.commands(f"G1 Z{maxPartHeight + 25}")
            while not self.ok_response:
                pass

        #run probe command and wait for it to finish completely
        self.g30_response = False
        self._printer.commands("G30")
        while not self.g30_response:
            pass

        #now that we hit something, record the probed position
        CurrentHeadPosition = self.Get_Head_Position()
        self._logger.info(f"Head Position after G30: {CurrentHeadPosition}")

        #write recent probe to file and update frontend var
        self.Write_To_File(CurrentHeadPosition[0], CurrentHeadPosition[1], CurrentHeadPosition[2], CurrentHeadPosition[3], CurrentHeadPosition[4], CurrentHeadPosition[5])
        self.lastProbedPoint = {CurrentHeadPosition[0], CurrentHeadPosition[1], CurrentHeadPosition[2]}

        #move printhead back up to the safe z level
        self.ok_response = False
        self._printer.commands(f"G1 Z{maxPartHeight + 25}")
        while not self.ok_response:
            pass
        
        return

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
        
        #return updated headpos
        return self.headpos

    
    def Write_To_File(self, x_value, y_value, z_value, a_value, b_value, c_value):
        #if noWrite mode is on, return
        if self._settings.get(["noWrite"]) == True:
            self._logger.info("noWrite mode is on, not writing to file")
            return
        output_dir = os.path.join(os.getcwd(), "OctoCMM")
        if not os.path.exists(output_dir):
            os.mkdir(output_dir)
        output_file_name = "OctoCMM/OctoCMM_{}".format(self._settings.get(["output_file_name"]))
        #check if file exists, if not create one
        if not os.path.exists(output_file_name):
            self._logger.info(f"File {output_file_name} does not exist, creating it now, directory: {os.getcwd()}")
            open(output_file_name, 'x')
            #write header line
            with open(output_file_name, 'a') as f:
                f.write("File Generated By OctoCMM, each entry is an x,y,z coordinate pair for a position recorded as the surface of the part, then the time the data was recorded. ABC values are from m114 output\n")
                f.write("X,Y,Z,A,B,C,Time\n")
                f.close()
        
        #write data to file
        self._logger.info(f"Writing data to file {output_file_name}, in {os.getcwd()}")
        with open(output_file_name, 'a') as f:
            write_var = f"{x_value},{y_value},{z_value},{a_value},{b_value},{c_value},{datetime.datetime.now().strftime('%H:%M:%S')}\n"
            f.write(write_var)
            f.close()

    def parse_gcode_responses(self, comm, line, *args, **kwargs):
        #checks for M114 response
        pattern = r"ok X:\d+\.\d{1,4} Y:\d+\.\d{1,4} Z:\d+\.\d{1,4} E:\d+\.\d{1,4} Count: A:\d+ B:\d+ C:\d+"
        if re.match(pattern, line):
            #parse line for x,y,z values
            self._logger.info(f"Received M114 response: {line}")
            self.parse_m114_response(line)
            return line

        pattern = r"ok X:\d{1,4}\.\d{1,4} Y:\d{1,4}\.\d{1,4} Z:\d{1,4}\.\d{1,4} E:\d{1,4}\.\d{1,4} Count: A:\d{1,4} B:\d{1,4} C:\d{1,4}"
        if re.match(pattern, line):
            #G30 return code, ignore for now and set flag
            self._logger.info(f"Received G30 response: {line}")
            self.g30_response = True

        pattern = r"ok"
        if re.match(pattern, line):
            self.ok_response = True
            return line

    def parse_m114_response(self, line):
        x_value = re.search(r"X:(\d+\.\d{1,2})", line).group(1)
        y_value = re.search(r"Y:(\d+\.\d{1,2})", line).group(1)
        z_value = re.search(r"Z:(\d+\.\d{1,2})", line).group(1)
        a_value = re.search(r"A:(\d+)", line).group(1)
        b_value = re.search(r"B:(\d+)", line).group(1)
        c_value = re.search(r"C:(\d+)", line).group(1)
        self._logger.info(f"M114 parsed: X: {x_value}, Y: {y_value}, Z: {z_value}, A: {a_value}, B: {b_value}, C: {c_value}")
        self.headpos = [x_value, y_value, z_value, a_value, b_value, c_value]
        self._logger.info(f"recent headpos from parse_m114 {self.headpos}")
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