# -*- coding: utf-8 -*-
# 2024 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api


class BaseConfigSettings(models.TransientModel):
    _inherit = "base.config.settings"

    # sidebar_irrigation_menu = fields.Boolean(
    #     string="Irrigation Management",
    #     default=True)

    field_credit_overdue = fields.Boolean(
        string="Credit overdue",
        default=True)

    field_website = fields.Boolean(
        string="Website",
        default=True)

    field_category_id = fields.Boolean(
        string="Category",
        default=True)

    field_updated_in_remotecontrol = fields.Boolean(
        string="Updated in remotecontrol",
        default=True)

    field_fax = fields.Boolean(
        string="Fax",
        default=True)

    field_email_score = fields.Boolean(
        string="Email Score",
        default=True)

    field_email_bounced = fields.Boolean(
        string="Email Bounded",
        default=True)

    field_gender = fields.Boolean(
        string="Gender",
        default=True)

    field_birthdate = fields.Boolean(
        string="Birthdate",
        default=True)

    field_name_alias = fields.Boolean(
        string="Name alias",
        default=True)

    field_title = fields.Boolean(
        string="Title",
        default=True)

    field_lang = fields.Boolean(
        string="Lang",
        default=True)

    button_comparative_presconsumption = fields.Boolean(
        string="Comparative presconsumptions",
        default=True)

    button_website_publish = fields.Boolean(
        string="Website publish",
        default=True)

    button_act_show_contract = fields.Boolean(
        string="Contract",
        default=True)

    button_aggregate_quotas = fields.Boolean(
        string="Aggregate quotas",
        default=True)

    button_tracking_emails = fields.Boolean(
        string="Tracking emails",
        default=True)

    actions_droplist = fields.Boolean(
        string="Actions droplist",
        default=True)

    print_droplist = fields.Boolean(
        string="Print droplist",
        default=True)

    attachments = fields.Boolean(
        string="Attachments",
        default=True)

    action_generate_partner_parcel_shp = fields.Boolean(
        string="Generate Parcel SHP",
        default=True)

    action_synchronize_partners = fields.Boolean(
        string="Synchronize partner with remote control",
        default=True)

    wua_partner_report = fields.Boolean(
        string="Partner report",
        default=True)

    wua_lessor_report = fields.Boolean(
        string="Lessor report",
        default=True)

    wua_owner_report = fields.Boolean(
        string="Owner report",
        default=True)

    wua_tenant_report = fields.Boolean(
        string="Tenant report",
        default=True)

    @api.multi
    def set_default_values(self):
        values = self.env['ir.values'].sudo()
        # values.set_default('base.config.settings', 'sidebar_irrigation_menu',
        #                    self.sidebar_irrigation_menu)
        values.set_default('base.config.settings', 'field_credit_overdue',
                           self.field_credit_overdue)
        values.set_default('base.config.settings', 'field_website',
                           self.field_website)
        values.set_default('base.config.settings', 'field_category_id',
                           self.field_category_id)
        values.set_default('base.config.settings',
                           'field_updated_in_remotecontrol',
                           self.field_updated_in_remotecontrol)
        values.set_default('base.config.settings', 'field_fax',
                           self.field_fax)
        values.set_default('base.config.settings', 'field_email_score',
                           self.field_email_score)
        values.set_default('base.config.settings', 'field_email_bounced',
                           self.field_email_bounced)
        values.set_default('base.config.settings', 'field_gender',
                           self.field_gender)
        values.set_default('base.config.settings', 'field_birthdate',
                           self.field_birthdate)
        values.set_default('base.config.settings', 'field_name_alias',
                           self.field_name_alias)
        values.set_default('base.config.settings', 'field_title',
                           self.field_title)
        values.set_default('base.config.settings', 'field_lang',
                           self.field_lang)
        values.set_default('base.config.settings',
                           'button_comparative_presconsumption',
                           self.button_comparative_presconsumption)
        values.set_default('base.config.settings', 'button_website_publish',
                           self.button_website_publish)
        values.set_default('base.config.settings', 'button_act_show_contract',
                           self.button_act_show_contract)
        values.set_default('base.config.settings', 'button_aggregate_quotas',
                           self.button_aggregate_quotas)
        values.set_default('base.config.settings', 'button_tracking_emails',
                           self.button_tracking_emails)
        values.set_default('base.config.settings', 'actions_droplist',
                           self.actions_droplist)
        values.set_default('base.config.settings', 'print_droplist',
                           self.print_droplist)
        values.set_default('base.config.settings', 'attachments',
                           self.attachments)
        values.set_default('base.config.settings',
                           'action_generate_partner_parcel_shp',
                           self.action_generate_partner_parcel_shp)
        values.set_default('base.config.settings',
                           'action_synchronize_partners',
                           self.action_synchronize_partners)
        values.set_default('base.config.settings', 'wua_partner_report',
                           self.wua_partner_report)
        values.set_default('base.config.settings', 'wua_lessor_report',
                           self.wua_lessor_report)
        values.set_default('base.config.settings', 'wua_owner_report',
                           self.wua_owner_report)
        values.set_default('base.config.settings', 'wua_tenant_report',
                           self.wua_tenant_report)
