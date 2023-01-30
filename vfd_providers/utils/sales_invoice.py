# -*- coding: utf-8 -*-
# Copyright (c) 2020, Aakvatech and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
import erpnext
from frappe import _

from frappe.utils import flt, nowdate, nowtime, format_datetime
from frappe.utils.background_jobs import enqueue
import json
import re


def vfd_validation(doc, method):
    if doc.is_return or doc.is_not_vfd_invoice:
        return
    if doc.base_net_total == 0:
        frappe.throw(_("Base net amount is zero. Correct the invoice and retry."))

    vfdplus_settings = frappe.get_cached_doc("VFDPlus Settings", doc.company)

    tax_data = get_itemised_tax_breakup_html(doc)
    if not tax_data:
        frappe.throw(_("Taxes not set correctly"))

    for item in doc.items:
        if not item.item_code:
            frappe.throw(_("Item Code not set for item {0}".format(item.item_name)))
        if not item.item_tax_template:
            item_tax_template = frappe.get_value(
                "Item", item.item_code, "default_tax_template"
            )
            if not item_tax_template:
                frappe.throw(
                    _("Item Taxes Template not set for item {0}".format(item.item_code))
                )
            else:
                item.item_tax_template = item_tax_template
        item_taxcode = get_item_taxcode(
            item.item_tax_template, item.item_code, doc.name
        )

        with_tax = 0
        other_tax = 0

        for tax_name, tax_value in tax_data.get(item.item_code).items():
            if tax_value.get("tax_rate") == 18:
                with_tax += 1
            else:
                other_tax += tax_value.get("tax_amount")

        if other_tax:
            frappe.throw(
                _(
                    "Taxes not set correctly for Other Tax item {0}".format(
                        item.item_code
                    )
                )
            )
        if item_taxcode == 1 and with_tax != 1:
            if vfdplus_settings.vat_enabled:
                frappe.msgprint(
                    _(
                        "Taxes is not set to 18pct for Standard Rate item {0}".format(
                            item.item_code
                        )
                    )
                )
            else:
                frappe.throw(
                    _(
                        "Taxes not set correctly for Standard Rate item {0}".format(
                            item.item_code
                        )
                    )
                )
        elif item_taxcode != 1 and with_tax != 0:
            frappe.throw(
                _(
                    "Taxes not set correctly for Non Standard Rate item {0}".format(
                        item.item_code
                    )
                )
            )


def posting_vfd_invoice(invoice_name):
    doc = frappe.get_doc("Sales Invoice", invoice_name)
    if doc.vfd_posting_info or doc.docstatus != 1:
        return
    if doc.vfd_status == "Not Sent":
        doc.vfd_status = "Pending"
        doc.db_update()
        frappe.db.commit()
        doc.reload()
    customer_id_info = get_customer_id_info(doc.customer)
    if not doc.vfd_cust_id:
        vfd_cust_id_type = str(customer_id_info["cust_id_type"])
        vfd_cust_id = customer_id_info["cust_id"]
    elif doc.vfd_cust_id and not doc.vfd_cust_id_type:
        frappe.throw(
            _("Please make sure to set VFD Customer ID Type in Customer Master")
        )
    else:
        vfd_cust_id_type = doc.vfd_cust_id_type
        vfd_cust_id = doc.vfd_cust_id

    rect_data = {
        "DATE": doc.vfd_date,
        # 0:59:30.715164
        "TIME": format_datetime(str(doc.vfd_time), "HH:mm:ss"),
        "CUSTIDTYPE": int(vfd_cust_id_type[:1]),
        "CUSTID": vfd_cust_id,
        "CUSTNAME": remove_special_characters(doc.customer),
        "MOBILENUM": customer_id_info["mobile_no"],
        "RCTNUM": doc.vfd_gc,
        "DC": doc.vfd_dc,
        "GC": doc.vfd_gc,
        "ZNUM": format_datetime(str(doc.vfd_date), "YYYYMMdd"),
        "RCTVNUM": doc.vfd_rctvnum,
        "ITEMS": [],
        "TOTALS": {
            "TOTALTAXEXCL": flt(doc.base_net_total, 2),
            "TOTALTAXINCL": flt(doc.base_grand_total, 2),
            "DISCOUNT": flt(doc.base_discount_amount, 2),
        },
        "PAYMENTS": get_payments(doc.payments, doc.base_grand_total),
        "VATTOTALS": get_vattotals(doc.items, doc.name, vrn),
    }
    for item in doc.items:
        item_data = {
            "ID": remove_special_characters(
                item.item_code
            ),
            "DESC": remove_special_characters(
                item.item_name
            ),
            "QTY": flt(item.stock_qty, 2),
            "TAXCODE": get_item_taxcode(
                item.item_tax_template, item.item_code, doc.name
            ),
            "AMT": flt(get_item_inclusive_amount(item), 2),
        }
        rect_data["ITEMS"].append({"ITEM": item_data})


        posting_info_doc.flags.ignore_permissions = True
        posting_info_doc.insert(ignore_permissions=True)
        doc.vfd_status = "Failed"
        doc.db_update()
        frappe.db.commit()
        return "Failed"

    frappe.db.commit()
    if int(posting_info_doc.ackcode) == 0:
        doc.vfd_posting_info = posting_info_doc.name
        doc.vfd_status = "Success"
        doc.save(ignore_permissions=True)
        frappe.db.commit()
        return "Success"
    else:
        doc.vfd_status = "Failed"
        doc.db_update()
        frappe.db.commit()
        return "Failed"


