# -*- coding: utf-8 -*-
# 2019 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models


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
            try:
                self.env.cr.savepoint()
                self.env.cr.execute("""
                    UPDATE public.wua_flowmeter
                    SET with_gis_flowmeter = FALSE
                """)
                self.env.cr.execute("""
                    UPDATE public.wua_flowmeter wf1
                    SET with_gis_flowmeter = TRUE
                    FROM public.wua_gis_flowmeter wgf1 WHERE
                    wf1.name = wgf1.name;
                """)
                self.env.cr.commit()
                self.env.invalidate_all()
            except Exception:
                self.env.cr.rollback()
                gis_flowmeter_ok = False
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
            try:
                self.env.cr.savepoint()
                self.env.cr.execute("""
                    UPDATE public.wua_intake
                    SET with_gis_intake = FALSE
                """)
                self.env.cr.execute("""
                    UPDATE public.wua_intake wi1
                    SET with_gis_intake = TRUE
                    FROM public.wua_gis_intake wgi1 WHERE
                    wi1.intake_code = wgi1.code;
                """)
                self.env.cr.commit()
                self.env.invalidate_all()
            except Exception:
                self.env.cr.rollback()
                gis_intake_ok = False
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
