# -*- coding: utf-8 -*-
# 2019 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models
import logging


class WuaParcel(models.Model):
    _inherit = 'wua.parcel'

    # Expand and split original method for flowmeters and intakes
    def set_gis_fields_flowmeter(self):
        gis_flowmeter_ok = False
        self.env.cr.execute("""
            SELECT EXISTS(SELECT * FROM information_schema.tables
            WHERE table_name='wua_gis_flowmeter')
            """)
        if self.env.cr.fetchone()[0]:
            gis_flowmeter_ok = True
        if gis_flowmeter_ok:
            self.env.cr.execute("""
                SELECT name, geom FROM public.wua_gis_flowmeter
                """)
            gis_flowmeters = self.env.cr.fetchall()
            if gis_flowmeters:
                flowmeters = self.env['wua.flowmeter'].search([])
                number_of_gis_flowmeters = len(gis_flowmeters)
                number_of_flowmeters = len(flowmeters)
                self.env.cr.execute("""
                    UPDATE public.wua_flowmeter
                    SET with_gis_flowmeter = FALSE
                    """)
                for gis_flowmeter in gis_flowmeters:
                    name = gis_flowmeter[0]
                    filtered_flowmeters = \
                        flowmeters.filtered(
                            lambda x: x.name == name)
                    if len(filtered_flowmeters) == 1:
                        flowmeter = filtered_flowmeters[0]
                        flowmeter.write({
                            'with_gis_flowmeter': True
                        })
                _logger = logging.getLogger(self.__class__.__name__)
                _logger.info('Matching GIS info...')
                _logger.info('Number of Odoo-Flowmeters: ' +
                             str(number_of_flowmeters))
                _logger.info('Number of GIS-Flowmeters : ' +
                             str(number_of_gis_flowmeters))
        return gis_flowmeter_ok

    def set_gis_fields_intake(self):
        gis_intake_ok = False
        self.env.cr.execute("""
            SELECT EXISTS(SELECT * FROM information_schema.tables
            WHERE table_name='wua_gis_intake')
            """)
        if self.env.cr.fetchone()[0]:
            gis_intake_ok = True
        if gis_intake_ok:
            self.env.cr.execute("""
                SELECT code, geom FROM public.wua_gis_intake
                """)
            gis_intakes = self.env.cr.fetchall()
            if gis_intakes:
                intakes = self.env['wua.intake'].search([])
                number_of_gis_intakes = len(gis_intakes)
                number_of_intakes = len(intakes)
                self.env.cr.execute("""
                    UPDATE public.wua_intake
                    SET with_gis_intake = FALSE
                    """)
                for gis_intake in gis_intakes:
                    intake_code = gis_intake[0]
                    filtered_intakes = \
                        intakes.filtered(
                            lambda x: x.intake_code == intake_code)
                    if len(filtered_intakes) == 1:
                        intake = filtered_intakes[0]
                        intake.write({
                            'with_gis_intake': True
                        })
                _logger = logging.getLogger(self.__class__.__name__)
                _logger.info('Matching GIS info...')
                _logger.info('Number of Odoo-Intakes: ' +
                             str(number_of_intakes))
                _logger.info('Number of GIS-Intakes : ' +
                             str(number_of_gis_intakes))
        return gis_intake_ok

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
        gis_flowmeter_ok = self.set_gis_fields_flowmeter()
        gis_intake_ok = self.set_gis_fields_intake()
        return gis_parcels_ok and gis_flowmeter_ok and gis_intake_ok
