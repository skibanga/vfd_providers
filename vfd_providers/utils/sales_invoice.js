frappe.ui.form.on("Sales Invoice", {
  refresh: function (frm) {},
  generate_vfd: (frm) => {
    if (!frm.doc.vfd_custid) {
      frappe.msgprint({
        title: __("Confirmation Required"),
        message: __("Are you sure you want to send VFD without TIN"),
        primary_action: {
          label: "Proceed",
          action(values) {
            _generate_vfd(frm);
            cur_dialog.cancel();
          },
        },
      });
    } else if (frm.doc.vfd_custid && frm.doc.vfd_custid != frm.doc.tax_id) {
      frappe.msgprint({
        title: __("Confirmation Required"),
        message: __("TIN an VFD Customer ID mismatch"),
        primary_action: {
          label: "Proceed",
          action(values) {
            _generate_vfd(frm);
            cur_dialog.cancel();
          },
        },
      });
    } else {
      _generate_vfd(frm);
    }
  },
});

function _generate_vfd(frm) {
  frappe.dom.freeze(__("Generating VFD..."));
  frappe
    .call("vfd_providers.utils.utils.generate_tra_vfd", {
      docname: frm.doc.name,
    })
    .then((r) => {
      frappe.dom.unfreeze();
      frm.reload_doc();
      frappe.show_alert({
        message: __("VFD Generated"),
        indicator: "green",
      });
    })
    .fail((r) => {
      frappe.msgprint(__("Error generating VFD"));
      frappe.dom.unfreeze();
    });
}
