from dateutil.relativedelta import relativedelta

from odoo import fields, models


class HospitalDiseaseMonthReport(models.TransientModel):
    """Wizard that opens a grouped monthly disease analysis view."""

    _name = 'hr.hospital.disease.month.report'
    _description = 'Hospital Disease Month Report Wizard'

    def _default_date_from(self):
        """Return the first day of the current month."""
        today = fields.Date.context_today(self)
        return today.replace(day=1)

    def _default_date_to(self):
        """Return the last day of the current month."""
        today = fields.Date.context_today(self)
        start = today.replace(day=1)
        return start + relativedelta(months=1, days=-1)

    date_from = fields.Date(string='From', required=True, default=_default_date_from)
    date_to = fields.Date(string='To', required=True, default=_default_date_to)
    doctor_ids = fields.Many2many('hr.hospital.doctor', string='Doctors')
    disease_ids = fields.Many2many('hr.hospital.disease', string='Diseases', domain=[('is_group', '=', False)])

    def action_generate_report(self):
        """Open the visit list grouped by disease for the selected period."""
        self.ensure_one()
        domain = [
            ('planned_date', '>=', self.date_from),
            ('planned_date', '<=', self.date_to),
        ]
        if self.doctor_ids:
            domain.append(('doctor_id', 'in', self.doctor_ids.ids))
        if self.disease_ids:
            domain.append(('disease_id', 'in', self.disease_ids.ids))

        action = self.env.ref('hr_hospital.action_hr_hospital_visit').read()[0]
        action['domain'] = domain
        action['context'] = dict(self.env.context, group_by='disease_id')
        action['views'] = [
            (self.env.ref('hr_hospital.view_hr_hospital_visit_list').id, 'list'),
            (self.env.ref('hr_hospital.view_hr_hospital_visit_form').id, 'form'),
        ]
        action['name'] = 'Disease Month Report'
        return action
