from odoo import api, fields, models


class VisitReportWizard(models.TransientModel):
    """Wizard that builds a filtered list view for hospital visits."""

    _name = 'visit.report.wizard'
    _description = 'Visit Report Wizard'
    _rec_name = 'name'

    name = fields.Char(default='Visit Report', readonly=True)
    doctor_ids = fields.Many2many('hr.hospital.doctor', string='Doctors')
    patient_ids = fields.Many2many('hr.hospital.patient', string='Patients')
    date_start = fields.Date(string='Start Date')
    date_end = fields.Date(string='End Date')
    only_completed = fields.Boolean(string='Only Completed Visits')
    disease_id = fields.Many2one(
        'hr.hospital.disease',
        string='Disease',
        domain=[('is_group', '=', False)],
    )

    @api.model
    def default_get(self, fields_list):
        """Prefill doctors or patients when the wizard is opened from a record."""
        res = super().default_get(fields_list)
        active_model = self.env.context.get('active_model')
        active_ids = self.env.context.get('active_ids')

        if active_model == 'hr.hospital.doctor':
            res['doctor_ids'] = [(6, 0, active_ids)]
        elif active_model == 'hr.hospital.patient':
            res['patient_ids'] = [(6, 0, active_ids)]
        return res

    def action_generate_report(self):
        """Open the visit list with the selected filters applied."""
        domain = []
        if self.doctor_ids:
            domain.append(('doctor_id', 'in', self.doctor_ids.ids))
        if self.patient_ids:
            domain.append(('patient_id', 'in', self.patient_ids.ids))
        if self.date_start:
            domain.append(('planned_date', '>=', self.date_start))
        if self.date_end:
            domain.append(('planned_date', '<=', self.date_end))
        if self.only_completed:
            domain.append(('state', '=', 'done'))
        if self.disease_id:
            domain.append(('disease_id', '=', self.disease_id.id))

        return {
            'name': 'Visit Report',
            'type': 'ir.actions.act_window',
            'res_model': 'hr.hospital.visit',
            'view_mode': 'list,form',
            'domain': domain,
            'target': 'current',
        }
