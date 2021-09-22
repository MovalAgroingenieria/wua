# -*- coding: utf-8 -*-
# 2021 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, SUPERUSER_ID


def post_init_hook(cr, registry):
    env = api.Environment(cr, SUPERUSER_ID, {})
    values = env['ir.values'].sudo()
    # Initialize the "sequence_certificate_code_id" param (Many2one)
    sequence_certificate_code_id = 0
    try:
        sequence_certificate_code_id = env.ref(
            'base_wua_certificate.sequence_certificate_code').id
    except:
        sequence_certificate_code_id = 0
    if sequence_certificate_code_id > 0:
        values.set_default('wua.configuration',
                           'sequence_certificate_code_id',
                           sequence_certificate_code_id)
    # Initialize the "default_certificatetype_id" param (Many2one)
    default_certificatetype_id = 0
    try:
        default_certificatetype_id = env.ref(
            'base_wua_certificate.certificatetype_no_variation').id
    except:
        default_certificatetype_id = 0
    if default_certificatetype_id > 0:
        values.set_default('wua.configuration',
                           'default_certificatetype_id',
                           default_certificatetype_id)
    # Initialize the "portaluser_certificatetype_id" param (Many2one)
    portaluser_certificatetype_id = 0
    try:
        portaluser_certificatetype_id = env.ref(
            'base_wua_certificate.certificatetype_no_variation').id
    except:
        portaluser_certificatetype_id = 0
    if portaluser_certificatetype_id > 0:
        values.set_default('wua.configuration',
                           'portaluser_certificatetype_id',
                           portaluser_certificatetype_id)
    # Initialize html fields (problem in data file)
    standard_certificatetype = None
    try:
        standard_certificatetype = env.ref(
            'base_wua_certificate.certificatetype_no_variation')
    except:
        standard_certificatetype = None
    if standard_certificatetype:
        standard_certificatetype.write({
            'notes': '<p>Default certificate for <b>ALL</b> partners. This '
                     'certificate type contains the parcels related to the '
                     'partner and the most relevant data to justify their '
                     'rights.<br></p>',
            'main_page': '<p style="text-align: center;"><b>'
                         '<font style="font-size: 14px;">'
                         '{{ certificate.name_of_signer.upper() }}, '
                         'SECRETARY OF {{ partner.company_id.name.upper() }}'
                         '</font></b></p><p><br></p>'
                         '<p style="text-align: center;"><u><b>'
                         '<font style="font-size: 18px;">CERTIFY:</font></b>'
                         '</u></p><p><br></p><p>That '
                         '<b>{{ partner.name }}</b>, located at '
                         '<b>{{ partner.street }}, {{partner.city}} '
                         '-{{partner.state_id.name}}-</b>, and holder of '
                         'identity document number <b>{{ partner.vat }}</b> '
                         'is enrolled in the census of this water users '
                         'association, with the parcels listed on the next '
                         'page. These parcels are authorized for the use of '
                         'the water distributed by this corporation, for '
                         'agricultural irrigation.<br></p><p><br></p><p>'
                         'And as evidence thereof, I hereby issue this '
                         'certificate in {{ partner.company_id.city }} on '
                         '{{ current_month }} {{ current_day }}th, '
                         '{{ current_year }}.<br></p>'
        })


def uninstall_hook(cr, registry):
    env = api.Environment(cr, SUPERUSER_ID, {})
    try:
        env.cr.savepoint()
        env.cr.execute("""
            DELETE FROM ir_values
            WHERE model='wua.configuration' AND
            (name='sequence_certificate_code_id' OR
            name='only_parcels_as_main' OR
            name='default_certificatetype_id' OR
            name='allowed_request_for_portal_user' OR
            name='portaluser_certificatetype_id' OR
            name='max_pending_certificates')""")
        env.cr.commit()
    except Exception:
        env.cr.rollback()
