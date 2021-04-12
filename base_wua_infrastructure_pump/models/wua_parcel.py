# -*- coding: utf-8 -*-
# 2020 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models
import logging


class WuaParcel(models.Model):
    _inherit = 'wua.parcel'

    # Expand original method
    def set_gis_fields(self):
        gis_parcels_ok = super(WuaParcel, self).set_gis_fields()
        # @INFO: The original method return False if gis_parcels_ok
        #        or gis_irrigationsheds_ok or gis_irrigationditch_ok
        #        fail. Only gis_parcels_ok is needed, but if any fail
        #        the return is False.
        # Temporally do not check the return
        # if (not gis_parcels_ok):
        #    return False
        # Check pumpgrouops
        gis_pumpgroup_ok = False
        self.env.cr.execute("""
            SELECT EXISTS(SELECT * FROM information_schema.tables
            WHERE table_name='wua_gis_pumpgroup')
            """)
        if self.env.cr.fetchone()[0]:
            gis_pumpgroup_ok = True
        if gis_pumpgroup_ok:
            self.env.cr.execute("""
                SELECT code, geom FROM public.wua_gis_pumpgroup
                """)
            gis_pumpgroups = self.env.cr.fetchall()
            if gis_pumpgroups:
                pumpgroups = self.env['wua.pumpgroup'].search([])
                number_of_gis_pumpgroups = len(gis_pumpgroups)
                number_of_pumpgroups = len(pumpgroups)
                self.env.cr.execute("""
                    UPDATE public.wua_pumpgroup
                    SET with_gis_pumpgroup = FALSE
                    """)
                for gis_pumpgroup in gis_pumpgroups:
                    code = gis_pumpgroup[0]
                    filtered_pumpgroups = \
                        pumpgroups.filtered(
                            lambda x: x.pumpgroup_code == code)
                    if len(filtered_pumpgroups) == 1:
                        pumpgroup = filtered_pumpgroups[0]
                        pumpgroup.write({
                            'with_gis_pumpgroup': True
                        })
                _logger = logging.getLogger(self.__class__.__name__)
                _logger.info('Matching GIS info...')
                _logger.info('Number of Odoo-pumpgroups: ' +
                             str(number_of_pumpgroups))
                _logger.info('Number of GIS-pumpgroups : ' +
                             str(number_of_gis_pumpgroups))
        # Check photovoltaicplants
        gis_photovoltaicplant_ok = False
        self.env.cr.execute("""
            SELECT EXISTS(SELECT * FROM information_schema.tables
            WHERE table_name='wua_gis_photovoltaicplant')
            """)
        if self.env.cr.fetchone()[0]:
            gis_photovoltaicplant_ok = True
        if gis_photovoltaicplant_ok:
            self.env.cr.execute("""
                SELECT code, geom FROM public.wua_gis_photovoltaicplant
                """)
            gis_photovoltaicplants = self.env.cr.fetchall()
            if gis_photovoltaicplants:
                photovoltaicplants = self.env['wua.photovoltaicplant'].search(
                    [])
                number_of_gis_photovoltaicplants = len(gis_photovoltaicplants)
                number_of_photovoltaicplants = len(photovoltaicplants)
                self.env.cr.execute("""
                    UPDATE public.wua_photovoltaicplant
                    SET with_gis_photovoltaicplant = FALSE
                    """)
                for gis_photovoltaicplant in gis_photovoltaicplants:
                    code = gis_photovoltaicplant[0]
                    filtered_photovoltaicplants = \
                        photovoltaicplants.filtered(
                            lambda x: x.photovoltaicplant_code == code)
                    if len(filtered_photovoltaicplants) == 1:
                        photovoltaicplant = filtered_photovoltaicplants[0]
                        photovoltaicplant.write({
                            'with_gis_photovoltaicplant': True
                        })
                _logger = logging.getLogger(self.__class__.__name__)
                _logger.info('Matching GIS info...')
                _logger.info('Number of Odoo-photovoltaicplants: ' +
                             str(number_of_photovoltaicplants))
                _logger.info('Number of GIS-photovoltaicplants : ' +
                             str(number_of_gis_photovoltaicplants))
        return gis_parcels_ok and gis_pumpgroup_ok and gis_photovoltaicplant_ok
