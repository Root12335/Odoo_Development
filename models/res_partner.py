from odoo import api, fields, models
from odoo.exceptions import ValidationError


class ResPartner(models.Model):
    _inherit = "res.partner"

    related_patient_id = fields.Many2one(
        "hms.patient",
        string="Related Patient",
        copy=False,
    )

    @api.constrains("related_patient_id", "email")
    def _check_related_patient_email_conflict(self):
        for partner in self:
            if partner.related_patient_id and partner.related_patient_id.email:
                duplicate_partner = self.search([
                    ("id", "!=", partner.id),
                    ("email", "=ilike", partner.related_patient_id.email),
                ], limit=1)
                if duplicate_partner:
                    raise ValidationError(
                        "This patient cannot be linked because the patient email is already assigned "
                        f"to customer '{duplicate_partner.display_name}'."
                    )

    @api.constrains("vat", "parent_id")
    def _check_vat_for_crm_customers(self):
        if self.env.context.get("res_partner_search_mode") != "customer":
            return

        for partner in self.filtered(lambda rec: not rec.parent_id and not rec.vat):
            raise ValidationError("Tax ID is mandatory for CRM customers.")
