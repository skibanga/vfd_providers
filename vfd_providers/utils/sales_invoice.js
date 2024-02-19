frappe.ui.form.on("Sales Invoice", {
  refresh: function (frm) {},
  generate_vfd: (frm) => {
    if (!frm.doc.vfd_cust_id) {
      frappe.msgprint({
        title: __("Confirmation Required"),
        message: __("Are you sure you want to send VFD without TIN"),
        primary_action: {
          label: "Proceed",
          action(values) {
            generate_vfd(frm);
          },
        },
      });
    } else if (frm.doc.vfd_cust_id && frm.doc.vfd_cust_id != frm.doc.tax_id) {
      frappe.msgprint({
        title: __("Confirmation Required"),
        message: __("TIN an VFD Customer ID mismatch"),
        primary_action: {
          label: "Proceed",
          action(values) {
            generate_vfd(frm);
          },
        },
      });
    } else {
      generate_vfd(frm);
    }
  },
});

function generate_vfd(frm) {
  frappe.dom.freeze(__("Generating VFD..."));
  frappe
    .call("vfd_providers.utils.utils.generate_tra_vfd", {
      docname: frm.doc.name,
    })
    .then((r) => {
      frappe.dom.unfreeze();
    })
    .fail((r) => {
      frappe.msgprint(__("Error generating VFD"));
      frappe.dom.unfreeze();
    });
}
