# -*- coding: utf-8 -*-
# 2020 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, SUPERUSER_ID


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})

    env.cr.execute('''
         ALTER TABLE wua_infrastructure_configuration DROP CONSTRAINT
         wua_infrastructure_configuration_valid_max_levels_pressurized_i;''')

    for i in range(6, 40):
        query = '''
            ALTER TABLE wua_parcel
              ADD COLUMN IF NOT EXISTS waterpipe_0%s_id INT;
            ALTER TABLE wua_parcel
              DROP CONSTRAINT IF EXISTS "wua_parcel_waterpipe_0%s_id_fkey";
            ALTER TABLE wua_parcel
              ADD CONSTRAINT "wua_parcel_waterpipe_0%s_id_fkey"
              FOREIGN KEY (waterpipe_0%s_id) REFERENCES wua_waterpipe(id)
              ON DELETE SET NULL;
            CREATE INDEX IF NOT EXISTS "wua_parcel_waterpipe_0%s_id_index"
              ON wua_parcel USING btree(waterpipe_0%s_id);
                ''' % (i, i, i, i, i, i)
        env.cr.execute(query)

    env.cr.execute('''
        ALTER TABLE wua_parcel ADD COLUMN IF NOT EXISTS waterpipe_%s_id INT;
        ALTER TABLE wua_parcel
          DROP CONSTRAINT IF EXISTS "wua_parcel_waterpipe_%s_id_fkey";
        ALTER TABLE wua_parcel ADD CONSTRAINT "wua_parcel_waterpipe_%s_id_fkey"
            FOREIGN KEY (waterpipe_%s_id) REFERENCES wua_waterpipe(id)
            ON DELETE SET NULL;
        CREATE INDEX IF NOT EXISTS "wua_parcel_waterpipe_%s_id_index"
          ON wua_parcel USING btree(waterpipe_%s_id);
            ''' % ('40', '40', '40', '40', '40', '40'))
