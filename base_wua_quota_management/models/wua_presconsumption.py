# -*- coding: utf-8 -*-
# 2020 - Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models


class WuaPresconsumption(models.Model):
    _inherit = 'wua.presconsumption'

    # This funcion gets the pressurized consumptions of a water connection,
    # (type='waterconnection'), a irrigation shed (type='irrigationshed')
    # or a hydraulic sector (type='hydraulicsector'). If the
    # "active_agriculturalseason" parameter is True, the consumptions
    # will be from the active agricultural season.
    def get_presconsumptions(self, id, active_agriculturalseason,
                             type='waterconnection'):
        resp = []
        condition = [('waterconnection_id', '=', id)]
        if type == 'irrigationshed':
            condition = [('irrigationshed_id', '=', id)]
        if type == 'hydraulicsector':
            condition = [('hydraulicsector_id', '=', id)]
        agriculturalseason_ok = True
        if active_agriculturalseason:
            agriculturalseason = self.env['wua.agriculturalseason'].search(
                [('active_agriculturalseason', '=', True)])
            if agriculturalseason:
                condition.append(
                    ('agriculturalseason_id', '=', agriculturalseason.id))
            else:
                agriculturalseason_ok = False
        if agriculturalseason_ok:
            resp = self.search(condition, order='reading_end_time')
        return resp
