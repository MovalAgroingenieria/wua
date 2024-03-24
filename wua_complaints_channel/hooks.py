# -*- coding: utf-8 -*-
# 2024 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, SUPERUSER_ID


def post_init_hook(cr, registry):
    env = api.Environment(cr, SUPERUSER_ID, {})
    # Deactivate link types "no-wua".
    linktypes = env['cim.link.type'].sudo()
    link_type_exemployee = linktypes.browse(
        env.ref('cim_complaints_channel.cim_link_type_exemployee').id)
    if (link_type_exemployee and
       (not link_type_exemployee.complaint_ids)):
        link_type_exemployee.active = False
    link_type_self_employed = linktypes.browse(
        env.ref('cim_complaints_channel.cim_link_type_self_employed').id)
    if (link_type_self_employed and
       (not link_type_self_employed.complaint_ids)):
        link_type_self_employed.active = False
    link_type_collaborator = linktypes.browse(
        env.ref('cim_complaints_channel.cim_link_type_collaborator').id)
    if (link_type_collaborator and
       (not link_type_collaborator.complaint_ids)):
        link_type_collaborator.active = False
    link_type_executive = linktypes.browse(
        env.ref('cim_complaints_channel.cim_link_type_executive').id)
    if (link_type_executive and
       (not link_type_executive.complaint_ids)):
        link_type_executive.active = False
    link_type_trainee_staff = linktypes.browse(
        env.ref('cim_complaints_channel.cim_link_type_trainee_staff').id)
    if (link_type_trainee_staff and
       (not link_type_trainee_staff.complaint_ids)):
        link_type_trainee_staff.active = False
