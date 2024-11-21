# -*- coding: utf-8 -*-
# 2024 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import http
from odoo.http import request


class AttendanceController(http.Controller):
    # Helper method in case website module is not installed

    @http.route('/attendance', type='http', auth='user', methods=['GET'],
                csrf=False, website=True)
    def open_attendance(self, **kwargs):
        current_user = request.env.user
        assembly_id = int(kwargs.get('assembly_id'))
        participant_id = int(kwargs.get('participant_id'))
        if current_user:
            attendance = request.env['wua.attendance'].search([
                ('participant_id', '=', participant_id),
                ('assembly_id', '=', assembly_id)
            ])
            if attendance:
                return request.redirect(
                    '/web#id=%s&view_type=form&action=base_wua_assembly.'
                    'wua_raw_attendances_action_qr&model=wua.attendance'
                    '&active_id=%s' % (attendance.id, assembly_id))
            else:
                return "Attendance record not found."
        else:
            return "User not authenticated."