def get_customer_id_info(customer):
    data = {}
    cust_id, cust_id_type, mobile_no = frappe.get_value(
        "Customer", customer, ["vfd_custid", "vfd_custidtype", "mobile_no"]
    )
    if not cust_id:
        data["cust_id"] = ""
        data["cust_id_type"] = 6
    elif cust_id and not cust_id_type:
        frappe.throw(
            _("Please make sure to set VFD Customer ID Type in Customer Master")
        )
    else:
        data["cust_id"] = cust_id
        data["cust_id_type"] = int(cust_id_type[:1])

    data["mobile_no"] = remove_all_except_numbers(mobile_no) or ""
    return data


def get_item_taxcode(item_tax_template=None, item_code=None, invoice_name=None):
    if not item_tax_template:
        if item_code and invoice_name:
            frappe.throw(
                _(
                    "Item Taxes Template not set for item {0} in invoice {1}".format(
                        item_code, invoice_name
                    )
                )
            )
        elif item_code:
            frappe.throw(
                _("Item Taxes Template not set for item {0}".format(item_code))
            )
        else:
            frappe.throw(_("Item Taxes Template not set"))

    taxcode = None
    if item_tax_template:
        vfd_taxcode = frappe.get_value(
            "Item Tax Template", item_tax_template, "vfd_taxcode"
        )
        if vfd_taxcode:
            taxcode = int(vfd_taxcode[:1])
        else:
            frappe.throw(_("VFD Tax Code not setup in {0}".format(item_tax_template)))
    return taxcode


def get_payments(payments, base_grand_total):
    payments_dict = []
    total_payments_amount = 0
    for payment in payments:
        pmttype = ""
        vfd_pmttype = frappe.get_value(
            "Mode of Payment", payment.mode_of_payment, "vfd_pmttype"
        )
        if vfd_pmttype:
            pmttype = vfd_pmttype
        else:
            frappe.throw(
                _(
                    "VFD Payment Type in Mode of Payment not setup in {0}".format(
                        payment.mode_of_payment
                    )
                )
            )
        total_payments_amount += payment.base_amount
        payments_dict.append({"PMTTYPE": pmttype})
        payments_dict.append({"PMTAMOUNT": flt(payment.base_amount, 2)})

    if base_grand_total > total_payments_amount:
        payments_dict.append({"PMTTYPE": "INVOICE"})
        payments_dict.append(
            {"PMTAMOUNT": flt(base_grand_total - total_payments_amount, 2)}
        )

    return payments_dict


