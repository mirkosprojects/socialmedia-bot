function deleteContact(contact_id) {
    fetch("/delete-contact", {
        method: "POST",
        body: JSON.stringify({ contact_id: contact_id }),
    }).then((_res) => {
        window.location.href = "/settings";
    });
}
