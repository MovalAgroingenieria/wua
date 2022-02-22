# -*- coding: utf-8 -*-
# 2021 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models


class WuaParcel(models.Model):
    _inherit = 'wua.parcel'

    def set_gis_fields_tank(self):
        gis_tank_ok = False
        gis_tank_ok = False
        self.env.cr.execute("""
            SELECT EXISTS(SELECT * FROM information_schema.tables
            WHERE table_name='wua_gis_tank')
            """)
        if self.env.cr.fetchone()[0]:
            gis_tank_ok = True
        if (gis_tank_ok):
            try:
                self.env.cr.savepoint()
                self.env.cr.execute("""
                    UPDATE public.wua_tank
                    SET with_gis_tank = FALSE
                """)
                self.env.cr.execute("""
                    UPDATE public.wua_tank wt1
                    SET with_gis_tank = TRUE
                    FROM public.wua_gis_tank wgt1 WHERE wt1.name = wgt1.name;
                """)
                self.env.cr.commit()
                self.env.invalidate_all()
            except Exception:
                self.env.cr.rollback()
                gis_tank_ok = False
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
