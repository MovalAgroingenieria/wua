# -*- coding: utf-8 -*-
# 2024 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api, _


class WuaWaterconnectionIrrigationShift(models.Model):
    _inherit = 'wua.waterconnection.irrigation.shift'

    # Qué tipo de campo? Lo necesitamos relacionar con algo?
    # Meter en vista form rellenar manual
    batchline_id = fields.Integer(string='Batchline Id')
    batchline_name = fields.Char('batchline_name')

    # Aux method to get the float hours from a string HH:MM
    def _get_float_hour_from_str(self, hour):
        time_split = hour.split(':')
        hours = float(time_split[0])
        minutes = float(time_split[1]) / 60
        return hours + minutes

    def obtain_shift_info(self, shifts, groups):
        for group in groups:
            for shift in shifts:
                if shift["Id"] in group["Turnos"]:
                    name = group["Descripcion"] + "-" + str(shift["Id"]) + \
                        " " + str(group["Turnos"].index(shift["Id"]))
                    existing_record = \
                        self.env['wua.waterconnection.irrigation.shift'].\
                        search([('name', '=', name)])
                    description = shift["Dias"] + " de"
                    intervals = shift["Intervalos"]
                    for interval in range(1, intervals + 1):
                        start_hour = shift["Intervalo" + str(interval) +
                                            "Inicio"]
                        duration = shift["Intervalo" + str(interval) +
                                            "Duracion"]
                        end_hour = \
                            self._get_float_hour_from_str(start_hour) +\
                            (duration/60)
                        description += " " + start_hour + " a " + \
                            "{:.2f}".format(end_hour)
                    values = {
                        'name': name,
                        'description': description,
                        'batchline_id': shift["Id"],
                        'batchline_name': group["Descripcion"]
                        }
                    if not existing_record:
                        self.create(values)
                    else:
                        existing_record.write(values)
