$(function() {
    function OctoCMMViewModel(parameters) {

        self.Run_CMM_Probing_JS = function() {
            console.log("Run_CMM_Probing_JS function called");
        };

        self.Probe_Position_JS = function() {
            console.log("Prob_Position_JS function called");
        };

    }

    OCTOPRINT_VIEWMODELS.push([
        OctoCMMViewModel,

        ["settingsViewModel"],

        ["#tab_plugin_OctoCMM"]
    ]);
});