from odoo import api, fields, models
from odoo.exceptions import ValidationError


class HospitalDoctor(models.Model):
    _name = 'hr.hospital.doctor'
    _description = 'Hospital Doctor'

    _inherit = 'hr.hospital.medic.info'

    name = fields.Char(string='Full Name', required=True)
    specialization = fields.Char(string='Specialization')

    category_id = fields.Many2one(
        comodel_name='hr.hospital.doctor.category',
        string='Category',
        ondelete='restrict',
    )

    user_id = fields.Many2one(
        comodel_name='res.users',
        string='System User',
    )

    is_intern = fields.Boolean(
        string='Is Intern',
        compute='_compute_is_intern',
        store=True,
    )

    mentor_id = fields.Many2one(
        comodel_name='hr.hospital.doctor',
        string='Mentor Doctor',
        help='Only non-intern doctors can be mentors.',
        domain="[('is_intern', '=', False)]",
    )

    intern_ids = fields.One2many(
        comodel_name='hr.hospital.doctor',
        inverse_name='mentor_id',
        string='Interns',
    )

    visit_ids = fields.One2many(
        comodel_name='hr.hospital.visit',
        inverse_name='doctor_id',
        string='Visits',
    )

    @api.depends('category_id')
    def _compute_is_intern(self):
        for rec in self:
            rec.is_intern = rec.category_id.is_intern_category if rec.category_id else False

    @api.constrains('mentor_id', 'is_intern')
    def _check_mentor_intern_status(self):
        for rec in self:
            if rec.is_intern:
                if rec.mentor_id:
                    if rec.mentor_id.is_intern:
                        raise ValidationError(self.env._('A mentor cannot be an intern!'))
                    if rec.mentor_id == rec:
                        raise ValidationError(self.env._('A doctor cannot be their own mentor!'))
            else:
                if rec.mentor_id:
                    raise ValidationError(self.env._('Only interns can have a mentor.'))

    def _get_report_visit_history(self):
        self.ensure_one()
        return self.visit_ids.sorted(lambda visit: (visit.planned_date, visit.id), reverse=True)

    def _get_report_patient_rows(self):
        self.ensure_one()
        rows = []
        seen_patient_ids = set()
        for visit in self._get_report_visit_history():
            patient = visit.patient_id
            if not patient or patient.id in seen_patient_ids:
                continue
            seen_patient_ids.add(patient.id)
            rows.append(
                {
                    'patient': patient,
                    'gender_label': dict(patient._fields['gender'].selection).get(patient.gender, ''),
                    'date_of_birth': patient.date_of_birth,
                    'phone': patient.phone,
                    'status': visit.state,
                    'status_label': dict(self.env['hr.hospital.visit']._fields['state'].selection).get(visit.state, ''),
                    'visit_date': visit.planned_date,
                }
            )
        return rows

    def _get_report_print_datetime(self):
        return fields.Datetime.now().strftime('%Y-%m-%d %H:%M')
