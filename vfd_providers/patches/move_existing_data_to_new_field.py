import frappe


def migrate_data():
    def field_exists(doctype, fieldname):
        return frappe.db.has_column(doctype, fieldname)

    def field_empty_filter(fieldname):
        return [fieldname, "in", (None, "")]

    def process_batch(doctype, fields, conditions, limit_page_length):
        start = 0
        while True:
            records = frappe.get_all(
                doctype,
                fields=fields,
                filters=conditions,
                limit_start=start,
                limit_page_length=limit_page_length,
                order_by="creation desc",  
            )

            if not records:
                break

            for record in records:
                if record.vfd_custidtype is None or record.vfd_custidtype == "":
                    frappe.db.set_value(
                        doctype,
                        record.name,
                        "vfd_custidtype",
                        record.vfd_cust_id_type,
                        update_modified=False,
                    )
                if record.vfd_custid is None or record.vfd_custid == "":
                    frappe.db.set_value(
                        doctype,
                        record.name,
                        "vfd_custid",
                        record.vfd_cust_id,
                        update_modified=False,
                    )
            frappe.db.commit()
            start += limit_page_length

    if field_exists("Sales Invoice", "vfd_cust_id_type") and field_exists(
        "Sales Invoice", "vfd_cust_id"
    ):

        conditions = [
            field_empty_filter("vfd_custidtype"),
            field_empty_filter("vfd_custid"),
        ]
        process_batch(
            "Sales Invoice",
            fields=[
                "name",
                "vfd_cust_id_type",
                "vfd_cust_id",
                "vfd_custidtype",
                "vfd_custid",
            ],
            conditions=conditions,
            limit_page_length=10000, 
        )

    if field_exists("Customer", "vfd_cust_id_type") and field_exists(
        "Customer", "vfd_cust_id"
    ):
        conditions = [
            field_empty_filter("vfd_custidtype"),
            field_empty_filter("vfd_custid"),
        ]
        process_batch(
            "Customer",
            fields=[
                "name",
                "vfd_cust_id_type",
                "vfd_cust_id",
                "vfd_custidtype",
                "vfd_custid",
            ],
            conditions=conditions,
            limit_page_length=10000,  
        )

    drop_fields()    


def drop_fields():
    def drop_field(doctype, fieldname):
        if frappe.db.has_column(doctype, fieldname):
            frappe.db.sql(f"ALTER TABLE `tab{doctype}` DROP COLUMN `{fieldname}`")

    def delete_custom_field(doctype, fieldname):
        custom_field_name = f"{doctype}-{fieldname}"
        if frappe.db.exists("Custom Field", custom_field_name):
            frappe.delete_doc("Custom Field", custom_field_name)

    drop_field("Sales Invoice", "vfd_cust_id_type")
    drop_field("Sales Invoice", "vfd_cust_id")

    drop_field("Customer", "vfd_cust_id_type")
    drop_field("Customer", "vfd_cust_id")

    delete_custom_field("Sales Invoice", "vfd_cust_id_type")
    delete_custom_field("Sales Invoice", "vfd_cust_id")
    delete_custom_field("Customer", "vfd_cust_id_type")
    delete_custom_field("Customer", "vfd_cust_id")
    frappe.db.commit()
