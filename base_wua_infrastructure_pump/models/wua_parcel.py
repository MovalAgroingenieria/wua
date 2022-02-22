# -*- coding: utf-8 -*-
# 2020 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models


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
            try:
                self.env.cr.savepoint()
                self.env.cr.execute("""
                    UPDATE public.wua_pumpgroup
                    SET with_gis_pumpgroup = FALSE
                """)
                self.env.cr.execute("""
                    UPDATE public.wua_pumpgroup wp1
                    SET with_gis_pumpgroup = TRUE
                    FROM public.wua_gis_pumpgroup wgp1 WHERE
                    wp1.pumpgroup_code = wgp1.code;
                """)
                self.env.cr.commit()
                self.env.invalidate_all()
            except Exception:
                self.env.cr.rollback()
                gis_pumpgroup_ok = False
        # Check photovoltaicplants
        gis_photovoltaicplant_ok = False
        self.env.cr.execute("""
            SELECT EXISTS(SELECT * FROM information_schema.tables
            WHERE table_name='wua_gis_photovoltaicplant')
            """)
        if self.env.cr.fetchone()[0]:
            gis_photovoltaicplant_ok = True
        if gis_photovoltaicplant_ok:
            try:
                self.env.cr.savepoint()
                self.env.cr.execute("""
                    UPDATE public.wua_photovoltaicplant
                    SET with_gis_photovoltaicplant = FALSE
                """)
                self.env.cr.execute("""
                    UPDATE public.wua_photovoltaicplant wp1
                    SET with_gis_photovoltaicplant = TRUE
                    FROM public.wua_gis_photovoltaicplant wgp1 WHERE
                    wp1.photovoltaicplant_code = wgp1.code;
                """)
                self.env.cr.commit()
                self.env.invalidate_all()
            except Exception:
                self.env.cr.rollback()
                gis_photovoltaicplant_ok = False
        return gis_parcels_ok and gis_pumpgroup_ok and gis_photovoltaicplant_ok
