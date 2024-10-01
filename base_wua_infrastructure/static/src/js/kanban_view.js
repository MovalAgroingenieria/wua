odoo.define('base_wua_infrastructure.KanbanView', function (require) {
    "use strict";


    var KanbanView = require('web_kanban.KanbanView');


    KanbanView.include({

        reload_record: function (record) {
            var self = this;
            const options = {};
            if (this.model === 'res.partner.waterconnection') {
                options.context = {
                    'waterconnection_id_kanban': record.record.waterconnection_id.value,
                };
            }
            this.dataset.read_ids([record.id], this.fields_keys.concat(['__last_update']), options).done(function(records) {
                if (records.length) {
                    record.update(records[0]);
                    self.postprocess_m2m_tags(record);
                } else {
                    record.destroy();
                }
            });
        },

    });

});
