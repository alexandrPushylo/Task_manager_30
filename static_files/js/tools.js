function MESS_STATUS_OK(sec=1000){
    const mess_status_ok = $('#mess_status_ok');
    mess_status_ok.fadeToggle(sec);
    mess_status_ok.fadeToggle(sec);
}

function MESS_STATUS_FAIL(sec=1000){
    const mess_status_fail = $('#mess_status_fail');
    mess_status_fail.fadeToggle(sec);
    mess_status_fail.fadeToggle(sec);
}

function parseResponse(response){
    return JSON.parse(response)
}

function reloadPage() {
    window.location.reload()
}

function autoResize(elem) {
    elem.style.height = 'auto';
    elem.style.height = (elem.scrollHeight - 4) + 'px';
}