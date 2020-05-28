# -*- coding: utf-8 -*-
# 2020 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, api, fields, _
from odoo.exceptions import ValidationError


class WuaInvoicesetLine(models.Model):
    _inherit = 'wua.invoiceset.line'

    def populate_items_select_irrigationreport(self, product_id):
        company = self.env.user.company_id
        current_intake_id = 0
        if not company.parent_id:
            super(WuaInvoicesetLine,
                  self).populate_items_select_irrigationreport(product_id)
        else:
            current_intake_id = self.env['wua.intake'].search([
                ('company_id', '=', company.id)]).id
        if current_intake_id:
            irrigationreports = self.env['wua.irrigationreport'].search(
                [('of_active_agriculturalseason', '=', True),
                 ('is_validated', '=', True),
                 ('invoiced', '=', False),
                 ('product_id.id', '=', product_id),
                 ('intake_id', '=', current_intake_id)])
            if irrigationreports:
                user_id = self.env.user.id
                invoicesetline_id = self.id
                try:
                    self.env.cr.savepoint()
                    self.env.cr.execute("""
                    INSERT INTO wua_invoiceset_line_irrigationreport
                    (id, create_uid,write_uid,create_date,write_date,
                    invoicesetline_id,irrigationreport_id,selected,
                    irrigationreport_number,report_initial_time,
                    report_end_time,intake_id,product_id,partner_id,
                    volume_real)
                    SELECT
                    nextval('wua_invoiceset_line_irrigationreport_id_seq'),
                    %s,%s,now(),now(),%s,i.id,TRUE,i.irrigationreport_number,
                    i.report_initial_time,i.report_end_time,i.intake_id,
                    i.product_id,i.partner_id,i.volume_real
                    FROM wua_irrigationreport i INNER JOIN
                    wua_agriculturalseason a ON i.agriculturalseason_id = a.id
                    WHERE i.is_validated AND a.active_agriculturalseason AND
                    i.invoiced=FALSE AND i.product_id=%s AND
                    i.intake_id=%s""", (
                        user_id, user_id, invoicesetline_id, product_id,
                        current_intake_id))
                    self.env.cr.commit()
                    self.env.invalidate_all()
                    self.configured_line = True
                except Exception:
                    self.env.cr.rollback()
                    raise ValidationError(_('Error when updating records.'))

    def populate_items_select_presconsumption(self, product_id):
        current_company_id = self.env.user.company_id.id
        company_g_id = self.env['ir.values'].get_default(
            'wua.configuration', 'company_01')
        company_r_id = self.env['ir.values'].get_default(
            'wua.configuration', 'company_02')
        company_t_id = self.env['ir.values'].get_default(
            'wua.configuration', 'company_03')
        if current_company_id == company_g_id:
            company = 'company_01'
        elif current_company_id == company_r_id:
            company = 'company_02'
        elif current_company_id == company_t_id:
            company = 'company_03'
        else:
            raise ValidationError(
                _('Company not found or is a parent company.'))

        presconsumptions = self.env['wua.presconsumption'].search([
            ('product_id', '=', product_id),
            ('invoiceset_id', '=', False)])
        if len(presconsumptions) > 0:
            user_id = self.env.user.id
            invoicesetline_id = self.id
            try:
                self.env.cr.savepoint()
                if company == 'company_01':
                    self.env.cr.execute("""
                        INSERT INTO wua_invoiceset_line_presconsumption (id,
                        create_uid, write_uid, create_date, write_date,
                        invoicesetline_id, selected, presconsumption_id,
                        reading_id, reading_initial_time, initial_volume,
                        reading_end_time, end_volume, volume, watermeter_id,
                        waterconnection_id, irrigationshed_id,
                        hydraulicsector_id, adjustement_volume, volume_real,
                        area_total_company_g, area_total_company_r,
                        area_total_company_t)
                        SELECT
                        nextval('wua_invoiceset_line_presconsumption_id_seq'),
                        %s, %s, now(), now(), %s, TRUE, pc.id, reading_id,
                        reading_initial_time, initial_volume, reading_end_time,
                        end_volume, volume, pc.watermeter_id,
                        pc.waterconnection_id,
                        pc.irrigationshed_id, pc.hydraulicsector_id,
                        adjustement_volume, volume_real,
                        wc.area_total_company_g, wc.area_total_company_r,
                        area_total_company_t
                        FROM wua_presconsumption as pc
                        INNER JOIN wua_waterconnection as wc
                        ON pc.waterconnection_id = wc.id
                        WHERE pc.product_id=%s AND
                        invoiceset_id is null AND validated AND
                        wc.area_total_company_g > 0""", (user_id, user_id,
                                                         invoicesetline_id,
                                                         product_id))
                elif company == 'company_02':
                    self.env.cr.execute("""
                        INSERT INTO wua_invoiceset_line_presconsumption (id,
                        create_uid, write_uid, create_date, write_date,
                        invoicesetline_id, selected, presconsumption_id,
                        reading_id, reading_initial_time, initial_volume,
                        reading_end_time, end_volume, volume, watermeter_id,
                        waterconnection_id, irrigationshed_id,
                        hydraulicsector_id, adjustement_volume, volume_real,
                        area_total_company_g, area_total_company_r,
                        area_total_company_t)
                        SELECT
                        nextval('wua_invoiceset_line_presconsumption_id_seq'),
                        %s, %s, now(), now(), %s, TRUE, pc.id, reading_id,
                        reading_initial_time, initial_volume, reading_end_time,
                        end_volume, volume, pc.watermeter_id,
                        pc.waterconnection_id,
                        pc.irrigationshed_id, pc.hydraulicsector_id,
                        adjustement_volume, volume_real,
                        wc.area_total_company_g, wc.area_total_company_r,
                        area_total_company_t
                        FROM wua_presconsumption as pc
                        INNER JOIN wua_waterconnection as wc
                        ON pc.waterconnection_id = wc.id
                        WHERE pc.product_id=%s AND
                        invoiceset_id is null AND validated AND
                        wc.area_total_company_r > 0""", (user_id, user_id,
                                                         invoicesetline_id,
                                                         product_id))
                elif company == 'company_03':
                    self.env.cr.execute("""
                        INSERT INTO wua_invoiceset_line_presconsumption (id,
                        create_uid, write_uid, create_date, write_date,
                        invoicesetline_id, selected, presconsumption_id,
                        reading_id, reading_initial_time, initial_volume,
                        reading_end_time, end_volume, volume, watermeter_id,
                        waterconnection_id, irrigationshed_id,
                        hydraulicsector_id, adjustement_volume, volume_real,
                        area_total_company_g, area_total_company_r,
                        area_total_company_t)
                        SELECT
                        nextval('wua_invoiceset_line_presconsumption_id_seq'),
                        %s, %s, now(), now(), %s, TRUE, pc.id, reading_id,
                        reading_initial_time, initial_volume, reading_end_time,
                        end_volume, volume, pc.watermeter_id,
                        pc.waterconnection_id,
                        pc.irrigationshed_id, pc.hydraulicsector_id,
                        adjustement_volume, volume_real,
                        wc.area_total_company_g, wc.area_total_company_r,
                        area_total_company_t
                        FROM wua_presconsumption as pc
                        INNER JOIN wua_waterconnection as wc
                        ON pc.waterconnection_id = wc.id
                        WHERE pc.product_id=%s AND
                        invoiceset_id is null AND validated AND
                        wc.area_total_company_t > 0""", (user_id, user_id,
                                                         invoicesetline_id,
                                                         product_id))
                self.env.cr.execute("""
                    UPDATE wua_presconsumption
                    SET invoiceset_id=""" + str(self.invoiceset_id.id) + """,
                    invoiced_consumption=TRUE
                    WHERE product_id=""" + str(product_id) + """ and
                    invoiceset_id is null""")
                self.env.cr.commit()
                self.env.invalidate_all()
                self.configured_line = True
            except Exception:
                self.env.cr.rollback()
                raise ValidationError(_('Error when updating records.'))


