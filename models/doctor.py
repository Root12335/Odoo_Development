from odoo import fields, models


class HmsDoctor(models.Model):
    _name = "hms.doctors"
    _description = "HMS Doctor"
    _rec_name = "first_name"

    first_name = fields.Char(string="First Name", required=True)
    last_name = fields.Char(string="Last Name", required=True)
    image = fields.Binary(string="Image")