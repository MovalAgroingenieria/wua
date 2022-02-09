# -*- coding: utf-8 -*-
# 2022 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import tempfile
from contextlib import closing
import os
import glob
import subprocess

from odoo import models, exceptions, _
from odoo.addons.report.models.report import Report as Reportbaseclass


def _normalize_filepath(path):
    path = path or ''
    path = path.strip()
    if not os.path.isabs(path):
        return False
    path = os.path.normpath(path)
    return path if os.path.exists(path) else False


class Report(models.Model):
    _inherit = 'report'

    PAGE_OF_SIGNATURE = 1
    LLX_FOR_SIGNATURE = 30
    LLY_FOR_SIGNATURE = 70
    URX_FOR_SIGNATURE = 225
    URY_FOR_SIGNATURE = 193
    MAX_SIGNATURES = 2
    COLUMN_SPACING = 110
    FIT_IMAGE = True

    def all_signatures_ok(self, certificate_id):
        resp = False
        certificate = self.env['wua.certificate'].browse(certificate_id)
        if certificate and certificate.certificateuser_ids:
            resp = True
            for certificateuser in certificate.certificateuser_ids:
                if not certificateuser.signed:
                    resp = False
                    break
        return resp

    def get_pdf(self, docids, report_name, html=None, data=None):
        resp = False
        certificates = None
        call_parent_method = True
        report = self._get_report_from_name(report_name)
        if report and report.model == 'wua.certificate':
            certificates = self.env['report.certificate'].search([
                ('company_id', '=', self.env.user.company_id.id),
                ('model_id', '=', 'wua.certificate'),
            ])
            if certificates:
                call_parent_method = False
        if call_parent_method:
            resp = super(Report, self).get_pdf(
                docids, report_name, html=html, data=data)
        else:
            if self.all_signatures_ok(docids[0]):
                content = Reportbaseclass.get_pdf(
                    self, docids, report_name, html=html, data=data)
                all_signers_have_electronic_sign = True
                for certificate in certificates:
                    p12 = _normalize_filepath(certificate.path)
                    passwd = _normalize_filepath(certificate.password_file)
                    if not (p12 and passwd):
                        all_signers_have_electronic_sign = False
                        break
                if all_signers_have_electronic_sign:
                    show_sign = \
                        self.env['ir.values'].get_default(
                            'wua.configuration', 'show_sign')
                    signature_parameters = self._get_signature_parameters()
                    max_signatures = signature_parameters['max_signatures']
                    if max_signatures < 1:
                        max_signatures = 1
                    number_of_signature = 1
                    for certificate in certificates:
                        pdf_fd, pdf = tempfile.mkstemp(
                            suffix='.pdf', prefix='report.tmp.')
                        with closing(os.fdopen(pdf_fd, 'w')) as pf:
                            pf.write(content)
                        if show_sign and number_of_signature <= max_signatures:
                            signed = self.pdf_sign_with_visible_signature(
                                pdf, certificate, signature_parameters,
                                number_of_signature)
                            number_of_signature = number_of_signature + 1
                        else:
                            signed = self.pdf_sign(pdf, certificate)
                        if os.path.exists(signed):
                            with open(signed, 'rb') as pf:
                                content = pf.read()
                        for fname in (pdf, signed):
                            try:
                                os.unlink(fname)
                            except Exception:
                                pass
                resp = content
        return resp

    def pdf_sign_with_visible_signature(self, pdf, certificate,
                                        signature_parameters,
                                        number_of_signature=1):
        # Data of certificate
        p12_file = _normalize_filepath(certificate.path)
        passwd_file = _normalize_filepath(certificate.password_file)
        if not (p12_file and passwd_file):
            raise exceptions.UserError(
                _('Signing report (PDF): '
                  'Certificate or password file not found'))
        with open(passwd_file, 'rb') as pf:
            passwd = pf.readline().rstrip()
        # Background image
        background_img = self._get_background_img(os.path.dirname(p12_file))
        # Jar file
        current_dir = os.path.dirname(__file__)
        jar_path = current_dir + '/../static/jar'
        jar_file = jar_path + '/JSignPdf.jar'
        # Output dir
        output_dir = os.path.dirname(pdf)
        # Parameters
        page_of_signature = signature_parameters['page_of_signature']
        column_spacing = signature_parameters['column_spacing']
        llx_for_signature = signature_parameters['llx_for_signature']
        urx_for_signature = signature_parameters['urx_for_signature']
        width_for_signature = (urx_for_signature - llx_for_signature) + \
            column_spacing
        if number_of_signature > 1:
            llx_for_signature = (number_of_signature - 1) * width_for_signature
            urx_for_signature = llx_for_signature + urx_for_signature
        lly_for_signature = signature_parameters['lly_for_signature']
        ury_for_signature = signature_parameters['ury_for_signature']
        fit_image = signature_parameters['fit_image']
        # Path of signed pdf
        pdf_name = os.path.splitext(pdf)[0]
        pdf_signed = pdf_name + '_signed.pdf'
        # Call the jar file
        append_signature_parameter = ''
        if number_of_signature > 1:
            append_signature_parameter = ' -a'
        exec_line = 'java -Djsignpdf.home=' + jar_path + \
            ' -jar ' + jar_file + \
            append_signature_parameter + \
            ' -ksf ' + p12_file + \
            ' -ksp ' + passwd + \
            ' ' + pdf + \
            ' -d ' + output_dir + \
            ' -q' + \
            ' -pg ' + str(page_of_signature) + \
            ' -V' + \
            ' -llx ' + str(llx_for_signature) + \
            ' -lly ' + str(lly_for_signature) + \
            ' -urx ' + str(urx_for_signature) + \
            ' -ury ' + str(ury_for_signature)
        if background_img:
            bg_scale = 0
            if fit_image:
                bg_scale = -1
            exec_line = exec_line + \
                ' --bg-path ' + background_img + \
                ' --bg-scale ' + str(bg_scale)
        process = subprocess.Popen(exec_line, stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE, shell=True)
        out, err = process.communicate()
        if process.returncode:
            raise exceptions.UserError(
                _('Signing report (PDF): jPdfSign failed (error code: %s). '
                  'Message: %s. Output: %s') %
                (process.returncode, err, out))
        return pdf_signed

    def _get_signature_parameters(self):
        resp = {
            'page_of_signature': self.PAGE_OF_SIGNATURE,
            'llx_for_signature': self.LLX_FOR_SIGNATURE,
            'lly_for_signature': self.LLY_FOR_SIGNATURE,
            'urx_for_signature': self.URX_FOR_SIGNATURE,
            'ury_for_signature': self.URY_FOR_SIGNATURE,
            'max_signatures': self.MAX_SIGNATURES,
            'column_spacing': self.COLUMN_SPACING,
            'fit_image': self.FIT_IMAGE,
            }
        model_ir_values = self.env['ir.values']
        page_of_signature = model_ir_values.get_default('wua.configuration',
                                                        'page_of_signature')
        if page_of_signature > 0:
            resp['page_of_signature'] = page_of_signature
        llx_for_signature = model_ir_values.get_default('wua.configuration',
                                                        'llx_for_signature')
        if llx_for_signature > 0:
            resp['llx_for_signature'] = llx_for_signature
        lly_for_signature = model_ir_values.get_default('wua.configuration',
                                                        'lly_for_signature')
        if lly_for_signature > 0:
            resp['lly_for_signature'] = lly_for_signature
        urx_for_signature = model_ir_values.get_default('wua.configuration',
                                                        'urx_for_signature')
        if urx_for_signature > 0:
            resp['urx_for_signature'] = urx_for_signature
        ury_for_signature = model_ir_values.get_default('wua.configuration',
                                                        'ury_for_signature')
        if ury_for_signature > 0:
            resp['ury_for_signature'] = ury_for_signature
        max_signatures = model_ir_values.get_default('wua.configuration',
                                                     'max_signatures')
        if max_signatures > 0:
            resp['max_signatures'] = max_signatures
        column_spacing = model_ir_values.get_default('wua.configuration',
                                                     'column_spacing')
        if column_spacing > 0:
            resp['column_spacing'] = column_spacing
        fit_image = model_ir_values.get_default('wua.configuration',
                                                'fit_image')
        resp['fit_image'] = fit_image
        return resp

    def _get_background_img(self, path):
        resp = ''
        for file_name in (glob.glob(path + '/*.png') or []):
            resp = file_name
            break
        if not resp:
            for file_name in (glob.glob(path + '/*.jpg') or []):
                resp = file_name
                break
        if not resp:
            for file_name in (glob.glob(path + '/*.jpeg') or []):
                resp = file_name
                break
        return resp
