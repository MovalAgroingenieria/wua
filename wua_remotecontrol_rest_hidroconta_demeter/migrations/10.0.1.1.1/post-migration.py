# -*- coding: utf-8 -*-
# 2022 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, SUPERUSER_ID


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    values = env['ir.values'].sudo()
    url_remotecontrol_rest = values.get_default(
        'wua.irrigation.configuration', 'url_remotecontrol_rest')
    url_remotecontrol_rest_username = values.get_default(
        'wua.irrigation.configuration', 'url_remotecontrol_rest_username')
    url_remotecontrol_rest_password = values.get_default(
        'wua.irrigation.configuration', 'url_remotecontrol_rest_password')
    automatic_census_synchronization = values.get_default(
        'wua.irrigation.configuration', 'automatic_census_synchronization')
    url_remotecontrol_application = values.get_default(
        'wua.irrigation.configuration', 'url_remotecontrol_application')
    if (url_remotecontrol_rest):
        values.set_default(
            'wua.irrigation.configuration',
            'url_remotecontrol_rest_hidroconta', url_remotecontrol_rest)
    if (url_remotecontrol_rest_username):
        values.set_default(
            'wua.irrigation.configuration',
            'url_remotecontrol_rest_username_hidroconta',
            url_remotecontrol_rest_username)
    if (url_remotecontrol_rest_password):
        values.set_default(
            'wua.irrigation.configuration',
            'url_remotecontrol_rest_password_hidroconta',
            url_remotecontrol_rest_password)
    if (automatic_census_synchronization):
        values.set_default(
            'wua.irrigation.configuration',
            'automatic_census_synchronization_hidroconta',
            automatic_census_synchronization)
    if (url_remotecontrol_application):
        values.set_default(
            'wua.irrigation.configuration',
            'url_remotecontrol_application_hidroconta',
            url_remotecontrol_application)
