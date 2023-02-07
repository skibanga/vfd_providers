frappe.ui.form.on("Sales Invoice", {
    refresh: function (frm) {
    },
    generate_vfd: (frm) => {
        frappe.dom.freeze(__("Generating VFD..."));
        frappe.call("vfd_providers.utils.utils.generate_tra_vfd", {docname: frm.doc.name,})
            .then(r => {
                frappe.dom.unfreeze();
            })
            .fail(r => {
                frappe.dom.unfreeze();
            });
    }
})