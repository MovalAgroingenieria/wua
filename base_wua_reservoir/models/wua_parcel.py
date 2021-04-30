# -*- coding: utf-8 -*-
# 2021 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models
import logging


class WuaParcel(models.Model):
    _inherit = 'wua.parcel'

    # Expand and split original method for reservoirs
    def set_gis_fields_reservoir(self):
        gis_reservoir_ok = False
        self.env.cr.execute("""
            SELECT EXISTS(SELECT * FROM information_schema.tables
            WHERE table_name='wua_gis_reservoir')
            """)
        if self.env.cr.fetchone()[0]:
            gis_reservoir_ok = True
        if gis_reservoir_ok:
            self.env.cr.execute("""
                SELECT code, geom FROM public.wua_gis_reservoir
                """)
            gis_reservoirs = self.env.cr.fetchall()
            if gis_reservoirs:
                reservoirs = self.env['wua.reservoir'].search([])
                number_of_gis_reservoirs = len(gis_reservoirs)
                number_of_reservoirs = len(reservoirs)
                self.env.cr.execute("""
                    UPDATE public.wua_reservoir
                    SET with_gis_reservoir = FALSE
                    """)
                for gis_reservoir in gis_reservoirs:
                    code = gis_reservoir[0]
                    filtered_reservoirs = \
                        reservoirs.filtered(
                            lambda x: x.reservoir_code == code)
                    if len(filtered_reservoirs) == 1:
                        reservoir = filtered_reservoirs[0]
                        reservoir.write({
                            'with_gis_reservoir': True
                        })
                _logger = logging.getLogger(self.__class__.__name__)
                _logger.info('Matching GIS info...')
                _logger.info('Number of Odoo-reservoirs: ' +
                             str(number_of_reservoirs))
                _logger.info('Number of GIS-reservoirs : ' +
                             str(number_of_gis_reservoirs))
        return gis_reservoir_ok

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
        gis_reservoir_ok = self.set_gis_fields_reservoir()
        return gis_parcels_ok and gis_reservoir_ok
