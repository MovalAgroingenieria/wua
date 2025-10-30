# -*- coding: utf-8 -*-
# 2025 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, SUPERUSER_ID
import logging

_logger = logging.getLogger(__name__)


def uninstall_hook(cr, registry):
    env = api.Environment(cr, SUPERUSER_ID, {})
    # External IDs to force delete
    module = 'base_wua_waterpipe_measurement_mdm'
    xmlids_to_delete = [
        '%s.transform_template_sensor_to_flowreading' % module,
        '%s.transform_template_sensor_to_waterpipeflowreading' % module,
        '%s.mdm_sensor_type_flowmeter_totalizer' % module,
    ]
    for xmlid in xmlids_to_delete:
        try:
            record = env.ref(xmlid, raise_if_not_found=False)
            if record:
                _logger.info('Force unlinking record: %s', xmlid)
                record.with_context(force_unlink=True).unlink()
        except Exception as e:
            _logger.warning(
                'Could not force unlink record %s: %s', xmlid, str(e),
            )
