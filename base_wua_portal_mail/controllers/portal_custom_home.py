# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import base64
from odoo import http
from odoo.http import request, Response
from odoo.addons.website_portal.controllers.main import website_account


class website_account(website_account):

    _items_per_page = 10

    @http.route()
    def account(self, **kw):
        """ Add mail documents to main account page """
        response = super(website_account, self).account(**kw)
        partner = request.env.user.partner_id

        mail = request.env['mail.mail']
        mail_count = mail.search_count(
            [('recipient_ids', 'in', [partner.id])])
        response.qcontext.update({
            'mail_count': mail_count,
        })
        return response

    def _prepare_portal_layout_values(self):
        """ prepare the values to render portal layout """
        partner = request.env.user.partner_id
        values = {
            'company': request.website.company_id,
            'user': request.env.user,
            'partner': partner
        }
        return values

    @http.route(['/my/mails', '/my/mails/page/<int:page>'],
                type='http', auth="user", website=True)
    def portal_my_mails(self, page=1, search=None,
                        search_field=None, selected_columns=None, **kw):
        values = self._prepare_portal_layout_values()
        partner = request.env.user.partner_id
        mails_model = request.env['mail.mail']
        domain = ['|', ('recipient_ids', 'in', [partner.id]),
                  ('email_to', 'ilike', partner.email)]
        if search and search_field:
            field_map = {
                'date': 'date',
                'subject': 'subject',
                'email_from': 'email_from',
            }
            if search_field in field_map:
                domain.append((field_map[search_field], 'ilike', search))
        mails = mails_model.sudo().search(domain)
        mails_count = len(mails)
        items_per_page = self._items_per_page
        pager = request.website.pager(
            url="/my/mails",
            total=mails_count,
            page=page,
            step=items_per_page,
            url_args={
                'search': search,
                'search_field': search_field,
            },
        )
        offset = (page - 1) * items_per_page
        paginated_mails = mails[offset:offset + items_per_page]
        values.update({
            'mails': paginated_mails,
            'pager': pager,
            'search_query': search,
            'search_field': search_field,
            'default_url': '/my/mails',
        })
        return request.render(
            "base_wua_portal_mail.portal_my_mails",
            values)

    @http.route(['/my/mails/<int:mail>'],
                type='http', auth="user", website=True)
    def mails_followup(self, mail=None, **kw):
        mail = request.env['mail.mail'].browse([mail])

        mail_sudo = mail.sudo()

        return request.render("base_wua_portal_mail.portal_mails_followup", {
            'mail': mail_sudo,
            'partner': request.env.user.partner_id,
            'attachments': mail_sudo.attachment_ids
        })

    @http.route(['/my/mails/<int:mail>/<int:attachment>/attachment'],
                type='http', auth="user", website=True)
    def download_mail_attachment(self, mail=None, attachment=None, **kw):
        mail = request.env['mail.mail'].browse(mail).sudo()

        if not attachment or not mail.attachment_ids:
            return request.not_found()

        attachment_record = \
            request.env['ir.attachment'].sudo().browse(attachment)

        if (not attachment_record or attachment_record.id
                not in mail.attachment_ids.ids):
            return request.not_found()

        if not attachment_record.datas:
            return request.not_found()

        try:
            content = base64.decodestring(
                attachment_record.datas.encode('utf-8'))
        except Exception:
            return request.not_found()

        headers = [
            ('Content-Type',
             attachment_record.mimetype or 'application/octet-stream'),
            ('Content-Disposition',
             'attachment; filename="{}"'.format(attachment_record.name)),
        ]

        return Response(content, headers=headers)
