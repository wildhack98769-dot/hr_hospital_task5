from dateutil.relativedelta import relativedelta

from odoo import fields, models
from odoo.exceptions import UserError


class HospitalDiseaseReport(models.TransientModel):
    """Wizard that generates the disease statistics PDF report."""

    _name = 'hr.hospital.disease.report'
    _description = 'Hospital Disease Report Wizard'

    def _default_start_date(self):
        """Return the first day of the current month."""
        today = fields.Date.context_today(self)
        return today.replace(day=1)

    def _default_end_date(self):
        """Return the last day of the current month."""
        today = fields.Date.context_today(self)
        start = today.replace(day=1)
        next_month = start + relativedelta(months=1)
        return next_month - relativedelta(days=1)

    start_date = fields.Date(string='Start Date', required=True, default=_default_start_date)
    end_date = fields.Date(string='End Date', required=True, default=_default_end_date)
    doctor_ids = fields.Many2many('hr.hospital.doctor', string='Doctors')
    disease_ids = fields.Many2many(
        'hr.hospital.disease',
        string='Diseases',
        domain=[('is_group', '=', False)],
    )

    def _get_records(self):
        """Fetch visits matching the current report filters."""
        self.ensure_one()
        domain = [
            ('planned_date', '>=', self.start_date),
            ('planned_date', '<=', self.end_date),
        ]
        if self.doctor_ids:
            domain.append(('doctor_id', 'in', self.doctor_ids.ids))
        if self.disease_ids:
            domain.append(('disease_id', 'in', self.disease_ids.ids))
        return self.env['hr.hospital.visit'].search(domain, order='disease_id, planned_date, id')

    def action_generate_report(self):
        """Generate the PDF report for the selected visits."""
        self.ensure_one()
        records = self._get_records()
        if not records:
            raise UserError('No visits found for the selected criteria.')
        return self.env.ref('hr_hospital.action_report_disease_statistics').report_action(records)
