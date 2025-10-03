# -*- coding: utf-8 -*-
# 2025 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import logging
from jinja2 import Template, TemplateError
from odoo import models, fields, api, _


class WuaParcel(models.Model):
    _inherit = "wua.parcel"

    mapped = fields.Boolean(
        string="Mapped",
        default=False,
        readonly=True,
        help="Indicates if this parcel has been mapped with general instance.",
    )

    last_update = fields.Datetime(
        default=False,
        readonly=True,
        help="Date of the last update from with general instance.",
    )

    @api.multi
    def get_parcels_info_from_base_entity(self, jinja2_template):
        # Logging
        _logger = logging.getLogger(self.__class__.__name__)

        # Get parcels
        parcels = self.env["wua.parcel"].search([('active', '=', True)])
        num_of_parcels = len(parcels)
        parcel_info_get_success = 0
        parcel_info_get_failed = 0
        _logger.info("Mapping: Number of parcels found: %d", num_of_parcels)

        # Process parcels
        parcel_info_list = []
        for parcel in parcels:
            parcel_code = parcel.name
            partner = parcel.partner_id
            try:
                partner_info = Template(jinja2_template)
                partner_info = partner_info.render(partner=partner)
                parcel_info_get_success += 1
            except TemplateError as e:
                partner_info = _("ERROR IN TEMPLATE: %s") % e.message
                parcel_info_get_failed += 1
            parcel_info_list.append(
                {"parcel_code": parcel_code,
                 "partner_info": partner_info}
            )

        # Summary logging
        _logger.info("Mapping: Parcels scanned: %d", parcel_info_get_success)
        if parcel_info_get_failed > 0:
            _logger.info("Mapping: Parcels failed: %d", parcel_info_get_failed)

        return parcel_info_list

    @api.multi
    def set_parcel_info_to_base_entity(self, list_of_parcels):
        # Logging
        _logger = logging.getLogger(self.__class__.__name__)

        # Get parcels to set
        num_of_parcels_from_general_entity = len(list_of_parcels)
        parcels = self.env["wua.parcel"].search(
            [("name", "in", list_of_parcels)])
        num_of_parcels = len(parcels)
        parcel_info_set_success = 0
        parcel_info_set_failed = 0
        _logger.info("Mapping: Number of parcels: %d/%d",
                     num_of_parcels, num_of_parcels_from_general_entity)

        # Set others parcels as not mapped (refresh)
        other_parcels = self.env["wua.parcel"].search(
            [("name", "not in", list_of_parcels), ("mapped", "=", True)])
        for other_parcel in other_parcels:
            other_parcel.mapped = False
            other_parcel.last_update = False

        # Set parcels
        for parcel in parcels:
            try:
                parcel.mapped = True
                parcel.last_update = fields.Datetime.now()
                parcel_info_set_success += 1
            except Exception:
                parcel_info_set_failed += 1

        # Summary logging
        _logger.info("Mapping: Parcels successfully mapped: %d",
                     parcel_info_set_success)
        if parcel_info_set_failed > 0:
            _logger.info(
                "Mapping: Parcels failed to map: %d", parcel_info_set_failed)

        return [parcel_info_set_success, parcel_info_set_failed]
