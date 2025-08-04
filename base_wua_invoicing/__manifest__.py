# 2025 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

{
    'name': 'Massive Invoicing for Water Users Associations',
    'summary': 'In a Water Users Association, management of billing based on invoice sets.',
    'version': '16.0.1.0.0',
    'category': 'Accounting/Accounting',
    'website': 'https://www.moval.es',
    'author': 'Moval Agroingeniería',
    'license': 'AGPL-3',
    'application': False,
    'installable': True,
    'post_init_hook': 'post_init_hook',
    'depends': [
        'base_ter_invoicing',
    ],
}
