from odoo import models, fields, _


class ResCompany(models.Model):
    _inherit = 'res.company'

    l10n_do_is_subject_to_proportionality = fields.Boolean(
        string='Is Subject to Proportionality',
        help='Check this box if the company is subject to proportionality '
    )
