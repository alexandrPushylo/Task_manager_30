const selectPost = (e) => {
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

const toggleWorkdayStatus = (e, workday_id) => {
    const operation = "toggleWorkdayStatus";
    $.ajax({
        type: 'POST',
        mode: 'same-origin',
        url: window.location,
        data: {
            csrfmiddlewaretoken: $('input[name="csrfmiddlewaretoken"]').val(),
            workday_id: workday_id,
            operation: operation
        },
        success: (response) => {
            if (response==='ok'){
                MESS_STATUS_OK()
            }else {
                MESS_STATUS_FAIL()
            }
        }
    })
}

const toggleDriverSheetStatus = (e, itemId) => {
    const operation = "toggleDriverSheetStatus"
    $.ajax({
        type: 'POST',
        mode: 'same-origin',
        url: window.location,
        data: {
            csrfmiddlewaretoken: $('input[name="csrfmiddlewaretoken"]').val(),
            item_id: itemId,
            operation: operation
        },
        success: (response) => {
            const row = $('#driver_sheet_id__' + itemId)
            if (response === 'true') {
                row.css('color', '#018349')
                row.css('text-decoration-line', 'none')
                MESS_STATUS_OK()
            }
            if (response === 'false') {
                row.css('color', 'black')
                row.css('text-decoration-line', 'line-through')
                MESS_STATUS_OK()

            }
            if (response === 'none') {
                row.css('color', 'red')
                MESS_STATUS_FAIL()

            }
        }
    })
}

const toggleTechnicSheetStatus = (e, itemId) => {
    const operation = "toggleTechnicSheetStatus"
    $.ajax({
        type: 'POST',
        mode: 'same-origin',
        url: window.location,
        data: {
            csrfmiddlewaretoken: $('input[name="csrfmiddlewaretoken"]').val(),
            item_id: itemId,
            operation: operation
        },
        success: (response) => {
            const row = $('#technic_sheet_id__' + itemId)
            if (response === 'true') {
                row.css('background-color', '#effdf6')
                MESS_STATUS_OK()
            }
            if (response === 'false') {
                row.css('background-color', '#fdefef')
                MESS_STATUS_OK()
            }
            if (response === 'none') {
                row.css('color', 'red')
                MESS_STATUS_FAIL()
            }
        }
    })
}

function changeDriverForTechnic(e, techSheetId) {
    const operation = "changeDriverForTechnic"
    const e_name = e.name;
    const selectName = $('select[name=' + e_name + ']')
    $.ajax({
        type: 'POST',
        mode: 'same-origin',
        url: window.location,
        data: {
            csrfmiddlewaretoken: $('input[name="csrfmiddlewaretoken"]').val(),
            driver_sheet_id: selectName.val(),
            technic_sheet_id: techSheetId,
            operation: operation
        },
        success: (response) => {
            if (response === 'true') {
                selectName.css('border', 'none')
                MESS_STATUS_OK()
            }
            if (response === 'false') {
                selectName.css('border', 'red 1px solid')
                MESS_STATUS_OK()

            }
            if (response === 'none') {
                selectName.css('border', 'none')

            }
        }
    })
}

function onInput_tech_description(e) {
    const atID = e.id.replace('app_tech_description_', '');
    $('#div_btn_edit_control_' + atID).show();
    $('#btn_options_' + atID).show();
    $('#btn_edit_technics_and_materials').hide();
    $('#main_footer').hide();
}

$('.app_tech_description').each(function () {
    this.style.height = "" + (this.scrollHeight) + "px";
});
$('.material_description').each(function () {
    this.style.height = "" + (this.scrollHeight) + "px";
});

$('.text_area_description').each(function () {
    this.style.height = "" + (this.scrollHeight) + "px";
});

$('#applications_container').masonry({
// указываем элемент-контейнер в котором расположены блоки для динамической верстки
    itemSelector: '.application_items',
    // columnWidth: 50,
    gutter: 20,
    fitWidth: true,
    horizontalOrder: false,
// указываем класс элемента являющегося блоком в нашей сетке
    singleMode: true,
// true - если у вас все блоки одинаковой ширины
    isResizable: true,
// перестраивает блоки при изменении размеров окна
    isAnimated: true,
// анимируем перестроение блоков
    animationOptions: {
        queue: false,
        duration: 500
    }
// опции анимации - очередь и продолжительность анимации
});

$('#technic_sheet_list').masonry({
// указываем элемент-контейнер в котором расположены блоки для динамической верстки
    itemSelector: '.technic_sheet_item',
    // columnWidth: 50,
    gutter: 20,
    fitWidth: true,
    horizontalOrder: false,
// указываем класс элемента являющегося блоком в нашей сетке
    singleMode: true,
// true - если у вас все блоки одинаковой ширины
    isResizable: true,
// перестраивает блоки при изменении размеров окна
    isAnimated: true,
// анимируем перестроение блоков
    animationOptions: {
        queue: false,
        duration: 500
    }
// опции анимации - очередь и продолжительность анимации
});

$('#construction_site_container').masonry({
// указываем элемент-контейнер в котором расположены блоки для динамической верстки
    itemSelector: '.construction_site_items',
    // columnWidth: 200,
// указываем класс элемента являющегося блоком в нашей сетке
    singleMode: true,
// true - если у вас все блоки одинаковой ширины
    isResizable: true,
// перестраивает блоки при изменении размеров окна
    isAnimated: true,
// анимируем перестроение блоков
    animationOptions: {
        queue: false,
        duration: 500
    }
// опции анимации - очередь и продолжительность анимации
});


$('.io_choice_day').change(function () {
    const current_day = this.value;
    location.search = "?current_day=" + current_day
})


function changeViewProps(io){
    const operation = "change_props_for_view";
    const io_name = io.name;
    const io_isChecked = io.checked;
    const io_value = io.value;
    $.ajax({
        type: 'POST',
        mode: 'same-origin',
        url: window.location,
        data: {
            csrfmiddlewaretoken: $('input[name="csrfmiddlewaretoken"]').val(),
            io_name: io_name,
            io_isChecked: io_isChecked,
            io_value: io_value,
            operation: operation,
        },
        success: (response) => {}
    })
}

function setFilterProps(e) {
    const operation = "set_props_for_filter";
    $.ajax({
        type: 'POST',
        mode: 'same-origin',
        url: window.location,
        data: {
            csrfmiddlewaretoken: $('input[name="csrfmiddlewaretoken"]').val(),
            filter_construction_site: $('select[name="filter_construction_site"]').val(),
            filter_foreman: $('select[name="filter_foreman"]').val(),
            filter_technic: $('select[name="filter_technic"]').val(),
            sort_by: $('select[name="sort_by"]').val(),
            operation: operation
        },
        success: (d) => {
            window.location.reload()
        }
    })
}

function changeIsCancelled(e) {
    const applicationTechnicId = e.id.replace('reject_', '');
    $.ajax({
        type: 'POST',
        mode: 'same-origin',
        url: window.location,
        data: {
            csrfmiddlewaretoken: $('input[name="csrfmiddlewaretoken"]').val(),
            applicationTechnicId: applicationTechnicId,
            operation: 'reject'
        },
        success: (d) => {
            window.location.reload()
        }
    })
}

function changeIsChecked(e, appTodayId) {
    const applicationTechnicId = e.id.replace('accept_', '');
    $.ajax({
        type: 'POST',
        mode: 'same-origin',
        url: window.location,
        data: {
            csrfmiddlewaretoken: $('input[name="csrfmiddlewaretoken"]').val(),
            applicationTechnicId: applicationTechnicId,
            application_today_id: appTodayId,
            operation: 'accept'
        },
        success: (d) => {
            window.location.reload()
        }
    })
}

function onChangeApplicationMaterialDescription(e) {
    const applicationMaterialId = e.id.replace('app_mat_desc_id_', '');
    const btn_submit = $('.btn_sub_' + applicationMaterialId);
    const text_area_desc = $('#app_mat_desc_id_' + applicationMaterialId);
    const label_desc = $('.lbl_desc_' + applicationMaterialId);

    label_desc.removeClass('text-success', 'text-danger')
    label_desc.addClass('text-danger')
    label_desc.text('Заявка не сохранена')

    text_area_desc.removeClass('border-success', 'border-danger')
    text_area_desc.addClass('border-danger')

    btn_submit.removeClass('btn-outline-primary', 'btn-outline-success')
    btn_submit.addClass('btn-warning')
    btn_submit.text('Сохранить')
}

function acceptApplicationMaterial(application_material_id) {
    const operation = 'accept_application_material'
    const app_material_description = $('#app_mat_desc_id_' + application_material_id).val()
    $.ajax({
        type: 'POST',
        mode: 'same-origin',
        url: window.location,
        data: {
            csrfmiddlewaretoken: $('input[name="csrfmiddlewaretoken"]').val(),
            operation: operation,
            application_material_id: application_material_id,
            app_material_description: app_material_description
        },
        success: (response) => {
            if (response === 'true') {
                toggleStatusApplicationMaterial(application_material_id, 'accept')
            }
            if (response === 'false') {
                toggleStatusApplicationMaterial(application_material_id, 'reject')
            }
        },
    })
}

function toggleStatusApplicationMaterial(application_material_id, status) {
    const button_submit = $('.btn_sub_' + application_material_id);
    const label_description = $('.lbl_desc_' + application_material_id);
    const textarea_description = $('#app_mat_desc_id_' + application_material_id);

    if (status === 'accept') {
        button_submit.removeClass('btn-primary')
        button_submit.removeClass('btn-warning')
        button_submit.addClass('btn-outline-success')
        button_submit.text('Отменить заявку на:')

        label_description.text('Заявка подтверждена')
        label_description.removeClass('text-danger')
        label_description.addClass('text-success')

        textarea_description.removeClass('border-danger')
        textarea_description.addClass('border-success')
    }
    if (status === 'reject') {
        button_submit.removeClass('btn-outline-success')
        button_submit.addClass('btn-primary')
        button_submit.text('Подтвердить заявку на:')

        label_description.text('Заявка не подтверждена')
        label_description.removeClass('text-success')
        label_description.addClass('text-danger')

        textarea_description.removeClass('border-success')
        textarea_description.addClass('border-danger')
    }
}

function open_print_page(e) {
    const location = window.location
    window.open(location + e)
}

function toggleHidePanel(e) {
    $.ajax({
        type: 'POST',
        mode: 'same-origin',
        url: window.location,
        data: {
            csrfmiddlewaretoken: $('input[name="csrfmiddlewaretoken"]').val(),
            operation: 'toggle_panel'
        },
        success: (d) => {
            $('#spec_panel').toggle();
            const app_container = $('#applications_container')
            if (app_container.attr('class').includes('mx-auto')) {
                app_container.removeClass('mx-auto');
            } else {
                app_container.addClass('mx-auto');
            }
        }
    })
}

function connectTelegramBot(e, userKey) {
    console.log(userKey)
    $.ajax({
        type: 'POST',
        mode: 'same-origin',
        url: window.location,
        data: {
            csrfmiddlewaretoken: $('input[name="csrfmiddlewaretoken"]').val(),
            user_key: userKey
        },
        success: (d) => {
            window.location.reload()
        }
    })
}

function copyApplicationTo(e) {
    $.ajax({
        type: 'POST',
        mode: 'same-origin',
        url: window.location,
        data: {
            csrfmiddlewaretoken: $('input[name="csrfmiddlewaretoken"]').val(),
            target_day: $('input[name="copy_modal_target_day"]').val(),
            application_id: $('select[name="copy_modal_application_id"]').val(),
            operation: 'copy'
        },
        success: (d) => {
            window.location.reload()
        }
    })
}

function setSpecTask(e, technicSheetId) {
    const operation = "set_spec_task";
    $.ajax({
        type: 'POST',
        mode: 'same-origin',
        url: window.location,
        data: {
            csrfmiddlewaretoken: $('input[name="csrfmiddlewaretoken"]').val(),
            technic_sheet_id: technicSheetId,
            operation: operation
        },
        success: (d) => {
            window.location.reload()
        }
    })
}

function changeReadOnlyMode(readOnly) {
    $.ajax({
        type: 'POST',
        mode: 'same-origin',
        url: window.location,
        data: {
            csrfmiddlewaretoken: $('input[name="csrfmiddlewaretoken"]').val(),
            read_only: readOnly,
            operation: 'change_read_only_mode'
        },
        success: (d) => {
            window.location.reload()
        }
    })
}

function prepareModalDeleteApplication(url) {
    $('#btn_delete_app').attr('href', url);
}

function setTaskDescription(technic_id) {
    const operation = "set_task_description";

    let task_mode;
    let manual_description;

    if ($('#auto_mode_' + technic_id).is(':checked')) {
        task_mode = 'auto';
    } else if ($('#default_mode_' + technic_id).is(':checked')) {
        task_mode = 'default';
    } else if ($('#manual_mode_' + technic_id).is(':checked')) {
        task_mode = 'manual';
        manual_description = $('#io_manual_mode_' + technic_id).val();
    }
    $.ajax({
        type: 'POST',
        mode: 'same-origin',
        url: window.location,
        data: {
            csrfmiddlewaretoken: $('input[name="csrfmiddlewaretoken"]').val(),
            operation: operation,
            technic_id: technic_id,
            task_mode: task_mode,
            manual_description: manual_description
        },
        success: (d) => {
            $('#btn_technic_id_' + technic_id).hide();
        }
    })
}

function checkPassword(){
    const new_password_0 = $('#new_password_0');
    const new_password_1 = $('#new_password_1');
    const span_password_error = $('#span_password_error');
    const btn_change_password = $('#btn_change_password');

    if(new_password_0.val() !== new_password_1.val()){
        span_password_error.show();
        new_password_0.addClass('border border-danger');
        new_password_1.addClass('border border-danger');
        btn_change_password.addClass('disabled');
    }
    else {
        span_password_error.hide();
        new_password_0.removeClass('border border-danger')
        new_password_1.removeClass('border border-danger')
        btn_change_password.removeClass('disabled');
    }
}

function changePassword() {
    const operation = "changePassword";
    $.ajax({
        type: 'POST',
        mode: 'same-origin',
        url: window.location,
        data: {
            csrfmiddlewaretoken: $('input[name="csrfmiddlewaretoken"]').val(),
            operation: operation,
            new_password_0: $('input[name="new_password_0"]').val(),
            new_password_1: $('input[name="new_password_1"]').val(),
        },
        success: (response) => {
            if (response==='accept'){
                alert('Пароль успешно изменен');
                reloadPage();
                // $('#p_status_accept').show()
                // $('#p_status_error').hide()
            }
            else {
                // $('#p_status_accept').hide()
                // $('#p_status_error').show()
                alert('Произошла ошибка');
                reloadPage();
            }
        }
    })
}

