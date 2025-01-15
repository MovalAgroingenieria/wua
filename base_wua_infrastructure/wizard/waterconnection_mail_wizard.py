# -*- coding: utf-8 -*-
from openerp import api, fields, models


class WuaWaterconnectionMailWizard(models.TransientModel):
    _name = 'wua.waterconnection.mail.wizard'
    
    shared_title = fields.Char(
        string='Shared Title',
        help='The title that will be included in the email for all selected records.'
    )
    shared_text = fields.Text(
        string='Shared Text',
        help='Text that will be included in the email for all selected records.'
    )
    
    @api.multi
    def action_send_mails(self):
        """
        Envía el correo usando una plantilla, aplicando el shared_text a cada registro.
        """
        self.ensure_one()
        active_ids = self._context.get('active_ids', [])
        WaterConnection = self.env['wua.waterconnection']
        waterconnections = WaterConnection.browse(active_ids)
        
        # Referencia a la plantilla de correo (definida en XML)
        template = self.env.ref(
            'base_wua_infrastructure.email_template_waterconnection_notice', False)
        if not template:
            return True
        
        for wc in waterconnections:
            possible_partners = []
            for irrigationpoint in wc.irrigationpoint_ids:
                parcel = irrigationpoint.parcel_id
                for partnerlink in parcel.partnerlink_ids:
                    if partnerlink.water_costs_percentage > 0:
                        possible_partners.append(partnerlink.partner_id.id)
            if possible_partners:
                possible_partners = list(set(possible_partners))
                if len(possible_partners) == 1:
                    partner_to_sent_id = possible_partners[0]
            partner_rec = self.env['res.partner'].browse(partner_to_sent_id)
            partner_email = partner_rec.email
            # Agregamos el shared_text en el contexto para usarlo en la plantilla
            ctx = {
                'default_model': 'wua.waterconnection',
                'default_res_id': wc.id,
                'shared_title': self.shared_title,
                'shared_text': self.shared_text,
                'partner_to_sent': partner_rec,
                'partner_email': partner_email,
            }
            # Enviar el correo individual y obtener el ID de mail.mail generado
            template.with_context(ctx).send_mail(wc.id, force_send=True)

        
        return True
