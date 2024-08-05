import click
import frappe
from frappe import _


@frappe.whitelist()
def generate_tra_vfd(docname, sinv_doc=None, method="POST"):
    if not sinv_doc:
        sinv_doc = frappe.get_doc("Sales Invoice", docname)
    if sinv_doc.is_not_vfd_invoice or sinv_doc.vfd_status in ["Sent", "Success"]:
        return
    comp_vfd_provider = frappe.get_cached_doc("Company VFD Provider", sinv_doc.company)
    if not comp_vfd_provider:
        return
    vfd_provider = frappe.get_cached_doc("VFD Provider", comp_vfd_provider.vfd_provider)
    if not vfd_provider:
        return
    vfd_provider_settings = vfd_provider.vfd_provider_settings

    if not vfd_provider_settings:
        return
    if vfd_provider.name == "VFDPlus":
        from vfd_providers.vfd_providers.doctype.vfdplus_settings.vfdplus_settings import (
            post_fiscal_receipt,
        )
    elif vfd_provider.name == "TotalVFD":
        from vfd_providers.vfd_providers.doctype.total_vfd_setting.total_vfd_setting import (
            post_fiscal_receipt,
        )
    else:
        frappe.throw(_("VFD Provider not supported"))

    post_fiscal_receipt(sinv_doc, method)


def autogenerate_vfd(doc, method):
    if doc.is_not_vfd_invoice or doc.vfd_status == "Sent":
        return
    if doc.is_auto_generate_vfd and doc.docstatus == 1:
        generate_tra_vfd(docname=doc.name, sinv_doc=doc, method=method)


def clean_and_update_tax_id_info(doc, method):
    cleaned_tax_id = "".join(char for char in (doc.tax_id or "") if char.isdigit())
    doc.tax_id = cleaned_tax_id
    if doc.tax_id:
        doc.vfd_custidtype = "1- TIN"
        doc.vfd_custid = doc.tax_id
    else:
        doc.vfd_custidtype = "6- Other"
        doc.vfd_custid = "999999999"
