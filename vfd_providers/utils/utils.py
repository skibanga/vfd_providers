import click
import frappe
from frappe import _
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


def make_custom_fields():
    create_custom_fields(
        {
            "Web Form": [
                {
                    "fieldname": "payments_tab",
                    "fieldtype": "Tab Break",
                    "label": "Payments",
                    "insert_after": "custom_css",
                },
                {
                    "default": "0",
                    "fieldname": "accept_payment",
                    "fieldtype": "Check",
                    "label": "Accept Payment",
                    "insert_after": "payments",
                },
                {
                    "depends_on": "accept_payment",
                    "fieldname": "payment_gateway",
                    "fieldtype": "Link",
                    "label": "Payment Gateway",
                    "options": "Payment Gateway",
                    "insert_after": "accept_payment",
                },
                {
                    "default": "Buy Now",
                    "depends_on": "accept_payment",
                    "fieldname": "payment_button_label",
                    "fieldtype": "Data",
                    "label": "Button Label",
                    "insert_after": "payment_gateway",
                },
                {
                    "depends_on": "accept_payment",
                    "fieldname": "payment_button_help",
                    "fieldtype": "Text",
                    "label": "Button Help",
                    "insert_after": "payment_button_label",
                },
                {
                    "fieldname": "payments_cb",
                    "fieldtype": "Column Break",
                    "insert_after": "payment_button_help",
                },
                {
                    "default": "0",
                    "depends_on": "accept_payment",
                    "fieldname": "amount_based_on_field",
                    "fieldtype": "Check",
                    "label": "Amount Based On Field",
                    "insert_after": "payments_cb",
                },
                {
                    "depends_on": "eval:doc.accept_payment && doc.amount_based_on_field",
                    "fieldname": "amount_field",
                    "fieldtype": "Select",
                    "label": "Amount Field",
                    "insert_after": "amount_based_on_field",
                },
                {
                    "depends_on": "eval:doc.accept_payment && !doc.amount_based_on_field",
                    "fieldname": "amount",
                    "fieldtype": "Currency",
                    "label": "Amount",
                    "insert_after": "amount_field",
                },
                {
                    "depends_on": "accept_payment",
                    "fieldname": "currency",
                    "fieldtype": "Link",
                    "label": "Currency",
                    "options": "Currency",
                    "insert_after": "amount",
                },
            ]
        }
    )

    frappe.clear_cache(doctype="Web Form")


@frappe.whitelist()
def generate_tra_vfd(docname):
    sinv_doc = frappe.get_doc("Sales Invoice", docname)
    if (
        sinv_doc.is_not_vfd_invoice
        or sinv_doc.do_not_send_vfd
        or sinv_doc.vfd_status == "Sent"
    ):
        return
    comp_vfd_provider = frappe.get_doc(
        "Company VFD Provider", filters={"name": sinv_doc.company}
    )
    if not comp_vfd_provider:
        return
    vfd_provider = frappe.get_doc(
        "VFD Provider", filters={"name": comp_vfd_provider.vfd_provider}
    )
    if not vfd_provider:
        return
    vfd_provider_settings = frappe.get_doc(
        "VFD Provider Settings", filters={"name": vfd_provider.vfd_provider_settings}
    )
    if not vfd_provider_settings:
        return
    vfd_provider_settings.send_vfd_request(doc=sinv_doc, method="validate")


def autogenerate_vfd(doc, method):
    if doc.is_not_vfd_invoice or doc.do_not_send_vfd or doc.vfd_status == "Sent":
        return
    if doc.docstatus == 1:
        generate_tra_vfd(docname=doc.name)
