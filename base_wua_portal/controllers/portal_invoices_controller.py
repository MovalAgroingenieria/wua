# -*- coding: utf-8 -*-
# 2025 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo import http
from odoo.exceptions import AccessError
from odoo.http import request
from odoo.fields import Date


class PortalInvoices(http.Controller):

    _items_per_page = 10

    def _prepare_portal_layout_values(self):
        """ prepare the values to render portal layout """
        partner = request.env.user.partner_id
        partner = partner.parent_id or partner
        gis_viewer_link = partner.gis_viewer_link
        if gis_viewer_link and '&arg=' in gis_viewer_link:
            gis_viewer_link = gis_viewer_link.split('&arg=')[0]
        liquidation_on_portal = request.env['ir.values'].sudo().get_default(
            'wua.invoicing.configuration',
            'liquidation_on_portal'
        )
        values = {
            'company': request.website.company_id,
            'gis_viewer_link': gis_viewer_link,
            'user': request.env.user,
            'partner': partner,
            'liquidation_on_portal': liquidation_on_portal
        }
        return values

    def _get_archive_groups(self, model, domain=None, fields=None,
                            groupby="create_date", order="create_date desc"):
        if not model:
            return []
        if domain is None:
            domain = []
        if fields is None:
            fields = ['name', 'create_date']
        groups = []
        for group in request.env[model].sudo()._read_group_raw(
                domain, fields=fields, groupby=groupby, orderby=order):
            dates, label = group[groupby]
            date_begin, date_end = dates.split('/')
            groups.append({
                'date_begin': Date.to_string(Date.from_string(date_begin)),
                'date_end': Date.to_string(Date.from_string(date_end)),
                'name': label,
                'item_count': group[groupby + '_count']
            })
        return groups

    @http.route(['/my/invoices', '/my/invoices/page/<int:page>'],
                type='http', auth="user", website=True)
    def portal_my_invoices(self, page=1, date_begin=None, date_end=None,
                           search=None, search_field=None, **kw):
        values = self._prepare_portal_layout_values()
        partner = request.env.user.partner_id
        partner = partner.parent_id or partner
        AccountInvoice = request.env['account.invoice'].sudo()

        domain = [
            ('type', 'in', ['out_invoice', 'out_refund']),
            ('message_partner_ids', 'child_of',
             [partner.commercial_partner_id.id]),
            ('state', 'in', ['open', 'paid', 'cancel'])
        ]

        if date_begin and date_end:
            domain += [('create_date', '>', date_begin),
                       ('create_date', '<=', date_end)]

        if search and search_field:
            field_map = {
                'name': 'number',
                'invoiceset': 'invoiceset_id.description',
                'date_invoice': 'date_invoice',
            }
            if search_field in field_map:
                domain.append((field_map[search_field], 'ilike', search))

        archive_groups = self._get_archive_groups('account.invoice', domain)

        invoice_count = AccountInvoice.search_count(domain)

        pager = request.website.pager(
            url="/my/invoices",
            url_args={'date_begin': date_begin, 'date_end': date_end,
                      'search': search, 'search_field': search_field},
            total=invoice_count,
            page=page,
            step=self._items_per_page
        )

        invoices = AccountInvoice.search(
            domain, limit=self._items_per_page, offset=pager['offset'])

        values.update({
            'date': date_begin,
            'invoices': invoices,
            'page_name': 'invoice',
            'pager': pager,
            'archive_groups': archive_groups,
            'default_url': '/my/invoices',
            'search': search,
            'search_field': search_field,
        })
        return request.render("website_portal_sale.portal_my_invoices", values)

    @http.route(['/my/invoices/pdf/<int:invoice_id>'], type='http',
                auth="user", website=True)
    def portal_get_invoice(self, invoice_id=None, **kw):
        invoice = request.env['account.invoice'].sudo().browse([invoice_id])
        try:
            invoice.check_access_rights('read')
            invoice.check_access_rule('read')
        except AccessError:
            return request.render("website.403")

        pdf = \
            request.env['report'].sudo().get_pdf(
                [invoice_id], 'account.report_invoice')
        invoice_name = \
            invoice.number.replace('/', '_') if invoice.number else 'Invoice'
        pdfhttpheaders = [
            ('Content-Type', 'application/pdf'), ('Content-Length', len(pdf)),
            ('Content-Disposition',
             'attachment; filename=%s.pdf;' % invoice_name)
        ]
        return request.make_response(pdf, headers=pdfhttpheaders)

    @http.route(['/my/invoices/pdf_multi'], type='http', auth="user", website=True, csrf=False)
    def portal_get_invoice(self, invoice_ids=None, **post):

        invoice_ids = request.httprequest.form.getlist('invoice_ids')
        if not invoice_ids:
            return request.redirect('/my/invoices')

        invoice_ids = [int(i) for i in invoice_ids]

        invoices = request.env['account.invoice'].sudo().browse(invoice_ids)

        try:
            invoices.check_access_rights('read')
            invoices.check_access_rule('read')
        except AccessError:
            return request.render("website.403")

        pdf = request.env['report'].sudo().get_pdf(
            invoice_ids,
            'account.report_invoice'
        )

        # filename logic
        if len(invoices) == 1 and invoices[0].number:
            filename = invoices[0].number.replace('/', '_') + '.pdf'
        else:
            filename = "Invoices.pdf"

        headers = [
            ('Content-Type', 'application/pdf'),
            ('Content-Length', len(pdf)),
            ('Content-Disposition', 'attachment; filename=%s;' % filename),
        ]

        return request.make_response(pdf, headers=headers)