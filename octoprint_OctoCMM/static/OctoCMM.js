$(function() {
    function OctoCMMViewModel(parameters) {
        var self = this;

        self.exampleTextField1 = ko.observable();
        self.exampleTextField2 = ko.observable();
        self.exampleButton1 = function() {
            console.log("Example button 1 clicked!");
        };
        self.exampleButton2 = function() {
            console.log("Example button 2 clicked!");
        };

        self.exampleTextField1Data = ko.computed(function() {
            return "Example text field 1 data: " + self.exampleTextField1();
        });
        self.exampleTextField2Data = ko.computed(function() {
            return "Example text field 2 data: " + self.exampleTextField2();
        });

        self.onBeforeBinding = function() {
            self.exampleTextField1("");
            self.exampleTextField2("");
        }
    }

    OCTOPRINT_VIEWMODELS.push([
        OctoCMMViewModel,
        [],
        ["#tab_plugin_OctoCMM"]
    ]);
});