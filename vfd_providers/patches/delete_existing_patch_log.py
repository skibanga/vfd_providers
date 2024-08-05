import frappe

patch_values = [
    "vfd_providers.patches.custom_fields.vfd_providers_updated_custom_fields"
    # Add other patch values here as needed
]

def delete():
    doctype = "Patch Log"

    for patch_value in patch_values:
        try:
            doc = frappe.get_value(doctype, {"patch": patch_value}, "name")
            doc_name = doc
            
            frappe.delete_doc_if_exists(doctype, doc_name, force=1)
            frappe.db.commit()

        except Exception as e:
            frappe.log_error(f"An error occurred: {str(e)}", "Patch Log Deletion")
