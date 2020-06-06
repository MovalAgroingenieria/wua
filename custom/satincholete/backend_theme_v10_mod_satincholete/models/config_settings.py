# -*- coding: utf-8 -*-
# 2020 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api
import odoo.tools as tools
import os


class CustomColorConfiguration(models.TransientModel):
    _inherit = 'res.config.settings'
    _name = 'res.backend.settings'

    DEFAULT_PRIMARY_COLOR = "rgba(51,122,183,1)"
    DEFAULT_SIDEBAR_COLOR = "rgba(0,0,0,1)"
    DEFAULT_REPORTS_COLOR = "rgba(51,122,183,1)"

    @api.model_cr
    def init(self):
        varless_file = False
        backendcss_file = False
        addons_path = tools.config['addons_path'].split(',')
        for path in addons_path:
            if '/wua/custom/satincholete' in path \
                    and self._module == 'backend_theme_v10_mod_satincholete':
                path = os.path.dirname(path)
                varless_file = path + '/satincholete/'\
                    'backend_theme_v10_mod_satincholete/static/src/less/'\
                    'variables_mod.less'
                backendcss_file = path + '/satincholete/'\
                    'backend_theme_v10_mod_satincholete/static/src/css/'\
                    'backend_mod.css'
        if not os.path.exists(varless_file):
            with open(varless_file, 'w') as fout:
                fout.write(
                    "@gray-base:             %s;\n"
                    "@brand-primary:         %s;\n"
                    "@brand-info:            %s;\n" %
                    (self.DEFAULT_SIDEBAR_COLOR, self.DEFAULT_PRIMARY_COLOR,
                     self.DEFAULT_PRIMARY_COLOR))
        if not os.path.exists(backendcss_file):
            with open(backendcss_file, 'w') as fout:
                fout.write(".bg-theme-report-color { background-color: %s; }\n"
                           ".theme-report-color { color: %s; }" %
                           (self.DEFAULT_REPORTS_COLOR,
                            self.DEFAULT_REPORTS_COLOR))

    backend_primary_color = fields.Char(
        string="Primary color",
        default=DEFAULT_PRIMARY_COLOR,
        help="The backend theme primary color. Applied to many objects,"
        "navbar, fonts, buttons...")

    sidebar_background_color = fields.Char(
        string="Sidebar color",
        default=DEFAULT_SIDEBAR_COLOR,
        help="The sidebar background color.")

    report_motive_color = fields.Char(
        string="Report color",
        default=DEFAULT_REPORTS_COLOR,
        help="Color for bars, icons and other decoration in reports")

    @api.onchange('backend_primary_color')
    def _onchage_backend_primary_color(self):
        self.report_motive_color = self.backend_primary_color

    @api.multi
    def restore_defaults(self):
        self.backend_primary_color = self.DEFAULT_PRIMARY_COLOR
        self.sidebar_background_color = self.DEFAULT_SIDEBAR_COLOR
        self.report_motive_color = self.DEFAULT_REPORTS_COLOR

    @api.multi
    def set_default_values(self):
        values = self.env['ir.values'].sudo()
        values.set_default('res.backend.settings', 'backend_primary_color',
                           self.backend_primary_color)
        values.set_default('res.backend.settings', 'sidebar_background_color',
                           self.sidebar_background_color)
        values.set_default('res.backend.settings', 'report_motive_color',
                           self.report_motive_color)

        # Change vars in files
        varless_file = False
        backendcss_file = False
        addons_path = tools.config['addons_path'].split(',')
        for path in addons_path:
            if '/wua/custom/satincholete' in path \
                    and self._module == 'backend_theme_v10_mod_satincholete':
                path = os.path.dirname(path)
                varless_file = path + '/satincholete/'\
                    'backend_theme_v10_mod_satincholete/static/src/less/'\
                    'variables_mod.less'
                varless_file_new = path + '/satincholete/'\
                    'backend_theme_v10_mod_satincholete/static/src/less/'\
                    'variables_mod_new.less'
                backendcss_file = path + '/satincholete/'\
                    'backend_theme_v10_mod_satincholete/static/src/css/'\
                    'backend_mod.css'
                backendcss_file_new = path + '/satincholete/'\
                    'backend_theme_v10_mod_satincholete/static/src/css/'\
                    'backend_mod_new.css'
        if os.path.exists(varless_file):
            with open(varless_file) as fin, \
                    open(varless_file_new, 'w') as fout:
                for line in fin:
                    lineout = line
                    if line.startswith('@gray-base:'):
                        lineout = "@gray-base:             %s;\n" \
                            % self.sidebar_background_color
                    if line.startswith('@brand-primary:'):
                        lineout = "@brand-primary:         %s;\n" \
                            % self.backend_primary_color
                    if line.startswith('@brand-info:'):
                        lineout = "@brand-info:            %s;\n" \
                            % self.backend_primary_color
                    fout.write(lineout)
            fout.close()
            os.rename(varless_file_new, varless_file)
        elif not os.path.exists(varless_file):
            with open(varless_file, 'w') as fout:
                fout.write(
                    "@gray-base:             %s;\n"
                    "@brand-primary:         %s;\n"
                    "@brand-info:            %s;\n" %
                    (self.sidebar_background_color, self.backend_primary_color,
                     self.backend_primary_color))
        if os.path.exists(backendcss_file):
            with open(backendcss_file) as fin, \
                    open(backendcss_file_new, 'w') as fout:
                for line in fin:
                    lineout = line
                    if line.startswith('.bg-theme-report-color'):
                        lineout = \
                            ".bg-theme-report-color " \
                            "{ background-color: %s; }\n" % \
                            self.report_motive_color
                    if line.startswith('.theme-report-color'):
                        lineout = ".theme-report-color { color: %s; }" % \
                            self.report_motive_color
                    fout.write(lineout)
            fout.close()
            os.rename(backendcss_file_new, backendcss_file)
        elif not os.path.exists(backendcss_file):
            with open(backendcss_file, 'w') as fout:
                fout.write(".bg-theme-report-color { background-color: %s; }\n"
                           ".theme-report-color { color: %s; }" %
                           (self.report_motive_color,
                            self.report_motive_color))
        return values
