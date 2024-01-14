import frappe

def execute():
    frappe.db.set_value("Custom Field", "Sales Invoice-vfd_posting_info", "options", "VFD Provider Posting")
    frappe.delete_doc('Custom Field', 'Sales Invoice-vfd_z_report')