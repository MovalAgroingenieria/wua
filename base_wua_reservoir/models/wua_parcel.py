# -*- coding: utf-8 -*-
# 2021 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models


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
            try:
                self.env.cr.savepoint()
                self.env.cr.execute("""
                    UPDATE public.wua_reservoir
                    SET with_gis_reservoir = FALSE
                """)
                self.env.cr.execute("""
                    UPDATE public.wua_reservoir wr1
                    SET with_gis_reservoir = TRUE
                    FROM public.wua_gis_reservoir wgr1 WHERE
                    wr1.reservoir_code = wgr1.code;
                """)
                self.env.cr.commit()
                self.env.invalidate_all()
            except Exception:
                self.env.cr.rollback()
                gis_reservoir_ok = False
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
