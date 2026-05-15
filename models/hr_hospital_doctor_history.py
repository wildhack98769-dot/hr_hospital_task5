from odoo import _, api, fields, models


class HospitalDoctorHistory(models.Model):
    """Historical record of doctor assignment changes for patients."""

    _name = 'hr.hospital.doctor.history'
    _description = 'Doctor Appointment History'

    _order = 'appointment_date desc'

    patient_id = fields.Many2one(
        comodel_name='hr.hospital.patient',
        string='Patient',
        required=True,
        ondelete='cascade',
    )
    doctor_id = fields.Many2one(
        comodel_name='hr.hospital.doctor',
        string='Doctor',
        required=True,
        ondelete='restrict',
    )
    appointment_date = fields.Date(string='Appointment Date', required=True, default=fields.Date.context_today)
    change_date = fields.Date(string='Change Date')
    active = fields.Boolean(string='Active', default=True)

    @api.onchange('appointment_date', 'change_date')
    def _onchange_dates(self):
        """Warn when the reassignment date is earlier than the appointment date."""
        if self.appointment_date and self.change_date:
            if self.change_date < self.appointment_date:
                return {
                    'warning': {
                        'title': _('Date Error'),
                        'message': _('The doctor change date cannot be earlier than the appointment date.'),
                    }
                }
        return None

    @api.depends('patient_id', 'doctor_id', 'appointment_date')
    def _compute_display_name(self):
        """Compose a human-readable label for doctor history entries."""
        for rec in self:
            patient_name = rec.patient_id.display_name or _('Unknown Patient')
            doctor_name = rec.doctor_id.display_name or _('Unknown Doctor')
            category = rec.doctor_id.category_id.name if rec.doctor_id.category_id else _('No Category')
            date_str = rec.appointment_date.strftime('%Y-%m-%d') if rec.appointment_date else ''

            rec.display_name = f'{patient_name} - {doctor_name} ({category}) {date_str}'
