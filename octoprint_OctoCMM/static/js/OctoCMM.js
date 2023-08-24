$(function() {
    function OctoCMMViewModel(parameters) {
    

    var cmm_data = ko.observable("State: x | LastPos: x,x,x");

    self.Run_CMM_Probing_JS = function() {
        console.log("Run_CMM_Probing_JS function called");

        $.ajax({
            url: "/api/plugin/OctoCMM",
            type: "GET",
            dataType: "json",
            data: {command: "start_probing"},
            contentType: "application/json; charset=UTF-8"
        }).done(function(result) {
            console.log("Result:", result);
        }).fail(function(jqXHR, textStatus, errorThrown) {
            console.error("Error:", errorThrown);
        });
        
    }}

    self.Probe_Position_JS = function() {
        console.log("Probe_Position_JS function called");

        $.ajax({
            url: "/api/plugin/OctoCMM",
            type: "GET",
            dataType: "json",
            data: {command: "probe_current_position"},
            contentType: "application/json; charset=UTF-8"
        }).done(function(result) {
            console.log("Result:", result);
        }).fail(function(jqXHR, textStatus, errorThrown) {
            console.error("Error:", errorThrown);
        });
        
    }

    self.update_vars = function() {
        console.log("update_vars function called");

        $.ajax({
            url: "/api/plugin/OctoCMM",
            type: "GET",
            dataType: "json",
            data: {command: "update_vars"},
            contentType: "application/json; charset=UTF-8"
        }).done(function(result) {
            console.log("Result:", result);
            data = result;
        }).fail(function(jqXHR, textStatus, errorThrown) {
            console.error("Error:", errorThrown);
        });
        
    }

    OCTOPRINT_VIEWMODELS.push([
        OctoCMMViewModel,

        ["settingsViewModel"],

        ["#tab_plugin_OctoCMM"]
    ]);
});