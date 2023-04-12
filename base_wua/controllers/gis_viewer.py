import werkzeug
import urlparse
from odoo import http
from odoo.http import request


class GisViewerController(http.Controller):

    # Helper method in case website module is not installed
    def url_for(self, path_or_uri, lang=None):
        if isinstance(path_or_uri, unicode):
            path_or_uri = path_or_uri.encode('utf-8')
        current_path = request.httprequest.path
        if isinstance(current_path, unicode):
            current_path = current_path.encode('utf-8')
        location = path_or_uri.strip()
        url = urlparse.urlparse(location)
        if request and not url.netloc and not url.scheme and url.path:
            location = urlparse.urljoin(current_path, location)
        return location.decode('utf-8')

    @http.route('/gisviewer', type='http', auth='user', methods=['GET'],
                csrf=False, website=True)
    def open_gis_viewer(self, **kwargs):
        current_user = request.env.user
        if current_user:
            model_wua_parcel = request.env['wua.parcel']
            # Artifact to get URL
            viewer_data = model_wua_parcel.run_gisviewer_url() or {}
            url_to_redirect = viewer_data.get('url', False)
            if (url_to_redirect):
                # If website not installed, redirect methdo will not exists
                # Create the function
                request.redirect = lambda url, code=302: \
                    werkzeug.utils.redirect(self.url_for(url), code)
                result = request.redirect(url_to_redirect, 302)
                return result
