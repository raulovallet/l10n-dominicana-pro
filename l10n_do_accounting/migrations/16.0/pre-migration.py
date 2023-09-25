from odoo import models, fields, api

def migrate(cr, version):

        cr.execute("""
            DELETE FROM ir_ui_view
            WHERE id IN (
                SELECT res_id
                FROM ir_model_data
                WHERE module = 'l10n_do_accounting'
            );
        """)


