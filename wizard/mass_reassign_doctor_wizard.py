from odoo import fields, models


class MassReassignDoctorWizard(models.TransientModel):
    """Wizard that mass-updates the personal doctor for selected patients."""

    _name = 'mass.reassign.doctor.wizard'
    _description = 'Mass Reassign Doctor Wizard'
    _rec_name = 'name'

    name = fields.Char(default='Reassign Doctor', readonly=True)
    doctor_id = fields.Many2one('hr.hospital.doctor', string='New Doctor', required=True)
    change_date = fields.Date(string='Change Date', default=fields.Date.context_today)

    def action_reassign_doctor(self):
        """Apply the selected doctor to all patients in the active selection."""
        patient_ids = self.env.context.get('active_ids')
        patients = self.env['hr.hospital.patient'].browse(patient_ids)
        patients.write({'personal_doctor_id': self.doctor_id.id})
