
from odoo import http
from odoo.http import request


class GisViewerController(http.Controller):

    @http.route('/gisviewer', type='http', auth='user', methods=['GET'],
                csrf=False, website=True)
    def open_gis_viewer(self, **kwargs):
        current_user = request.env.user
        if current_user:
            model_wua_parcel = request.env['wua.parcel']
            # Artifact to get URL
            viewer_data = model_wua_parcel.run_gisviewer_url()
            return request.redirect(viewer_data.get('url'))
