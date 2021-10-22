# -*- coding: utf-8 -*-
# 2021 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, SUPERUSER_ID, exceptions, _


def pre_init_hook(cr):
    env = api.Environment(cr, SUPERUSER_ID, {})
    exists_wua_gis_parcel = True
    try:
        env.cr.execute('SELECT name, geom FROM public.wua_gis_parcel LIMIT 1')
    except Exception:
        raise exceptions.MissingError(
            _('ATTENTION: it is not possible to install this module, because '
              'the table "wua_gis_parcel" does not exist (the parcels do not '
              'have GIS links).'))
    if not exists_wua_gis_parcel:
        raise exceptions.MissingError(
            _('ATTENTION: it is not possible to install this module, because '
              'the table "wua_gis_parcel" does not exist (the parcels do not '
              'have GIS links).'))


def uninstall_hook(cr, registry):
    env = api.Environment(cr, SUPERUSER_ID, {})
    try:
        env.cr.savepoint()
        env.cr.execute("""
            DELETE FROM ir_values
            WHERE model='wua.vegetationindex.configuration' AND
            (name='enable_remotesensing' OR
            name='remotesensing_key' OR
            name='url_api_fis' OR
            name='url_wms' OR
            name='initial_date')""")
        env.cr.commit()
    except Exception:
        env.cr.rollback()
