import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


def execute():
    fields = {
        "Sales Invoice": [
            {
                "fieldname": "vfd_verification_url",
                "fieldtype": "Data",
                "label": "VFD Verification URL",
                "insert_after": "vfd_posting_info",
                "module_def": "VFD Providers",
                "allow_on_submit": 1,
                "length": "1000"
            },
        ],
    }

    create_custom_fields(fields, update=True)
    