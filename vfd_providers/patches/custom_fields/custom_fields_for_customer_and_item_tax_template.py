import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

def execute():
    fields = {
        "Customer": [
            {
                "fieldname": "vfd_details",
                "label": "VFD Details",
                "fieldtype": "Section Break",
                "insert_after": "companies",
                "module_def": "VFD Providers",
            },
            {
                "fieldname": "vfd_cust_id",
                "label": "VFD Customer ID",
                "fieldtype": "Data",
                "insert_after": "vfd_details",
                "reqd": 1,
                "module_def": "VFD Providers",
            },
            {
                "fieldname": "vfd_cust_id_type",
                "label": "VFD Customer ID Type",
                "fieldtype": "Select",
                "insert_after": "vfd_cust_id",
                "options": "\n1- PAN\n2- Passport\n3- Driving License\n4- Voter ID\n5- Aadhaar\n6- Other",
                "reqd": 1,
                "module_def": "VFD Providers",
            },
        ],
        "Item Tax Template": [
            {
                "fieldname": "vfd_taxcode",
                "label": "VFD TAXCODE",
                "fieldtype": "Select",
                "insert_after": "taxes",
                "options": "\n1- Standard Rate (18%)\n2- Special Rate\n3- Zero rated\n4- Special Relief\n5- Exempt",
                "module_def": "VFD Providers",
            }
        ],
    }
    create_custom_fields(fields, update=True)
