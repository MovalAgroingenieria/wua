odoo.define('base_wua_portal_infrastructure.manage_columns', function (require) {
    "use strict";
    $(document).ready(function () {
        // Handle column visibility based on user selection
        var selectedColumns = JSON.parse(localStorage.getItem('selected_columns')) || [];

        // Default: show all columns if no selection stored
        if (selectedColumns.length === 0) {
            selectedColumns = [
                "water_connection", "description", "last_reading_time", "last_reading_value",
                "volume_real", "last_data_time", "last_total_volume", "last_waterflow",
                "last_valve_open", "last_valve_scheduled"
            ];
        }

        // Update columns visibility based on selected columns
        selectedColumns.forEach(function (column) {
            $(".column-" + column).show();
        });

        // Handle column checkbox changes
        $(".column-toggle").change(function () {
            var columnClass = $(this).data("column");
            var isChecked = $(this).prop("checked");

            if (isChecked) {
                $(".column-" + columnClass).show();
                selectedColumns.push(columnClass);
            } else {
                $(".column-" + columnClass).hide();
                selectedColumns = selectedColumns.filter(function (col) {
                    return col !== columnClass;
                });
            }

            // Save the selected columns to localStorage
            localStorage.setItem('selected_columns', JSON.stringify(selectedColumns));
        });
    });
});
