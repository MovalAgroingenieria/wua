odoo.define('wua_remotecontrol_rest_batchline_irriweb_tank.button_import_tankconsumptions',
  (require) => {
    const ListView = require('web.ListView');
    const Model = require('web.DataModel');
    const core = require('web.core');

    ListView.include({
      render_buttons() {
        this._super.apply(this, arguments);
        if (this.$buttons) {
          const btn = this.$buttons.find('.button_import_tankconsumptions');
          btn.on('click', this.proxy('do_button_import_tankconsumptions'));
        }
      },
      do_button_import_tankconsumptions() {
        const { _t } = core;
        const message = _t('Import Tankconsumptions?');
        const confirmed = confirm(message);
        if (confirmed) {
          const pythonFunction = new Model('wua.tankconsumption')
            .call('do_import_tankconsumptions', []);
          pythonFunction.done((result) => {
            const titleNumberOfTankconsumptions = _t('Number of tankconsumptions');
            const titleErrorMessage = _t('WARNING');
            const numberOfTankconsumptions = result[1];
            const errorMessage = result[2];
            let resultMessage = `${titleNumberOfTankconsumptions}: ${
              numberOfTankconsumptions.toString()}`;
            if (errorMessage !== '') {
              resultMessage = `${resultMessage}\n\n${
                titleErrorMessage}: ${
                errorMessage}`;
            }
            window.alert(resultMessage);
            if (numberOfTankconsumptions > 0) {
              window.location.reload(false);
            }
          });
        }
      },
    });
  });
