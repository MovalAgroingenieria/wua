# -*- coding: utf-8 -*-
# Copyright 2018 Eduardo Iniesta - <einiesta@moval.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import logging
from odoo import api, SUPERUSER_ID


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    _logger = logging.getLogger(__name__)
    """ Each parcel must have a irrigation partner (only for parcels
        with multiple partner-links) """
    resp = update_irrigation_partner(env, version)
    _logger.info('update_irrigation_partner: ' + str(resp) +
                 ' irrigation partners migrated.')
    """ It is necessary to calculate the area percentage of
        subparcels. """
    resp = update_subparcel_percentage(env, version)
    _logger.info('update_subparcel_percentage: ' + str(resp) +
                 ' subparcels migrated.')


def update_irrigation_partner(env, version):
    resp = 0
    parcels = env['wua.parcel'].search([])
    for parcel in parcels:
        partnerlinks = parcel.partnerlink_ids
        if len(partnerlinks) > 0:
            partner_id = partnerlinks[0].partner_id
            partnerlinks[0].irrigation_partner = True
            parcel.partner_id = partner_id
            subparcels = env['wua.parcel.subparcel'].search(
                [('parcel_id', '=', parcel.id)])
            for subparcel in subparcels:
                subparcel.partner_id = partner_id
            resp = resp + 1
    return resp


def update_subparcel_percentage(env, version):
    resp = 0
    parcels = env['wua.parcel'].search([])
    for parcel in parcels:
        subparcels = parcel.subparcel_ids
        if len(subparcels) > 0:
            area_official = parcel.area_official
            if (round(sum(subparcel.area_perc
                          for subparcel in subparcels)) == 0 and
               area_official > 0):
                for subparcel in subparcels:
                    subparcel.area_perc = \
                        (subparcel.area_official * 100) / area_official
                    resp = resp + 1
    return resp
