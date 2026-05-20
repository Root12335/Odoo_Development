    from odoo import api, fields, models, tools
from odoo.exceptions import ValidationError


class HmsPatient(models.Model):
    _name = "hms.patient"
    _description = "HMS Patient"
    _rec_name = "first_name"
    _sql_constraints = [
        (
            "unique_patient_email",
            "unique(email)",
            "Patient email must be unique.",
        ),
    ]

    first_name = fields.Char(string="First Name")
    last_name = fields.Char(string="Last Name")
    birthdate = fields.Date(string="Birthdate")
    email = fields.Char(string="Email")
    history = fields.Html(string="History")
    cr_ratio = fields.Float(string="CR Ratio")
    state = fields.Selection(
        [
            ("undetermined", "Undetermined"),
            ("good", "Good"),
            ("fair", "Fair"),
            ("serious", "Serious"),
        ],
        string="State",
        default="undetermined",
    )
    blood_type = fields.Selection(
        [
            ("a_pos", "A+"),
            ("a_neg", "A-"),
            ("b_pos", "B+"),
            ("b_neg", "B-"),
            ("ab_pos", "AB+"),
            ("ab_neg", "AB-"),
            ("o_pos", "O+"),
            ("o_neg", "O-")
        ],
        string="Blood Type"
    )
    pcr = fields.Boolean(string="PCR")
    image = fields.Binary(string="Image")
    address = fields.Text(string="Address")
    age = fields.Integer(string="Age", compute="_compute_age", readonly=True)
    department_id = fields.Many2one(
        "hms.department",
        string="Department",
        domain="[('is_opened', '=', True)]",
    )
    department_capacity = fields.Integer(
        string="Department Capacity",
        related="department_id.capacity",
        readonly=True,
    )
    doctor_ids = fields.Many2many(
        "hms.doctors",
        string="Doctors",
    )
    log_history_ids = fields.One2many(
        "hms.patient.log",
        "patient_id",
        string="Log History",
    )

    def _get_age_from_birthdate(self, birthdate):
        if not birthdate:
            return 0

        today = fields.Date.context_today(self)
        age = today.year - birthdate.year
        if (today.month, today.day) < (birthdate.month, birthdate.day):
            age -= 1
        return max(age, 0)

    @api.depends("birthdate")
    def _compute_age(self):
        for record in self:
            record.age = record._get_age_from_birthdate(record.birthdate)

    @api.onchange("birthdate")
    def _onchange_birthdate(self):
        if self.birthdate and self._get_age_from_birthdate(self.birthdate) < 30 and not self.pcr:
            self.pcr = True
            return {
                "warning": {
                    "title": "PCR Checked",
                    "message": "PCR has been checked automatically because the patient age is lower than 30.",
                }
            }
        return {}

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            birthdate = fields.Date.to_date(vals.get("birthdate"))
            if birthdate and self._get_age_from_birthdate(birthdate) < 30:
                vals["pcr"] = True

        patients = super().create(vals_list)
        return patients

    def write(self, vals):
        old_states = {patient.id: patient.state for patient in self}

        if vals.get("birthdate"):
            birthdate = fields.Date.to_date(vals["birthdate"])
            if self._get_age_from_birthdate(birthdate) < 30:
                vals["pcr"] = True

        result = super().write(vals)

        if "state" in vals:
            for patient in self:
                if old_states.get(patient.id) != patient.state:
                    patient._create_log_history(f"State changed to {patient._get_state_label()}")
        return result

    def _get_state_label(self):
        return dict(self._fields["state"].selection).get(self.state, self.state)

    def _create_log_history(self, description):
        self.env["hms.patient.log"].create({
            "patient_id": self.id,
            "created_by_id": self.env.user.id,
            "date": fields.Datetime.now(),
            "description": description,
        })

    @api.constrains("pcr", "cr_ratio")
    def _check_cr_ratio_required(self):
        for record in self:
            if record.pcr and not record.cr_ratio:
                raise ValidationError("CR Ratio is mandatory when PCR is checked.")

    @api.constrains("department_id")
    def _check_department_is_opened(self):
        for record in self:
            if record.department_id and not record.department_id.is_opened:
                raise ValidationError("Patients cannot be assigned to a closed department.")

    @api.constrains("email")
    def _check_email(self):
        for record in self:
            if record.email and not tools.email_normalize(record.email, strict=False):
                raise ValidationError("Please enter a valid patient email address.")

    @api.constrains("email")
    def _check_unique_email(self):
        for record in self:
            if record.email:
                patient = self.search([
                    ("id", "!=", record.id),
                    ("email", "=ilike", record.email),
                ], limit=1)
                if patient:
                    raise ValidationError("Patient email must be unique.")


class HmsPatientLog(models.Model):
    _name = "hms.patient.log"
    _description = "HMS Patient Log"
    _order = "date desc"

    patient_id = fields.Many2one(
        "hms.patient",
        string="Patient",
        required=True,
        ondelete="cascade",
    )
    created_by_id = fields.Many2one(
        "res.users",
        string="Created By",
        required=True,
        default=lambda self: self.env.user,
        readonly=True,
    )
    date = fields.Datetime(
        string="Date",
        required=True,
        default=fields.Datetime.now,
        readonly=True,
    )
    description = fields.Char(string="Description", required=True, readonly=True)
