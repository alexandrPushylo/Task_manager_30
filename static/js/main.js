// $(document).ready(() => {
//     alert('ok')
// })

const selectPost = (e) => {
    // console.log(e.value)
    // alert(e.value)
    const post = e.value
    const foreman_select = $('#foreman_select');
    const foreman_select_div = $('#foreman_select_div');
    if (post === 'master') {
        foreman_select_div.show()
        foreman_select.prop("disabled", false);
    } else {
        foreman_select_div.hide()
        foreman_select.prop("disabled", true);
    }
}

const toggleWorkdayStatus = (e) => {
    const csrf = $('input[name="csrfmiddlewaretoken"]').val();
    const pathname = window.location.pathname;
    const [id, status] = e
    // console.log(id, status)
    const workDayStatus = $('.status_' + id);
    // console.log(workDayStatus)
    if(workDayStatus.is(':checked')){
        workDayStatus.prop('checked', false);
    }else {
        workDayStatus.prop('checked', true);
    }
    // console.log(workDayStatus.checked)

    // $.ajax({
    //         type: 'POST',
    //         mode: 'same-origin',
    //         url: pathname,
    //         data: {
    //             csrfmiddlewaretoken: csrf,
    //             id_day: id,
    //             status: status
    //         }
    //     }).done((d)=>{
    //         console.log(d)
    // })

}

const toggleButtonStatus = (e) => {
    const button_save_div = $('.button_save_div')
    button_save_div.show()
}