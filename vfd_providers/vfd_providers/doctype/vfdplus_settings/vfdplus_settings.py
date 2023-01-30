# Copyright (c) 2023, Aakvatech Limited and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document
from time import sleep
import frappe, json, requests
from frappe import _


class VFDPlusSettings(Document):
    def validate(self):
        get_serial_info(self, method="validate")


# Below are the status codes returned by VFDPlus API
vfdplus_status_codes = {
    "4000": "VFDPLUS-API-KEY not found in header!",
    "4001": "Invalid VFDPLUS-API-KEY!",
    "4002": "VFDPLUS-API-KEY expired!",
    "4003": "VFDPLUS-API-KEY not enabled!",
    "4004": "VFDPLUS-API-KEY is deleted!",
    "4005": "VFDPLUS-API-KEY does not match any vfd-plus-account!",
    "4006": "VFDPLUS-API-KEY does not match any vfd-plus-serial/credential!",
    "4007": "Serial/Credential is not active!",
    "4008": "TRA Serial Supplied is not activated!",
    "4009": "Device Cannot generate receipt,Device is still off",
    "4010": "TRA Supplied serial is expired; Please contact Our Customer-Service Team for Renewal Process.",
    "4011": "VFDPlus Accpount Expired",
    "4012": "Invalid Receipt JSON Format,check missing fields,read all instructions supplied per each error line",
    "4013": "Only single receipt can be posted at a time",
    "4014": "Discount setting on device is not enabled",
    "4015": "Invoice/Receipt for a given serial is already posted",
    "2000": "Receipt Posted OK, OK Response",
}


def send_vfdplus_request(
    call_type, company, payload=None, type="GET", vfdplus_settings=None
):
    """Send request to VFDPlus API
    Parameters
    ----------
    call_type : str
    Type of call to make. e.g. "get_serial_info", "post_fiscal_receipt", "account_info", etc.
    company : str
    Company to get VFDPlus settings from
    payload : dict
    Payload to send to VFDPlus API
    type : str
    Type of request to make. e.g. "GET", "POST", "PUT", etc.

    Returns
    -------
    data : dict
    Dictionary with response from VFDPlus API
    """
    vfdplus = frappe.get_cached_doc("VFD Provider", "VFDPlus")
    if not vfdplus_settings:
        vfdplus_settings = frappe.get_cached_doc("VFDPlus Settings", company)
    url = (
        vfdplus.base_url
        + frappe.get_list(
            "VFD Provider Attribute",
            filters={"parent": "VFDPlus", "key": call_type},
            fields=["value"],
            ignore_permissions=True,
        )[0].value
    )
    headers = {
        "VFDPLUS-API-KEY": vfdplus_settings.vfdplus_api_key,
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
            if res.status_code == 200:
                data = json.loads(res.text)
                if data.get("msg_status") != "OK":
                    frappe.throw(
                        _(f"Error returned from VFDPlus: {data.get('msg_code')}")
                    )
            else:
                data = []
                frappe.log_error(
                    "Send Request",
                    f"Send Request: {url} - Status Code: {res.status_code}\n{res.text}",
                )
                frappe.throw(f"Error is {res.text}")
            break
        except Exception as e:
            sleep(3 * i + 1)
            if i != 2:
                continue
            else:
                frappe.log_error(frappe.get_traceback(), str(e))
                frappe.throw(f"Connection failure is {res.text}")
                raise e
    return data


def post_fiscal_receipt(doc):
    """Post fiscal receipt to VFDPlus
    Parameters
    ----------
    doc : object
    Python object which is expected to be from VFDPlus Settings doctype.

    Returns
    -------
    Nothing
    """
    vfdplus_settings = frappe.get_cached_doc("VFDPlus Settings", doc.company)

    cart_items = []
    for item in doc.items:
        # vat_rate_code, vat_rate_id = get_vat_rate_code(item.item_tax_template)
        vat_rate_code, vat_rate_id = ("A", 1)
        cart_items.append(
            {
                "vat_rate_code": vat_rate_code,
                "vat_rate_id": vat_rate_id,
                "item_name": item.item_code,
                "item_barcode": "-1",
                "item_qty": item.qty,
                "usp": item.base_net_rate,
                "sp": item.base_net_amount,
                "unit_discount_perc": 0.0,
                "unit_discount_amt": 0.0,
                "total_item_discount": 0.0,
            }
        )

    payload = {
        "credential_code": vfdplus_settings.company,
        "branch_id": "",
        "depart_id": "",
        "trans_no": doc.name,
        "idate": doc.vfd_date,
        "itime": doc.vfd_time,
        "customer_info": {
            "cust_name": doc.customer_name,
            "cust_id_type": doc.vfd_cust_id_type,
            "cust_id": doc.vfd_cust_id,
            "cust_phone": "",
            "cust_vrn": "",
            "cust_addr": "",
            "id_for": "",
        },
        "payment_methods": [
            {
                "pmt_type": "INVOICE",
                "pmt_amount": doc.base_rounded_total or doc.base_grand_total,
            }
        ],
        "cart_totals": {
            "item_counts": len(doc.items),
            "total_amount": doc.base_rounded_total or doc.base_grand_total,
            "total_amount_exclude_discount": doc.base_rounded_total
            or doc.base_grand_total,
            "discount": 0.0,
        },
        "cart_items": [
            {
                "vat_rate_code": "A",
                "vat_rate_id": 1,
                "item_name": "VITUMBUA",
                "item_barcode": "-1",
                "item_qty": 10.0,
                "usp": 1000.0,
                "sp": 1000.0,
                "unit_discount_perc": 0.0,
                "unit_discount_amt": 0.0,
                "total_item_discount": 0.0,
            }
        ],
        "user_info": {
            "user_id": "1",
            "username": doc.modified_by.split("@")[0],
            "till_id": "1",
        },
    }

    data = send_vfdplus_request("post_fiscal_receipt", doc.company, payload, "POST")

    doc.vfd_rctvnum = data.get("rctvnum")
    doc.vfd_verification_url = (
        f"https://virtual.tra.go.tz/efdmsRctVerify/{data.get('rctvnum')}_{doc.vfd_time}"
    )
    doc.save()
    frappe.db.commit()
    return


def get_serial_info(doc, method):
    """Get serial info from VFDPlus
    Parameters
    ----------
    doc : object
    Python object which is expected to be from VFDPlus Settings doctype.
    method : str
    Method name which is calling this function. e.g. validate, on_update, etc.

    Returns
    -------
    Nothing
    """
    data = send_vfdplus_request(
        call_type="serial_info", company=doc.company, type="GET", vfdplus_settings=doc
    )
    if data:
        doc.response = str(data["msg_data"])
        for key, value in data["msg_data"].items():
            try:
                setattr(doc, key, value)
            except Exception as e:
                frappe.log_error(
                    frappe.get_traceback(), "Error in set attribute for VFDPlus"
                )
                raise e
    if method != "validate":
        doc.save(ignore_permissions=True)


@frappe.whitelist()
def get_account_info(company):
    """Get serial info from VFDPlus
    Parameters
    ----------
    company : str
    String having Company name

    Returns
    -------
    data : dict
    Dictionary of account info
    """
    # TODO
    data = send_vfdplus_request(call_type="account_info", company=company, type="GET")
    if data:
        return data
    else:
        frappe.throw(_(f"No data returned from VFDPlus for company: {company}"))
