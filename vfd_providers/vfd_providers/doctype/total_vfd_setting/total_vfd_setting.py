# Copyright (c) 2023, Aakvatech Limited and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document
from time import sleep
import frappe, json, requests
from frappe import _
from frappe.utils import nowdate, nowtime, format_datetime


def post_fiscal_receipt(doc):
    """Post fiscal receipt to Total VFD
    Parameters
    ----------
    doc : object
    Python object which is expected to be from Sales Invoice doctype.

    Returns
    -------
    Nothing
    """
    total_vfd_setting = frappe.get_cached_doc("Total VFD Setting", doc.company)
    doc.vfd_date = doc.vfd_date or nowdate()
    doc.vfd_time = format_datetime(str(nowtime()), "HH:mm:ss")

    items = []
    tax_map = {"1": "A", "2": "B", "3": "C", "4": "D", "5": "E"}
    for item in doc.items:
        vat_rate_id = frappe.get_cached_value(
            "Item Tax Template", item.item_tax_template, "vfd_taxcode"
        )[:1]
        vat_group = tax_map[vat_rate_id]
        if vat_group == "A":
            if item.base_net_amount == item.base_amount:
                # both amounts are same if the price is exclusive of VAT
                price = item.base_net_amount * 1.18
            else:
                price = item.base_amount
        else:
            price = item.base_amount
        items.append(
            {
                "id": item.item_code,
                "name": item.item_name,
                "price": price,
                "qty": item.qty,
                "vatGroup": vat_group,
                "discount": 0.0,
            }
        )

    payload = {
        "serial": total_vfd_setting.serial_id,
        "customer": {
            "name": doc.customer_name,
            "idType": doc.vfd_cust_id_type or "6",
            "idValue": doc.vfd_cust_id or "NIL",
            "mobile": "",
        },
        "payments": [
            {
                "type": "INVOICE",
                "amount": doc.base_grand_total,
            }
        ],
        "items": items,
    }

    payload = json.dumps(payload)

    vfd_provider_posting_doc = frappe.new_doc("VFD Provider Posting")

    data = send_total_vfd_request(
        "sales",
        doc.company,
        payload,
        "POST",
        vfd_provider_posting_doc=vfd_provider_posting_doc,
    )

    doc.vfd_rctvnum = data["msg_data"].get("rctvnum")
    doc.vfd_date = data["msg_data"].get("localDate")
    doc.vfd_time = data["msg_data"].get("localTime")
    doc.vfd_status = "Success"
    doc.vfd_verification_url = data["msg_data"].get("verificationLink")
    doc.save()

    vfd_provider_posting_doc.sales_invoice = doc.name
    vfd_provider_posting_doc.rctnum = doc.vfd_rctvnum
    vfd_provider_posting_doc.date = doc.vfd_date
    vfd_provider_posting_doc.time = doc.vfd_time
    vfd_provider_posting_doc.ackmsg = data["msg_data"]
    vfd_provider_posting_doc.save()

    frappe.db.commit()
    return data


def send_total_vfd_request(
    call_type,
    company,
    payload=None,
    type="GET",
    total_vfd_setting=None,
    vfd_provider_posting_doc=None,
):
    """Send request to Total VFD API
    Parameters
    ----------
    call_type : str
    Type of call to make. e.g. "get_serial_info", "post_fiscal_receipt", "account_info", etc.
    company : str
    Company to get Total VFD settings from
    payload : dict
    Payload to send to Total VFD API
    type : str
    Type of request to make. e.g. "GET", "POST", "PUT", etc.
    total_vfd_setting : object
    Python object which is expected to be from Total VFD Setting doctype.
    vfd_provider_posting_doc : object
    Python object which is expected to be from VFD Provider Posting doctype.

    Returns
    -------
    data : dict
    Dictionary with response from Total VFD API
    """
    total_vfd = frappe.get_cached_doc("VFD Provider", "Total VFD")
    if not total_vfd:
        frappe.throw(_("Total VFD is not setup!"))
    if not total_vfd_setting:
        total_vfd_setting = frappe.get_cached_doc("Total VFD Setting", company)
    url = (
        total_vfd.base_url
        + frappe.get_list(
            "VFD Provider Attribute",
            filters={"parent": "Total VFD", "key": call_type},
            fields=["value"],
            ignore_permissions=True,
        )[0].value
    )
    headers = {
        "Authorization": "Bearer " + total_vfd_setting.bearer_token,
        "x-active-business": total_vfd_setting.x_active_business,
        "Content-Type": "application/json",
    }

    data = None
    for i in range(3):
        try:
            res = requests.request(
                method=type,
                url=url,
                data=payload if payload else None,
                headers=headers,
                timeout=500,
            )
            if res.ok:
                data = json.loads(res.text)
                frappe.log_error(
                    title="Send Request OK",
                    message=f"Send Request: {url} - Status Code: {res.status_code}\n{res.text}",
                )
            else:
                data = []
                frappe.log_error(
                    title="Send Request Error",
                    message=f"Send Request: {url} - Status Code: {res.status_code}\n{res.text}",
                )
                frappe.throw(f"Error is {res.text}")
            if vfd_provider_posting_doc:
                vfd_provider_posting_doc.req_headers = (
                    json.dumps(headers, ensure_ascii=False)
                    .replace("\\'", "'")
                    .replace('\\"', '"')
                )
                vfd_provider_posting_doc.req_data = (
                    json.dumps(payload, ensure_ascii=False)
                    .replace("\\'", "'")
                    .replace('\\"', '"')
                )
                vfd_provider_posting_doc.ackcode = data["status"]
                vfd_provider_posting_doc.ackmsg = (
                    str(data["msg_data"]).replace("\\'", "'").replace('\\"', '"')
                )

            break
        except Exception as e:
            sleep(3 * i + 1)
            if i != 2:
                continue
            else:
                frappe.log_error(
                    message=frappe.get_traceback(),
                    title=str(e)[:140] if e else "Send Total VFD Request Error",
                )
                frappe.throw(f"Connection failure is {res.text}")
                raise e
    return data
