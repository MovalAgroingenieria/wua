# -*- coding: utf-8 -*-
# Copyright 2018 Eduardo Iniesta - <einiesta@moval.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import logging
from odoo import api, SUPERUSER_ID


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    _logger = logging.getLogger(__name__)
    """ Set the codes for hydraylic sectors and irrigation
        ditches. """
    resp = update_hydraulicsector_code(env, version)
    _logger.info('update_hydraulicsector_code: ' + str(resp) +
                 ' hydraulic sectors migrated.')
    resp = update_irrigationditch_code(env, version)
    _logger.info('update_irrigationditch_code: ' + str(resp) +
                 ' irrigation ditches migrated.')
    """ Remove the irrigation points mapped to the irrigation
        gates. """
    resp = remove_irrigationpoint_mapped_to_irrigationgate(env, version,
                                                           _logger)
    _logger.info('remove_irrigationpoint_mapped_to_irrigationgate: ' +
                 str(resp) + ' irrigation points removed.')
    """ Updating of the pressurized irrigation data for parcels/subparcels:
        water connections (parcels), type of infrastructure (parcels) and
        hydraulic sector (parcels and subparcels). """
    resp = update_pressurized_infrastructure(env, version)
    _logger.info('update_pressurized_infrastructure: ' + str(resp) +
                 ' parcels migrated.')


def update_hydraulicsector_code(env, version):
    resp = 0
    hydraulicsectors = env['wua.hydraulicsector'].search([])
    if len(hydraulicsectors) > 0:
        if sum(hydraulicsector.hydraulicsector_code for hydraulicsector
               in hydraulicsectors) == len(hydraulicsectors):
            for hydraulicsector in hydraulicsectors:
                resp = resp + 1
                if resp > 1:
                    hydraulicsector.hydraulicsector_code = resp
    return resp


def update_irrigationditch_code(env, version):
    resp = 0
    irrigationditches = env['wua.irrigationditch'].search([])
    if len(irrigationditches) > 0:
        if sum(irrigationditch.irrigationditch_code for irrigationditch
               in irrigationditches) == len(irrigationditches):
            for irrigationditch in irrigationditches:
                resp = resp + 1
                if resp > 1:
                    irrigationditch.irrigationditch_code = resp
    return resp


def remove_irrigationpoint_mapped_to_irrigationgate(env, version, logger):
    resp = 0
    irrigationpoints = env['wua.parcel.irrigationpoint'].search(
        [('type', '=', 'IG')])
    if len(irrigationpoints) > 0:
        resp = len(irrigationpoints)
        for irrigationpoint in irrigationpoints:
            parcel_name = ''
            irrigationgate_name = ''
            parcels = env['wua.parcel'].browse(irrigationpoint.parcel_id.id)
            if len(parcels) == 1:
                parcel_name = parcels[0].name
            irrigationgates = env['wua.irrigationgate'].browse(
                irrigationpoint.irrigationgate_id.id)
            if len(irrigationgates) == 1:
                irrigationgate_name = irrigationgates[0].name
            logger.info('Irrigation Point removed: irrigationgate = ' +
                        irrigationgate_name + '; parcel_name = ' + parcel_name)
        irrigationpoints.unlink()
    return resp


def update_pressurized_infrastructure(env, version):
    resp = 0
    parcels = env['wua.parcel'].search([])
    subparcels = env['wua.parcel.subparcel']
    irrigationpoints = env['wua.parcel.irrigationpoint']
    irrigationpointswc = env['wua.parcel.irrigationpointwc']
    for parcel in parcels:
        subparcels_of_parcel = subparcels.search(
            [('parcel_id', '=', parcel.id)])
        irrigationpoints_of_parcel = irrigationpoints.search(
            [('parcel_id', '=', parcel.id)])
        hydraulic_infrastructure_type = 0
        if len(irrigationpoints_of_parcel) > 0:
            hydraulic_infrastructure_type = 1
            hydraulicsector = irrigationpoints_of_parcel[0].\
                waterconnection_id.hydraulicsector_id
            parcel.hydraulicsector_id = hydraulicsector
            for subparcel in subparcels_of_parcel:
                subparcel.hydraulicsector_id = hydraulicsector
            pos = 0
            for irrigationpoint in irrigationpoints_of_parcel:
                pos = pos + 1
                irrigationpointwc_code = parcel.name + '-' + str(pos).zfill(2)
                irrigationpointswc.create({
                    'irrigationpointwc_code': irrigationpointwc_code,
                    'parcel_id': parcel.id,
                    'pos': pos,
                    'waterconnection_id': (irrigationpoint.
                                           waterconnection_id.id),
                    })
        parcel.hydraulic_infrastructure_type = hydraulic_infrastructure_type
        resp = resp + 1
    return resp
