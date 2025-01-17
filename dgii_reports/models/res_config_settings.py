from odoo import models, fields, _


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    l10n_do_is_subject_to_proportionality = fields.Boolean(
        related='company_id.l10n_do_is_subject_to_proportionality',
        string='Subject to Proportionality',
        help='Check this box if the company is subject to proportionality',
        readonly=False,
    )