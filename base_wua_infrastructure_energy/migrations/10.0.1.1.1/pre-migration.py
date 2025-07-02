# -*- coding: utf-8 -*-
# 2025 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, SUPERUSER_ID


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})

    cr.execute(
        'ALTER TABLE IF EXISTS "wua_gis_power_line" '
        'RENAME TO "wua_gis_powerline";'
    )
    cr.execute(
        'ALTER TABLE IF EXISTS "wua_gis_power_line_support" '
        'RENAME TO "wua_gis_powerlinesupport";'
    )
    cr.execute(
        'ALTER TABLE IF EXISTS "wua_gis_processing_centre" '
        'RENAME TO "wua_gis_processingcentre";'
    )

    cr.execute(
        'ALTER SEQUENCE IF EXISTS "wua_gis_power_line_gid_seq" '
        'RENAME TO "wua_gis_powerline_gid_seq";'
    )
    cr.execute(
        'ALTER SEQUENCE IF EXISTS "wua_gis_power_line_support_gid_seq" '
        'RENAME TO "wua_gis_powerlinesupport_gid_seq";'
    )
    cr.execute(
        'ALTER SEQUENCE IF EXISTS "wua_gis_processing_centre_gid_seq" '
        'RENAME TO "wua_gis_processingcentre_gid_seq";'
    )
    env.cr.commit()

    cr.execute(
        'ALTER INDEX IF EXISTS "wua_gis_power_line_idx" '
        'RENAME TO "wua_gis_powerline_idx";'
    )
    cr.execute(
        'ALTER INDEX IF EXISTS "wua_gis_power_line_support_idx" '
        'RENAME TO "wua_gis_powerlinesupport_idx";'
    )
    cr.execute(
        'ALTER INDEX IF EXISTS "wua_gis_processing_centre_idx" '
        'RENAME TO "wua_gis_processingcentre_idx";'
    )
    env.cr.commit()

    try:
        cr.execute(
            'ALTER TABLE wua_gis_powerline '
            'RENAME CONSTRAINT wua_gis_power_line_pkey '
            'TO wua_gis_powerline_pkey;'
        )
    except Exception:
        pass
    try:
        cr.execute(
            'ALTER TABLE wua_gis_powerline '
            'RENAME CONSTRAINT wua_gis_power_line_name_key '
            'TO wua_gis_powerline_name_key;'
        )
    except Exception:
        pass
    try:
        cr.execute(
            'ALTER TABLE wua_gis_powerlinesupport '
            'RENAME CONSTRAINT wua_gis_power_line_support_pkey '
            'TO wua_gis_powerlinesupport_pkey;'
        )
    except Exception:
        pass
    try:
        cr.execute(
            'ALTER TABLE wua_gis_powerlinesupport '
            'RENAME CONSTRAINT wua_gis_power_line_support_name_key '
            'TO wua_gis_powerlinesupport_name_key;'
        )
    except Exception:
        pass
    try:
        cr.execute(
            'ALTER TABLE wua_gis_processingcentre '
            'RENAME CONSTRAINT wua_gis_processing_centre_pkey '
            'TO wua_gis_processingcentre_pkey;'
        )
    except Exception:
        pass
    try:
        cr.execute(
            'ALTER TABLE wua_gis_processingcentre '
            'RENAME CONSTRAINT wua_gis_processing_centre_name_key '
            'TO wua_gis_processingcentre_name_key;'
        )
    except Exception:
        pass
    env.cr.commit()

    cr.execute("""
        CREATE OR REPLACE FUNCTION wua_gis_powerline_update_on_wua_powerline()
        RETURNS trigger AS
        $$
        BEGIN
            IF TG_OP = 'UPDATE' OR TG_OP = 'DELETE' THEN
                UPDATE public.wua_powerline
                SET with_gis_powerline = False
                WHERE name = OLD.name;
            END IF;
            IF TG_OP = 'UPDATE' OR TG_OP = 'INSERT' THEN
                UPDATE public.wua_powerline
                SET with_gis_powerline = True
                WHERE name = NEW.name;
            END IF;
            RETURN NULL;
        END;
        $$ LANGUAGE plpgsql SECURITY DEFINER;
    """)
    env.cr.commit()

    cr.execute("""
        CREATE OR REPLACE FUNCTION
        wua_gis_powerlinesupport_update_on_wua_powerlinesupport()
        RETURNS trigger AS
        $$
        BEGIN
            IF TG_OP = 'UPDATE' OR TG_OP = 'DELETE' THEN
                UPDATE public.wua_powerlinesupport
                SET with_gis_powerlinesupport = False
                WHERE name = OLD.name;
            END IF;
            IF TG_OP = 'UPDATE' OR TG_OP = 'INSERT' THEN
                UPDATE public.wua_powerlinesupport
                SET with_gis_powerlinesupport = True
                WHERE name = NEW.name;
            END IF;
            RETURN NULL;
        END;
        $$ LANGUAGE plpgsql SECURITY DEFINER;
    """)
    env.cr.commit()

    cr.execute("""
        CREATE OR REPLACE FUNCTION
        wua_gis_processingcentre_update_on_wua_processingcentre()
        RETURNS trigger AS
        $$
        BEGIN
            IF TG_OP = 'UPDATE' OR TG_OP = 'DELETE' THEN
                UPDATE public.wua_processingcentre
                SET with_gis_processingcentre = False
                WHERE name = OLD.name;
            END IF;
            IF TG_OP = 'UPDATE' OR TG_OP = 'INSERT' THEN
                UPDATE public.wua_processingcentre
                SET with_gis_processingcentre = True
                WHERE name = NEW.name;
            END IF;
            RETURN NULL;
        END;
        $$ LANGUAGE plpgsql SECURITY DEFINER;
    """)
    env.cr.commit()

    cr.execute("""
        DROP TRIGGER IF EXISTS wua_gis_powerline_write_trigger
        ON public.wua_gis_powerline;
        DROP TRIGGER IF EXISTS wua_gis_powerline_create_unlink_trigger
        ON public.wua_gis_powerline;
        DROP TRIGGER IF EXISTS wua_gis_power_line_write_trigger
        ON public.wua_gis_powerline;
        DROP TRIGGER IF EXISTS wua_gis_power_line_create_unlink_trigger
        ON public.wua_gis_powerline;
        CREATE TRIGGER wua_gis_powerline_write_trigger
        AFTER UPDATE OF name ON public.wua_gis_powerline
        FOR EACH ROW
        WHEN (OLD.name IS DISTINCT FROM NEW.name)
        EXECUTE PROCEDURE wua_gis_powerline_update_on_wua_powerline();
        CREATE TRIGGER wua_gis_powerline_create_unlink_trigger
        AFTER INSERT OR DELETE ON public.wua_gis_powerline
        FOR EACH ROW
        EXECUTE PROCEDURE wua_gis_powerline_update_on_wua_powerline();
    """)
    env.cr.commit()

    cr.execute("""
        DROP TRIGGER IF EXISTS wua_gis_powerlinesupport_write_trigger
        ON public.wua_gis_powerlinesupport;
        DROP TRIGGER IF EXISTS wua_gis_powerlinesupport_create_unlink_trigger
        ON public.wua_gis_powerlinesupport;
        DROP TRIGGER IF EXISTS wua_gis_power_line_support_write_trigger
        ON public.wua_gis_powerlinesupport;
        DROP TRIGGER IF EXISTS wua_gis_power_line_support_create_unlink_trigger
        ON public.wua_gis_powerlinesupport;
        CREATE TRIGGER wua_gis_powerlinesupport_write_trigger
        AFTER UPDATE OF name ON public.wua_gis_powerlinesupport
        FOR EACH ROW
        WHEN (OLD.name IS DISTINCT FROM NEW.name)
        EXECUTE PROCEDURE
        wua_gis_powerlinesupport_update_on_wua_powerlinesupport();
        CREATE TRIGGER wua_gis_powerlinesupport_create_unlink_trigger
        AFTER INSERT OR DELETE ON public.wua_gis_powerlinesupport
        FOR EACH ROW
        EXECUTE PROCEDURE
        wua_gis_powerlinesupport_update_on_wua_powerlinesupport();
    """)
    env.cr.commit()

    cr.execute("""
        DROP TRIGGER IF EXISTS wua_gis_processingcentre_write_trigger
        ON public.wua_gis_processingcentre;
        DROP TRIGGER IF EXISTS wua_gis_processingcentre_create_unlink_trigger
        ON public.wua_gis_processingcentre;
        DROP TRIGGER IF EXISTS wua_gis_processing_centre_write_trigger
        ON public.wua_gis_processingcentre;
        DROP TRIGGER IF EXISTS wua_gis_processing_centre_create_unlink_trigger
        ON public.wua_gis_processingcentre;
        CREATE TRIGGER wua_gis_processingcentre_write_trigger
        AFTER UPDATE OF name ON public.wua_gis_processingcentre
        FOR EACH ROW
        WHEN (OLD.name IS DISTINCT FROM NEW.name)
        EXECUTE PROCEDURE
        wua_gis_processingcentre_update_on_wua_processingcentre();
        CREATE TRIGGER wua_gis_processingcentre_create_unlink_trigger
        AFTER INSERT OR DELETE ON public.wua_gis_processingcentre
        FOR EACH ROW
        EXECUTE PROCEDURE
        wua_gis_processingcentre_update_on_wua_processingcentre();
    """)
    env.cr.commit()
