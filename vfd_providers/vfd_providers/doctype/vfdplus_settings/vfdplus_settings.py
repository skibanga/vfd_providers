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


def send_vfdplus_request(call_type, company, payload=None, type="GET"):
    vfdplus = frappe.get_cached_doc("VFD Provider", "VFDPlus")
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
    return


def get_serial_info(doc, method):
    data = send_vfdplus_request(
        call_type="serial_info", company=doc.company, type="GET"
    )
    if data:
        doc.response = str(data["msg_data"])
        for key, value in data.items():
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
    # TODO
    data = send_vfdplus_request(call_type="account_info", company=company, type="GET")
    if data:
        return data
    else:
        frappe.throw(_(f"No data returned from VFDPlus for company: {company}"))
