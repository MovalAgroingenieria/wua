# 2025 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

{
    'name': 'Water Users Association Management',
    'summary': 'In a water users association, management of users and parcels',
    'version': '16.0.1.0.0',
    'category': 'Water Users Associations',
    'website': 'https://www.moval.es',
    'author': 'Moval Agroingeniería',
    'license': 'AGPL-3',
    'application': False,
    'installable': True,
    'pre_init_hook': 'pre_init_hook',
    'post_init_hook': 'post_init_hook',
    'uninstall_hook': 'uninstall_hook',
    'depends': [
        'base_ter',
    ],
    'data': [
        'security/ir.model.access.csv',
        'data/ter_profile_data.xml',
        'views/base_ter_menus.xml',
        'views/res_config_settings_views.xml',
        'views/res_partner_views.xml',
        'views/ter_parcel_views.xml',
        'views/wua_concession_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'base_wua/static/src/scss/base_wua.scss',
            ('remove', 'base_ter/static/lib/ter_iconset/iconset.css'),
            'base_wua/static/lib/ter_iconset/iconset.css',
            'base_wua/static/lib/wua_iconset/iconset.css',
        ],
        'web.assets_frontend': [
            ('remove', 'base_ter/static/lib/ter_iconset/iconset.css'),
            'base_wua/static/lib/ter_iconset/iconset.css',
            'base_wua/static/lib/wua_iconset/iconset.css',
        ],
        'web.report_assets_common': [
            ('remove', 'base_ter/static/lib/ter_iconset/iconset.css'),
            'base_wua/static/lib/ter_iconset/iconset.css',
            'base_wua/static/lib/wua_iconset/iconset.css',
        ],
    },
}
