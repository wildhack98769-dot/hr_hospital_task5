from odoo import fields
from odoo.exceptions import AccessError, ValidationError
from odoo.tests.common import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestHospitalModule(TransactionCase):
    """Regression tests for the hospital module access rules and model actions."""

    def _make_user(self, login, group_xmlid):
        """Create a test user in the requested hospital group."""
        group = self.env.ref(group_xmlid)
        return self.env['res.users'].create(
            {
                'name': login.replace('.', ' ').title(),
                'login': login,
                'email': f'{login}@example.com',
                'password': login,
                'company_id': self.env.company.id,
                'company_ids': [(4, self.env.company.id)],
                'groups_id': [(4, group.id)],
            }
        )

    def test_patient_open_patient_visits(self):
        """Patient action should open only the current patient's visits."""
        patient = self.env['hr.hospital.patient'].create({'name': 'Test Patient'})

        action = patient.action_open_patient_visits()

        self.assertEqual(action['domain'], [('patient_id', '=', patient.id)])
        self.assertEqual(action['context']['default_patient_id'], patient.id)

    def test_patient_create_visit_action_sets_defaults(self):
        """Patient quick visit action should prefill patient and doctor."""
        doctor = self.env['hr.hospital.doctor'].create({'name': 'Test Doctor'})
        patient = self.env['hr.hospital.patient'].create(
            {'name': 'Test Patient', 'personal_doctor_id': doctor.id}
        )

        action = patient.action_create_visit()

        self.assertEqual(action['context']['default_patient_id'], patient.id)
        self.assertEqual(action['context']['default_doctor_id'], doctor.id)

    def test_doctor_quick_visit_action_sets_doctor(self):
        """Doctor quick visit action should carry the active doctor."""
        doctor = self.env['hr.hospital.doctor'].create({'name': 'Action Doctor'})

        action = doctor.action_create_quick_visit()

        self.assertEqual(action['context']['default_doctor_id'], doctor.id)

    def test_visit_action_done_sets_state_and_actual_date(self):
        """Visit action_done should mark the record done and stamp the date."""
        patient = self.env['hr.hospital.patient'].create({'name': 'Visit Patient'})
        doctor = self.env['hr.hospital.doctor'].create({'name': 'Visit Doctor'})
        visit = self.env['hr.hospital.visit'].create(
            {
                'patient_id': patient.id,
                'doctor_id': doctor.id,
                'planned_date': fields.Datetime.now(),
            }
        )

        visit.action_done()

        self.assertEqual(visit.state, 'done')
        self.assertTrue(visit.actual_date)

    def test_visit_access_rules_by_group(self):
        """Hospital visit record rules should scope access by the user's role."""
        patient_user = self._make_user('test.patient', 'hr_hospital.group_hospital_patient')
        intern_user = self._make_user('test.intern', 'hr_hospital.group_hospital_intern')
        doctor_user = self._make_user('test.doctor', 'hr_hospital.group_hospital_doctor')
        manager_user = self._make_user('test.manager', 'hr_hospital.group_hospital_manager')

        mentor = self.env['hr.hospital.doctor'].sudo().create(
            {'name': 'Mentor', 'user_id': doctor_user.id}
        )
        intern = self.env['hr.hospital.doctor'].sudo().create(
            {
                'name': 'Intern',
                'user_id': intern_user.id,
                'mentor_id': mentor.id,
            }
        )
        patient = self.env['hr.hospital.patient'].sudo().create(
            {'name': 'Patient', 'user_id': patient_user.id}
        )
        own_visit = self.env['hr.hospital.visit'].sudo().create(
            {
                'patient_id': patient.id,
                'doctor_id': mentor.id,
                'planned_date': fields.Datetime.now(),
            }
        )
        intern_visit = self.env['hr.hospital.visit'].sudo().create(
            {
                'patient_id': patient.id,
                'doctor_id': intern.id,
                'planned_date': fields.Datetime.now(),
            }
        )

        patient_visible = self.env['hr.hospital.visit'].with_user(patient_user).search([])
        self.assertEqual(patient_visible, own_visit)
        with self.assertRaises(AccessError):
            intern_visit.with_user(patient_user).write({'summary': '<p>x</p>'})

        intern_visible = self.env['hr.hospital.visit'].with_user(intern_user).search([])
        self.assertEqual(intern_visible, intern_visit)
        intern_visit.with_user(intern_user).write({'summary': '<p>updated</p>'})

        doctor_visible = self.env['hr.hospital.visit'].with_user(doctor_user).search([])
        self.assertEqual(doctor_visible, own_visit | intern_visit)
        own_visit.with_user(doctor_user).write({'summary': '<p>doctor update</p>'})

        manager_visible = self.env['hr.hospital.visit'].with_user(manager_user).search([])
        self.assertEqual(manager_visible, own_visit | intern_visit)

    def test_doctor_intern_mentor_constraint(self):
        """Doctor mentor validation should reject invalid intern relations."""
        intern_category = self.env['hr.hospital.doctor.category'].create(
            {'name': 'Test Intern Category', 'is_intern_category': True}
        )
        doctor_category = self.env['hr.hospital.doctor.category'].create(
            {'name': 'Test Doctor Category', 'is_intern_category': False}
        )
        intern_mentor = self.env['hr.hospital.doctor'].create(
            {'name': 'Intern Mentor', 'category_id': intern_category.id}
        )
        valid_doctor = self.env['hr.hospital.doctor'].create(
            {'name': 'Valid Doctor', 'category_id': doctor_category.id}
        )

        with self.assertRaises(ValidationError):
            self.env['hr.hospital.doctor'].create(
                {
                    'name': 'Bad Intern',
                    'category_id': intern_category.id,
                    'mentor_id': intern_mentor.id,
                }
            )

        with self.assertRaises(ValidationError):
            valid_doctor.write({'mentor_id': intern_mentor.id})

    def test_disease_display_name_is_hierarchical(self):
        """Disease display name should include the parent disease name."""
        parent = self.env['hr.hospital.disease'].create(
            {'name': 'Parent Disease Group', 'is_group': True, 'code': 'P00'}
        )
        child = self.env['hr.hospital.disease'].create({'name': 'Child Disease', 'parent_id': parent.id, 'code': 'P01'})

        self.assertEqual(child.display_name, 'Parent Disease Group / Child Disease')

    def test_dashboard_actions_follow_role_access(self):
        """Dashboard actions should follow the role-based access matrix."""
        patient_user = self._make_user('dash.patient', 'hr_hospital.group_hospital_patient')
        intern_user = self._make_user('dash.intern', 'hr_hospital.group_hospital_intern')
        doctor_user = self._make_user('dash.doctor', 'hr_hospital.group_hospital_doctor')
        manager_user = self._make_user('dash.manager', 'hr_hospital.group_hospital_manager')

        dashboard = self.env['hr.hospital.dashboard'].create({})

        dashboard.with_user(patient_user).action_open_visits()
        dashboard.with_user(intern_user).action_open_visits()

        with self.assertRaises(AccessError):
            dashboard.with_user(patient_user).action_open_patients()

        with self.assertRaises(AccessError):
            dashboard.with_user(intern_user).action_open_diseases()

        dashboard.with_user(doctor_user).action_open_patients()
        dashboard.with_user(doctor_user).action_open_doctor_history()
        dashboard.with_user(manager_user).action_open_doctors()

    def test_doctor_group_can_edit_doctor_cards(self):
        """Doctor users should be able to edit doctor cards, but not delete them."""
        doctor_user = self._make_user('doctor.card', 'hr_hospital.group_hospital_doctor')
        doctor = self.env['hr.hospital.doctor'].sudo().create(
            {'name': 'Editable Doctor', 'user_id': doctor_user.id}
        )

        doctor.with_user(doctor_user).write({'specialization': 'Updated Specialization'})
        self.assertEqual(doctor.specialization, 'Updated Specialization')

        with self.assertRaises(AccessError):
            doctor.with_user(doctor_user).unlink()
