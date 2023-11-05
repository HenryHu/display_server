function button_click(id) {
    let url = new URL("http://pureleaf:5000/button_click/" + id);

    let xhr = new XMLHttpRequest();
    xhr.open("POST", url);
    xhr.send()

    xhr.onload = function() {
        document.getElementById("status").textContent = "succ! status:" + xhr.status;
        location.reload();
    };
    xhr.onerror = function() {
        document.getElementById("status").textContent = "error!";
    };
}
