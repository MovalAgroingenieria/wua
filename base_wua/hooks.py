# 2025 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo import api, SUPERUSER_ID, exceptions, _


def pre_init_hook(cr):
    env = api.Environment(cr, SUPERUSER_ID, {})
    incompatible_modules = ['base_foa', 'base_pdo', 'base_agf']
    installed_incompatible_modules = env['ir.module.module'].search([
        ('name', 'in', incompatible_modules),('state', '=', 'installed')])
    if len(installed_incompatible_modules) > 0:
        raise exceptions.ValidationError(_(
            'Cannot install, incompatible modules are installed: %s.') % (
            ', '.join(installed_incompatible_modules.mapped('name'))))


def post_init_hook(cr, registry):
    env = api.Environment(cr, SUPERUSER_ID, {})
    env.ref('base.module_base_wua')._update_translations(
        overwrite=True)


def uninstall_hook(cr, registry):
    env = api.Environment(cr, SUPERUSER_ID, {})
    try:
        env.cr.savepoint()
        env.cr.execute("""
            DELETE FROM ir_config_parameter
            WHERE key LIKE 'base_wua.%'""")
        env.cr.commit()
    except (Exception,):
        env.cr.rollback()