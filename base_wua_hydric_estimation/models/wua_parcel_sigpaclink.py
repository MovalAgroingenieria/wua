# -*- coding: utf-8 -*-
# 2026 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, api, exceptions, _


class WuaParcelSigpaclink(models.Model):
    _inherit = 'wua.parcel.sigpaclink'

    @api.multi
    def action_create_cropunits_from_selected(self):
        if not self:
            raise exceptions.UserError(
                _('Please select at least one SIGPAC enclosure.'))
        active_season = self.env['wua.agriculturalseason'].search(
            [('active_agriculturalseason', '=', True)], limit=1)
        if not active_season:
            raise exceptions.UserError(
                _('No active agricultural season found.'))
        model_wua_cropunit = self.env['wua.cropunit']
        fallow_cultivation = self.env.ref('base_wua.cultivation_019')
        cropunits_geom = {}
        cropunit_ids = []
        created_count = 0
        skipped_count = 0
        for sigpac_link in self:
            parcel_id = sigpac_link.parcel_id.id
            all_sigpac_links = self.env['wua.parcel.sigpaclink'].search(
                [('parcel_id', '=', parcel_id)],
                order='id'
            )
            order_number = 0
            for idx, link in enumerate(all_sigpac_links, start=1):
                if link.id == sigpac_link.id:
                    order_number = idx
                    break
            if not order_number:
                skipped_count += 1
                continue
            existing_cropunit = model_wua_cropunit.search([
                ('parcel_id', '=', parcel_id),
                ('agriculturalseason_id', '=', active_season.id),
                ('order_number', '=', order_number)
            ], limit=1)
            if existing_cropunit:
                skipped_count += 1
                continue
            self.env.cr.execute(
                'SELECT geom FROM wua_parcel_sigpaclink WHERE id = %s',
                (sigpac_link.id,))
            geom_result = self.env.cr.fetchone()
            if not geom_result:
                skipped_count += 1
                continue
            geom = geom_result[0]
            new_cropunit = model_wua_cropunit.create({
                'agriculturalseason_id': active_season.id,
                'parcel_id': parcel_id,
                'cultivation_id': fallow_cultivation.id,
                'initial_date': active_season.initial_date,
                'end_date': active_season.end_date,
                'order_number': order_number,
                'aerial_image': None,
            })
            cropunits_geom[new_cropunit.name] = geom
            cropunit_ids.append(new_cropunit.id)
            created_count += 1
        for new_cropunit_code, geom in cropunits_geom.items():
            try:
                self.env.cr.execute(
                    'INSERT INTO wua_gis_cropunit (name, geom) '
                    'VALUES (%s, %s)', (new_cropunit_code, geom))
            except Exception:
                pass

        if cropunit_ids:
            model_wua_cropunit.browse(cropunit_ids)._compute_area_gis()

        message = _('Crop Units Creation Summary\n\n')
        message += _('Created: %d crop unit(s)\n') % created_count
        message += _('Skipped: %d enclosure(s)\n\n') % skipped_count

        if skipped_count > 0:
            message += _('Skipped enclosures already have crop units created '
                        'for the active agricultural season.\n\n'
                        'Each SIGPAC enclosure can only have one crop unit '
                        'per season.')

        if not cropunit_ids:
            raise exceptions.UserError(message)

        wizard = self.env['wizard.cropunit.creation.summary'].create({
            'message': message,
        })

        return {
            'type': 'ir.actions.act_window',
            'name': _('Crop Units Created'),
            'res_model': 'wizard.cropunit.creation.summary',
            'res_id': wizard.id,
            'view_mode': 'form',
            'view_type': 'form',
            'target': 'new',
        }
