odoo.define('base_wua_infrastructure.data_model', function (require) {
    "use strict";

    var Model = require('web.Model');
    var session = require('web.session');
    var pyeval = require('web.pyeval');

    Model.include({
        call: function (method, args, kwargs, options) {
            args = args || [];
            kwargs = kwargs || {};
            if (!_.isArray(args)) {
                kwargs = args;
                args = [];
            }
            pyeval.ensure_evaluated(args, kwargs);
            var call_kw = '/web/dataset/call_kw/' + this.name + '/' + method;
            if (this.name === 'res.partner.waterconnection' &&
                    method === 'search_read' && kwargs?.context?.partner_id) {
                args[0] = [
                    ['partner_id', '=', kwargs.context.partner_id],
                ];
            } else if (this.name === 'res.partner.waterconnection' &&
                    method === 'read' && kwargs?.context?.waterconnection_id_kanban) {
                method = 'search_read';
                args[0] = [
                    ['waterconnection_id.name', '=', kwargs.context.waterconnection_id_kanban],
                    ['partner_id', '=', kwargs.context.partner_id],
                ];
            }
            return session.rpc(call_kw, {
                model: this.name,
                method: method,
                args: args,
                kwargs: kwargs
            }, options);
        },
        call_button: function (method, args) {
            pyeval.ensure_evaluated(args, {});
            if (this.name === 'res.partner.waterconnection') {
                // Get the row and then get the waterconnection id
                if (args[1].view_type === 'kanban' && args[1].waterconnection_id === 'wc_name') {
                    // const waterconnections_contexts = $.find('a[data-context="{\'waterconnection_id\': \'wc_name\', \'view_type\': \'kanban\'}"]')
                    // waterconnections_contexts.forEach(wc => {
                    //     const kanban_card = $(wc.closest('div.o_kanban_card_content.o_kanban_record'));
                    //     const wc_name = kanban_card.find('h4')[0].textContent.trim();
                    //     wc.setAttribute('data-context', wc.getAttribute('data-context').replace('wc_name', wc_name))
                    //     args[1].waterconnection_id = wc_name;
                    // });
                } else if (args[1].view_type !== 'kanban' && args[1].waterconnection_id) {
                    args[1].waterconnection_id = parseInt($(`tr[data-id="${args[0][0]}"] > td[data-field="waterconnection_id"] > a`).first().attr('data-many2one-clickable-id'));
                }
            }
            return session.rpc('/web/dataset/call_button', {
                model: this.name,
                method: method,
                // Should not be necessary anymore. Integrate remote in this?
                domain_id: null,
                context_id: args.length - 1,
                args: args || []
            });
        },
    });
});
