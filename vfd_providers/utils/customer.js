frappe.ui.form.on("Customer", {
    vfd_custidtype: function (frm) {
        if (frm.doc.vfd_custidtype == "1- TIN") {
            let tax_id = frm.doc.tax_id;
            let vfd_custid = tax_id.split('-').join('');
            frm.set_value("vfd_custid", vfd_custid)
        }
    },
    vfd_custid: function (frm) {
        // frappe.msgprint(string(frm.doc.vfd_custid.length))
        // frappe.msgprint(frm.doc.vfd_custidtype.startsWith('1'))
        if (frm.doc.tax_id.length != 9 && frm.doc.vfd_custidtype.startsWith('1')) {
            frappe.throw(__("TIN Number is should be 9 numbers only, Please remove the dashes"));
        }
    },
    tax_id: function (frm) {
        frm.fields_dict.tax_id.$input.focusout(function () {
            if (frm.doc.tax_id.length != 9) {
                frappe.throw(__("TIN Number is should be 9 numbers only, Please remove the dashes"));
            }
            if (frm.doc.tax_id) {
                let tax_id = frm.doc.tax_id;
                let vfd_custid = tax_id.split('-').join('');
                frm.set_value("vfd_custid", vfd_custid);
                frm.set_value("vfd_custidtype", "1- TIN");
            }
        });
    },
})