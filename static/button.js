function set_status(status) {
    document.getElementById("status").textContent = status;
}

function button_click(id) {
    set_status("button " + id + " clicked, sending request...");

    let url = new URL(location.origin + "/button_click/" + id);

    let xhr = new XMLHttpRequest();
    xhr.open("POST", url);
    xhr.send()

    xhr.onload = function() {
        set_status("succ! status:" + xhr.status);
        location.reload();
    };
    xhr.onerror = function() {
        set_status("error!");
    };
}
