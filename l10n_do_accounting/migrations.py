from odoo import models, fields, api

def migrate(cr, versión):
    # Verificamos que la versión actual sea inferior a la versión especificada
    if versión < "1.0":
        # Agregamos la nueva columna
        cr.execute("""
            CREATE TABLE my_module_table (
                ...
                new_column_name VARCHAR(255) NOT NULL,
            )
        """)

        # Actualizamos la versión del módulo
        cr.execute("UPDATE my_module SET version='1.0'")


# Registramos el script de migración
models.get_model("ir.module.module").update_handler(
    "l10n_do_accounting",
    "16.0",
    migrate,
)