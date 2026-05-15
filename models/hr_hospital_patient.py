from odoo import _, fields, models


class HospitalPatient(models.Model):
    """Model representing patients receiving treatment."""

    _name = 'hr.hospital.patient'
    _description = 'Hospital Patient'
    _inherit = ['hr.hospital.medic.info']

    name = fields.Char(string='Full Name', required=True)
    user_id = fields.Many2one(
        comodel_name='res.users',
        string='User',
        help='Links the patient to the Odoo user account that can see their visits.',
    )
    date_of_birth = fields.Date(string='Date of Birth')
    gender = fields.Selection(
        selection=[
            ('male', 'Male'),
            ('female', 'Female'),
            ('other', 'Other'),
        ],
        string='Gender',
    )

    personal_doctor_id = fields.Many2one(
        comodel_name='hr.hospital.doctor',
        string='Personal Doctor',
    )

    doctor_history_ids = fields.One2many(
        comodel_name='hr.hospital.doctor.history',
        inverse_name='patient_id',
        string='Doctor History',
    )

    insurance_policy = fields.Char(string='Insurance Policy', size=20)

    def action_open_patient_visits(self):
        """Opens the list of visits for the current patient."""
        self.ensure_one()
        return {
            'name': _('Patient Visits'),
            'type': 'ir.actions.act_window',
            'res_model': 'hr.hospital.visit',
            'view_mode': 'list,form',
            'domain': [('patient_id', '=', self.id)],
            'context': {'default_patient_id': self.id},
        }

    def action_create_visit(self):
        """Open a visit form prefilled with the current patient."""
        self.ensure_one()
        action = self.env.ref('hr_hospital.action_hr_hospital_visit').read()[0]
        action['views'] = [(self.env.ref('hr_hospital.view_hr_hospital_visit_form').id, 'form')]
        action['target'] = 'new'
        context = dict(self.env.context, default_patient_id=self.id)
        if self.personal_doctor_id:
            context['default_doctor_id'] = self.personal_doctor_id.id
        action['context'] = context
        return action
