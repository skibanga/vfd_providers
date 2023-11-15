import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


def execute():
    fields = {
        "Sales Invoice": [
            {
                "fieldname": "generate_vfd",
                "label": "Generate VFD",
                "fieldtype": "Button",
                "insert_after": "due_date",
                "module_def": "VFD Providers",
                "depends_on": "eval: doc.docstatus == 1 &&\
                    doc.is_not_vfd_invoice == 0 && \
                    doc.vfd_status != 'Success' && \
                    doc.is_return == 0",
                "allow_on_submit": 1,
            },
            {
                "fieldname": "vfd_details",
                "fieldtype": "Section Break",
                "label": "VFD Details",
                "insert_after": "against_income_account",
                "module_def": "VFD Providers",
            },
            {
                "fieldname": "vfd_date",
                "label": "VFD Date",
                "fieldtype": "Date",
                "insert_after": "vfd_details",
                "allow_on_submit": 1,
                "read_only": 1,
                "module_def": "VFD Providers",
                "allow_on_submit": 1,
            },
            {
                "fieldname": "vfd_time",
                "label": "VFD Time",
                "fieldtype": "Time",
                "insert_after": "vfd_date",
                "allow_on_submit": 1,
                "read_only": 1,
                "module_def": "VFD Providers",
            },
            {
                "fieldname": "vfd_posting_info",
                "fieldtype": "Link",
                "label": "VFD Provider Posting",
                "options": "VFD Provider Posting",
                "insert_after": "vfd_time",
                "allow_on_submit": 1,
                "read_only": 1,
            },
            {
                "fieldname": "vfd_verification_url",
                "fieldtype": "Data",
                "label": "VFD Verification URL",
                "insert_after": "vfd_posting_info",
                "module_def": "VFD Providers",
            },
            {
                "fieldname": "column_break_vfd",
                "label": "",
                "fieldtype": "Column Break",
                "insert_after": "vfd_verification_url",
                "module_def": "VFD Providers",
            },
            {
                "fieldname": "vfd_status",
                "fieldtype": "Select",
                "label": "VFD Status",
                "options": "Not Sent\nPending\nFailed\nSuccess",
                "insert_after": "column_break_vfd",
                "default": "Not Sent",
                "in_list_view": 1,
                "allow_on_submit": 1,
                "read_only": 1,
                "module_def": "VFD Providers",
                "allow_on_submit": 1,
            },
            {
                "fieldname": "is_not_vfd_invoice",
                "fieldtype": "Check",
                "label": "Is Not VFD Invoice",
                "insert_after": "vfd_status",
                "module_def": "VFD Providers",
            },
            {
                "fieldname": "is_auto_generate_vfd",
                "fieldtype": "Check",
                "label": "Is Auto Generate VFD",
                "insert_after": "is_not_vfd_invoice",
                "allow_on_submit": 1,
                "module_def": "VFD Providers",
            },
            {
                "fieldname": "vfd_cust_id",
                "label": "VFD Cust ID",
                "fieldtype": "Data",
                "fetch_from": "customer.vfd_cust_id",
                "fetch_if_empty": 1,
                "insert_after": "is_auto_generate_vfd",
                "module_def": "VFD Providers",
                "allow_on_submit": 1,
            },
            {
                "fieldname": "vfd_cust_id_type",
                "label": "VFD Cust ID Type",
                "fieldtype": "Data",
                "fetch_from": "customer.vfd_cust_id_type",
                "fetch_if_empty": 1,
                "insert_after": "vfd_cust_id",
                "module_def": "VFD Providers",
            },
        ],
        "Item Tax Template": [
            {
                "fieldname": "vfd_taxcode",
                "fieldtype": "Data",
                "label": "VFD TAXCODE",
                "insert_after": "taxes",
                "module_def": "VFD Providers",
                "allow_on_submit": 1,
            },
        ],
        "Mode of Payment": [
            {
                "fieldname": "vfd_payment_type",
                "fieldtype": "Data",
                "label": "VFD Payment Type",
                "insert_after": "accounts",
                "module_def": "VFD Providers",
            },
        ],
    }

    create_custom_fields(fields, update=True)

    frappe.clear_cache(doctype="Sales Invoice")
