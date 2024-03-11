# -*- coding: utf-8 -*-
# 2024 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from lxml import etree
from odoo import models, api


class ResPartner(models.Model):
    _inherit = 'res.partner'

    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False,
                        submenu=False):
        res = super(ResPartner, self).fields_view_get(
            view_id=view_id, view_type=view_type, toolbar=toolbar,
            submenu=submenu)

        # Check if portal user
        is_portal_user = self.env.user.has_group('base.group_portal')
        if not is_portal_user:
            return res

        # Get config params
        # Sidebar (TODO)
        # show_sidebar_irrigation_menu = self.env['ir.values'].get_default(
        #     'base.config.settings', 'sidebar_irrigation_menu')
        # Fields
        show_field_credit_overdue = self.env['ir.values'].get_default(
            'base.config.settings', 'field_credit_overdue')
        show_field_website = self.env['ir.values'].get_default(
            'base.config.settings', 'field_website')
        show_field_category_id = self.env['ir.values'].get_default(
            'base.config.settings', 'field_category_id')
        show_field_updated_in_remotecontrol = \
            self.env['ir.values'].get_default(
                'base.config.settings', 'field_updated_in_remotecontrol')
        show_field_fax = self.env['ir.values'].get_default(
            'base.config.settings', 'field_fax')
        show_field_email_score = self.env['ir.values'].get_default(
            'base.config.settings', 'field_email_score')
        show_field_email_bounced = self.env['ir.values'].get_default(
            'base.config.settings', 'field_email_bounced')
        show_field_gender = self.env['ir.values'].get_default(
            'base.config.settings', 'field_gender')
        show_field_birthdate = self.env['ir.values'].get_default(
            'base.config.settings', 'field_birthdate')
        show_field_name_alias = self.env['ir.values'].get_default(
            'base.config.settings', 'field_name_alias')
        show_field_title = self.env['ir.values'].get_default(
            'base.config.settings', 'field_title')
        show_field_lang = self.env['ir.values'].get_default(
            'base.config.settings', 'field_lang')
        # Buttons
        show_button_comparative_presconsumption = \
            self.env['ir.values'].get_default(
                'base.config.settings',
                'button_comparative_presconsumption')
        show_button_website_publish = self.env['ir.values'].get_default(
            'base.config.settings', 'button_website_publish')
        show_button_act_show_contract = self.env['ir.values'].get_default(
            'base.config.settings', 'button_act_show_contract')
        show_button_aggregate_quotas = self.env['ir.values'].get_default(
            'base.config.settings', 'button_aggregate_quotas')
        show_button_tracking_emails = self.env['ir.values'].get_default(
            'base.config.settings', 'button_tracking_emails')
        show_button_gravity_consumptions = self.env['ir.values'].get_default(
            'base.config.settings', 'button_gravity_consumptions')
        show_button_hydric_movements = self.env['ir.values'].get_default(
            'base.config.settings', 'button_hydric_movements')
        show_button_watering_requests = self.env['ir.values'].get_default(
            'base.config.settings', 'button_watering_requests')
        # Toolbar actions and print (attachments is done by javascript)
        show_actions_droplist = self.env['ir.values'].get_default(
            'base.config.settings', 'actions_droplist')
        show_print_droplist = self.env['ir.values'].get_default(
            'base.config.settings', 'print_droplist')
        actions_to_remove = []
        show_action_generate_partner_parcel_shp = \
            self.env['ir.values'].get_default(
                'base.config.settings', 'action_generate_partner_parcel_shp')
        if not show_action_generate_partner_parcel_shp:
            actions_to_remove.append(
                'base_wua.wua_generate_partner_parcel_shp')
        show_action_synchronize_partners = self.env['ir.values'].get_default(
            'base.config.settings', 'action_synchronize_partners')
        if not show_action_synchronize_partners:
            actions_to_remove.append(
                'base_wua_remotecontrol_rest.wua_action_synchronize_partners')
        # Printed docs
        docs_to_remove = []
        show_wua_partner_report = \
            self.env['ir.values'].get_default(
                'base.config.settings', 'wua_partner_report')
        if not show_wua_partner_report:
            docs_to_remove.append('base_wua.wua_partner_report')
        show_wua_lessor_report = \
            self.env['ir.values'].get_default(
                'base.config.settings', 'wua_lessor_report')
        if not show_wua_lessor_report:
            docs_to_remove.append('base_wua.wua_lessor_report')
        show_wua_owner_report = \
            self.env['ir.values'].get_default(
                'base.config.settings', 'wua_owner_report')
        if not show_wua_owner_report:
            docs_to_remove.append('base_wua.wua_owner_report')
        show_wua_tenant_report = \
            self.env['ir.values'].get_default(
                'base.config.settings', 'wua_tenant_report')
        if not show_wua_tenant_report:
            docs_to_remove.append('base_wua.wua_tenant_report')
        show_wua_quota_report = \
            self.env['ir.values'].get_default(
                'base.config.settings', 'wua_quota_report')
        if not show_wua_quota_report:
            docs_to_remove.append(
                'base_wua_quota_management.wua_partner_quota_report')

        if view_type == 'form':
            doc = etree.XML(res['arch'])
            # Fields
            if not show_field_credit_overdue:
                for node in doc.xpath("//field[@name='credit_overdue']"):
                    node.set('modifiers', '{"invisible": true}')
            if not show_field_website:
                for node in doc.xpath("//field[@name='website']"):
                    node.set('modifiers', '{"invisible": true}')
            if not show_field_category_id:
                for node in doc.xpath("//field[@name='category_id']"):
                    node.set('modifiers', '{"invisible": true}')
            if not show_field_updated_in_remotecontrol:
                for node in doc.xpath(
                        "//field[@name='updated_in_remotecontrol']"):
                    node.set('modifiers', '{"invisible": true}')
            if not show_field_fax:
                for node in doc.xpath("//field[@name='fax']"):
                    node.set('modifiers', '{"invisible": true}')
            if not show_field_email_score:
                for node in doc.xpath("//field[@name='email_score']"):
                    node.set('modifiers', '{"invisible": true}')
            if not show_field_email_bounced:
                for node in doc.xpath("//field[@name='email_bounced']"):
                    node.set('modifiers', '{"invisible": true}')
            if not show_field_gender:
                for node in doc.xpath("//field[@name='gender']"):
                    node.set('modifiers', '{"invisible": true}')
            if not show_field_birthdate:
                for node in doc.xpath("//field[@name='birthdate']"):
                    node.set('modifiers', '{"invisible": true}')
            if not show_field_name_alias:
                for node in doc.xpath("//field[@name='name_alias']"):
                    node.set('modifiers', '{"invisible": true}')
            if not show_field_title:
                for node in doc.xpath("//field[@name='title']"):
                    node.set('modifiers', '{"invisible": true}')
            if not show_field_lang:
                for node in doc.xpath("//field[@name='lang']"):
                    node.set('modifiers', '{"invisible": true}')
            # Buttons
            if not show_button_comparative_presconsumption:
                button_action_id = self.env.ref(
                    'base_wua_pressurized_irrigation_monitoring.'
                    'res_partner_comparative_presconsumption_action').id
                for node in doc.xpath(
                        "//button[@name='%s']" % button_action_id):
                    node.set('modifiers', '{"invisible": true}')
            if not show_button_website_publish:
                for node in doc.xpath(
                        "//button[@name='website_publish_button']"):
                    node.set('modifiers', '{"invisible": true}')
            if not show_button_act_show_contract:
                for node in doc.xpath("//button[@name='act_show_contract']"):
                    node.set('modifiers', '{"invisible": true}')
            if not show_button_aggregate_quotas:
                for node in doc.xpath(
                        "//button[@name='action_get_partner_"
                        "aggregate_quotas']"):
                    node.set('modifiers', '{"invisible": true}')
            if not show_button_tracking_emails:
                button_action_id = self.env.ref(
                    'mail_tracking.action_view_mail_tracking_email').id
                for node in doc.xpath(
                        "//button[@name='%s']" % button_action_id):
                    node.set('modifiers', '{"invisible": true}')
            if not show_button_gravity_consumptions:
                for node in doc.xpath(
                        "//button[@name='action_see_gravity_consumptions']"):
                    node.set('modifiers', '{"invisible": true}')
            if not show_button_hydric_movements:
                for node in doc.xpath(
                        "//button[@name='action_get_hydric_movements']"):
                    node.set('modifiers', '{"invisible": true}')
            if not show_button_watering_requests:
                for node in doc.xpath(
                        "//button[@name='action_see_watering_requests']"):
                    node.set('modifiers', '{"invisible": true}')
            # Actions
            if not show_actions_droplist:
                res['toolbar']['action'] = []
            if show_actions_droplist and len(actions_to_remove) > 0:
                actions_menu = res.get('toolbar', {}).get('action', [])
                actions_to_show = []
                for action_menu in actions_menu:
                    if action_menu['xml_id'] not in actions_to_remove:
                        actions_to_show.append(action_menu)
                res['toolbar']['action'] = actions_to_show
            # Print
            if not show_print_droplist:
                res['toolbar']['print'] = []
            if show_print_droplist and len(docs_to_remove) > 0:
                print_menu = res.get('toolbar', {}).get('print', [])
                docs_to_show = []
                for print_doc in print_menu:
                    if print_doc['xml_id'] not in docs_to_remove:
                        docs_to_show.append(print_doc)
                res['toolbar']['print'] = docs_to_show

            res['arch'] = etree.tostring(doc)

        if view_type == 'tree':
            doc = etree.XML(res['arch'])
            # Actions
            if not show_actions_droplist:
                res['toolbar']['action'] = []
            # Print
            if not show_print_droplist:
                res['toolbar']['print'] = []

            res['arch'] = etree.tostring(doc)

        # if view_type == 'search':
        #     doc = etree.XML(res['arch'])
        #     res['arch'] = etree.tostring(doc)
        return res
