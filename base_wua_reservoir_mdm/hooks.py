# -*- coding: utf-8 -*-
# 2025 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import logging

_logger = logging.getLogger(__name__)


def uninstall_hook(cr, registry):
    """Delete transformation templates created by this module."""
    _logger.info('Running uninstall hook for base_wua_reservoir_mdm')

    xmlids_to_delete = [
        'base_wua_reservoir_mdm.mdm_sensor_type_pressure_mca',
        'base_wua_reservoir_mdm.transform_template_sensor_to_reservoirreading',
        'base_wua_reservoir_mdm.action_transform_reservoir_readings',
        'base_wua_reservoir_mdm.cron_transform_reservoir_readings',
    ]
    for xmlid in xmlids_to_delete:
        try:
            cr.execute(
                "DELETE FROM ir_model_data WHERE "
                "module='base_wua_reservoir_mdm' AND name='%s'" %
                xmlid.split('.')[1],
            )
            _logger.info('Deleted xmlid: %s', xmlid)
        except Exception as e:
            _logger.warning('Error deleting xmlid %s: %s', xmlid, str(e))
