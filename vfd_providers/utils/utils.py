import click
import frappe
from frappe import _
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


def make_custom_fields():
    create_custom_fields(
        {
            "Sales Invoice": [
                {
                    "default": "0",
                    "fieldname": "is_not_vfd_invoice",
                    "fieldtype": "Check",
                    "label": "Is Not VFD Invoice",
                },
                {
                    "default": "0",
                    "fieldname": "is_auto_generate_vfd",
                    "fieldtype": "Check",
                    "label": "Is Auto Generate VFD",
                },
                {
                    "default": "Not Sent",
                    "fieldname": "vfd_status",
                    "fieldtype": "Data",
                    "label": "VFD Status",
                },
                {
                    "fieldname": "vfd_posting_info",
                    "fieldtype": "Data",
                    "label": "VFD Provider Posting",
                },
                {
                    "fieldname": "vfd_verification_url",
                    "fieldtype": "Data",
                    "label": "VFD Verification URL",
                },
                {
                    "label": "VFD Cust ID",
                    "fieldtype": "Data",
                    "fieldname": "vfd_cust_id",
                    "fetch_from": "customer.vfd_cust_id",
                    "fetch_if_empty": True,
                },
                {
                    "label": "VFD Details",
                    "fieldname": "vfd_details",
                    "fieldtype": "Section Break",
                    "insert_after": "amended_from",
                },
                {
                    "label": "VFD Cust ID Type",
                    "fieldtype": "Data",
                    "fieldname": "vfd_cust_id_type",
                    "fetch_from": "customer.vfd_cust_id_type",
                    "fetch_if_empty": True,
                },
                {
                    "label": "VFD Date",
                    "fieldtype": "Date",
                    "fieldname": "vfd_date",
                },
                {
                    "label": "VFD Time",
                    "fieldtype": "Time",
                    "fieldname": "vfd_time",
                },
            ]
        },
        {
            "Item Tax Template": [
                {
                    "fieldname": "vfd_tax_code",
                    "fieldtype": "Data",
                    "label": "VFD Tax Code",
                },
            ]
        },
        {
            "Mode of Payment": [
                {
                    "fieldname": "vfd_payment_type",
                    "fieldtype": "Data",
                    "label": "VFD Payment Type",
                },
            ]
        },
    )

    frappe.clear_cache(doctype="Sales Invoice")


@frappe.whitelist()
def generate_tra_vfd(docname, sinv_doc=None):
    if not sinv_doc:
        sinv_doc = frappe.get_doc("Sales Invoice", docname)
    if sinv_doc.is_not_vfd_invoice or sinv_doc.vfd_status == "Sent":
        return
    comp_vfd_provider = frappe.get_cached_doc(
        "Company VFD Provider", filters={"name": sinv_doc.company}
    )
    if not comp_vfd_provider:
        return
    vfd_provider = frappe.get_cached_doc(
        "VFD Provider", filters={"name": comp_vfd_provider.vfd_provider}
    )
    if not vfd_provider:
        return
    vfd_provider_settings = frappe.get_cached_doc(
        "VFD Provider Settings", filters={"name": vfd_provider.vfd_provider_settings}
    )
    if not vfd_provider_settings:
        return
    if vfd_provider_settings.vfd_provider == "VFDPlus":
        from vfd_providers.vfd_providers.doctype.vfdplus_settings.vfdplus_settings import (
            post_fiscal_receipt,
        )

        post_fiscal_receipt(sinv_doc)


def autogenerate_vfd(doc, method):
    if doc.is_not_vfd_invoice or doc.vfd_status == "Sent":
        return
    if doc.is_auto_generate_vfd and doc.docstatus == 1:
        generate_tra_vfd(docname=doc.name, sinv_doc=doc)
