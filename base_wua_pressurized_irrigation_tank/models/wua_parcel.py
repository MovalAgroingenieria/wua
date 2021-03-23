# -*- coding: utf-8 -*-
# 2021 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models
import logging


class WuaParcel(models.Model):
    _inherit = 'wua.parcel'

    def set_gis_fields_tank(self):
        gis_tank_ok = False
        self.env.cr.execute("""
            SELECT EXISTS(SELECT * FROM information_schema.tables
            WHERE table_name='wua_gis_tank')
            """)
        if self.env.cr.fetchone()[0]:
            gis_tank_ok = True
        if gis_tank_ok:
            self.env.cr.execute("""
                SELECT name, geom FROM public.wua_gis_tank
                """)
            gis_tanks = self.env.cr.fetchall()
            if gis_tanks:
                tanks = self.env['wua.tank'].search([])
                number_of_gis_tanks = len(gis_tanks)
                number_of_tanks = len(tanks)
                self.env.cr.execute("""
                    UPDATE public.wua_tank
                    SET with_gis_tank = FALSE
                    """)
                for gis_tank in gis_tanks:
                    tank_code = gis_tank[0]
                    filtered_tanks = \
                        tanks.filtered(
                            lambda x: x.tank_code == tank_code)
                    if len(filtered_tanks) == 1:
                        tank = filtered_tanks[0]
                        tank.write({
                            'with_gis_tank': True
                        })
                _logger = logging.getLogger(self.__class__.__name__)
                _logger.info('Matching GIS info...')
                _logger.info('Number of Odoo-tanks: ' +
                             str(number_of_tanks))
                _logger.info('Number of GIS-tanks : ' +
                             str(number_of_gis_tanks))
        return gis_tank_ok

    def set_gis_fields(self):
        gis_parcels_ok = super(WuaParcel, self).set_gis_fields()
        # @INFO: The original method return False if gis_parcels_ok
        #        or gis_irrigationsheds_ok or gis_irrigationditch_ok
        #        fail. Only gis_parcels_ok is needed, but if any fail
        #        the return is False.
        # Temporally do not check the return
        # if (not gis_parcels_ok):
        #    return False
        # Call methods
        gis_tank_ok = self.set_gis_fields_tank()
        return gis_parcels_ok and gis_tank_ok