def get_vattotals(items, invoice_name, vrn):
    vattotals = {}
    for item in items:
        item_taxcode = get_item_taxcode(
            item.item_tax_template, item.item_code, invoice_name
        )
        if not vattotals.get(item_taxcode):
            vattotals[item_taxcode] = {}
            vattotals[item_taxcode]["NETTAMOUNT"] = 0
            vattotals[item_taxcode]["TAXAMOUNT"] = 0
        vattotals[item_taxcode]["NETTAMOUNT"] += flt(item.base_net_amount, 2)
        if vrn == "NOT REGISTERED":
            vattotals[item_taxcode]["TAXAMOUNT"] += 0
        else:
            vattotals[item_taxcode]["TAXAMOUNT"] += flt(
                item.base_net_amount * ((18 / 100) if item_taxcode == 1 else 0), 2
            )

    taxes_map = {"1": "A", "2": "B", "3": "C", "4": "D", "5": "E"}

    vattotals_list = []
    for key, value in vattotals.items():
        vattotals_list.append({"VATRATE": taxes_map.get(str(key))})
        vattotals_list.append({"NETTAMOUNT": flt(value["NETTAMOUNT"], 2)})
        vattotals_list.append({"TAXAMOUNT": flt(value["TAXAMOUNT"], 2)})
    return vattotals_list


def validate_cancel(doc, method):
    if doc.vfd_rctnum:
        frappe.throw(_("This invoice cannot be canceled"))


def get_itemised_tax_breakup_html(doc):
    if not doc.taxes:
        return

    itemised_tax = get_itemised_tax_breakup_data(doc)
    get_rounded_tax_amount(itemised_tax, doc.precision("tax_amount", "taxes"))
    return itemised_tax


def get_item_inclusive_amount(item):
    if item.base_net_amount == item.base_amount:
        # this is basic rate included
        item_tax_rate = json.loads(item.item_tax_rate)
        if not item_tax_rate or item_tax_rate == {}:
            return item.base_amount
        else:
            for key, value in item_tax_rate.items():
                if not value or value == 0.00:
                    return flt(item.base_amount, 2)
                return flt(
                    item.base_amount * (1 + (value / 100)), 2
                )  # 118% for 18% VAT
    else:
        return flt(item.base_amount, 2)


@erpnext.allow_regional
def get_itemised_tax_breakup_data(doc):
    itemised_tax = get_itemised_tax(doc.taxes)
    return itemised_tax


def get_itemised_tax(taxes, with_tax_account=False):
    itemised_tax = {}
    for tax in taxes:
        if getattr(tax, "category", None) and tax.category == "Valuation":
            continue

        item_tax_map = (
            json.loads(tax.item_wise_tax_detail) if tax.item_wise_tax_detail else {}
        )
        if item_tax_map:
            for item_code, tax_data in item_tax_map.items():
                itemised_tax.setdefault(item_code, frappe._dict())

                tax_rate = 0.0
                tax_amount = 0.0

                if isinstance(tax_data, list):
                    tax_rate = flt(tax_data[0])
                    tax_amount = flt(tax_data[1])
                else:
                    tax_rate = flt(tax_data)

                itemised_tax[item_code][tax.description] = frappe._dict(
                    dict(tax_rate=tax_rate, tax_amount=tax_amount)
                )

                if with_tax_account:
                    itemised_tax[item_code][
                        tax.description
                    ].tax_account = tax.account_head

    return itemised_tax


def get_rounded_tax_amount(itemised_tax, precision):
    # Rounding based on tax_amount precision
    for taxes in itemised_tax.values():
        for tax_account in taxes:
            taxes[tax_account]["tax_amount"] = flt(
                taxes[tax_account]["tax_amount"], precision
            )


def remove_special_characters(text):
    return re.sub("[^A-Za-z0-9 ]+", "", text)


def remove_all_except_numbers(text=None):
    if not text:
        return ""
    return re.sub("[^0-9]+", "", text)
