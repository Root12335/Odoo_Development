{
    "name": "HMS",
    "summary": "Hospital management system",
    "category": "Healthcare",
    "author": "Amr",
    "depends": ["base"],
    "data": [
        "security/hms_groups.xml",
        "security/ir.model.access.csv",
        "views/hms_patient_views.xml",
        "views/hms_department_views.xml",
        "views/hms_doctor_views.xml",
        "views/res_partner_views.xml"
    ],
    "application": True,
    "installable": True,
    "license": "LGPL-3"
}
