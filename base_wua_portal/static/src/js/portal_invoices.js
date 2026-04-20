odoo.define('your_module.portal_invoices', function (require) {
    "use strict";

    var $ = window.jQuery;

    function updateButtonVisibility() {
        var checked = $('input[name="invoice_ids"]:checked');
        var btn = $('#print_btn');

        if (!btn.length) return;

        if (checked.length > 0) {
            btn.show();
        } else {
            btn.hide();
        }
    }

    $(document).on('change', 'input[name="invoice_ids"]', function () {
        updateButtonVisibility();
    });

    $(document).on('change', '#select_all', function () {
        var checked = $(this).prop('checked');
        $('input[name="invoice_ids"]').prop('checked', checked);
        updateButtonVisibility();
    });

    $(function () {
        updateButtonVisibility();
    });
});