class WuaInvoiceset(models.Model):
    _inherit = 'wua.invoiceset'

    def after_calculate_invoiceset(self, invoiceset):
        super(WuaInvoiceset, self).after_calculate_invoiceset(invoiceset)
        for line in invoiceset.line_ids:
            if line.categ_id.productcategory_code == 7:
                selected_presconsumptions = \
                    line.line_presconsumption_ids.filtered(
                        lambda x: x.selected is True)
                for presconsumption in selected_presconsumptions:
                    pc = self.env['wua.presconsumption'].browse(
                        presconsumption.presconsumption_id.id)
                    vals = {'company_id': self.env.user.company_id.id,
                            'invoiceset_id': invoiceset.id, }
                    pc.write(vals)

    @api.multi
    def unlink(self):
        presconsumptions_ids = []
        for record in self:
            presconsumptions = self.env['wua.presconsumption'].search(
                [('invoiceset_id', '=', record.id)])
            for presconsumption in presconsumptions:
                presconsumptions_ids.append(presconsumption.id)
        res = super(WuaInvoiceset, self).unlink()
        if presconsumptions_ids:
            presconsumptions = self.env['wua.presconsumption'].browse(
                presconsumptions_ids)
            vals = {'invoiceset_id': None,
                    'company_id': None, }
            presconsumptions.write(vals)
        return res

    def after_cancel_invoiceset(self, invoiceset):
        super(WuaInvoiceset, self).after_cancel_invoiceset(invoiceset)
        for line in invoiceset.line_ids:
            if line.categ_id.productcategory_code == 7:
                presconsumptions_ids = []
                for line_presconsumption in line.line_presconsumption_ids:
                    presconsumptions_ids.append(
                        line_presconsumption.presconsumption_id.id)
                if presconsumptions_ids:
                    presconsumptions = self.env['wua.presconsumption'].browse(
                        presconsumptions_ids)
                    vals = {'invoiceset_id': None,
                            'company_id': None, }
                    presconsumptions.write(vals)
                line.line_presconsumption_ids.unlink()


class WuaInvoicesetLinePresconsumption(models.Model):
    _inherit = 'wua.invoiceset.line.presconsumption'

    area_total_company_g = fields.Float(
        string='Area of Grupo (ha)')

    area_total_company_r = fields.Float(
        string='Area of Resurrección (ha)')

    area_total_company_t = fields.Float(
        string='Area of Trasvase (ha)')
