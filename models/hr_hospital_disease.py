from odoo import api, fields, models
from odoo.exceptions import ValidationError


class HospitalDisease(models.Model):
    """Model for Hospital Diseases."""

    _name = 'hr.hospital.disease'
    _description = 'Disease Type'
    _parent_name = 'parent_id'
    _parent_store = True
    _rec_name = 'display_name'
    _order = 'parent_path'

    name = fields.Char(string='Disease Name', required=True)
    description = fields.Text(string='Description')
    parent_path = fields.Char(index=True)

    is_group = fields.Boolean(
        string='Is Group',
        default=False,
        help='If set, this record will be considered a category for other diseases',
    )

    parent_id = fields.Many2one(
        comodel_name='hr.hospital.disease',
        string='Parent Disease',
        ondelete='cascade',
        domain=[('is_group', '=', True)],
        index=True,
    )

    child_ids = fields.One2many(
        comodel_name='hr.hospital.disease',
        inverse_name='parent_id',
        string='Child Diseases',
    )

    display_name = fields.Char(
        compute='_compute_display_name',
        recursive=True,
        store=True,
    )

    code = fields.Char(string='ICD Code')
    color = fields.Integer(
        string='Color Index',
        default=1,
    )

    @api.constrains('parent_id')
    def _check_disease_recursion(self):
        """Prevent recursive disease hierarchies."""
        if not self._check_recursion():
            raise ValidationError('Error! You cannot create recursive hierarchies.')

    @api.depends('name', 'parent_id.display_name')
    def _compute_display_name(self):
        """Build a hierarchical display name for the disease tree."""
        for rec in self:
            if rec.parent_id:
                rec.display_name = f'{rec.parent_id.display_name} / {rec.name}'
            else:
                rec.display_name = rec.name
