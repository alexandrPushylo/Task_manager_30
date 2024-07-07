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
    const pathname = window.location;
    const [id, status] = e
    // console.log(id, status)
    const workDayStatus = $('.status_' + id);
    // console.log(workDayStatus)
    if (workDayStatus.is(':checked')) {
        workDayStatus.prop('checked', false);
    } else {
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

const toggleButtonStatus = (e, itemId) => {
    $.ajax({
        type: 'POST',
        mode: 'same-origin',
        url: window.location,
        data: {
            csrfmiddlewaretoken: $('input[name="csrfmiddlewaretoken"]').val(),
            item_id: itemId
        }
    })//.done((d) => {window.location.reload()})
}

function changeDriverForTechnic(e, techSheetId) {
    const e_name = e.name;
    $.ajax({
        type: 'POST',
        mode: 'same-origin',
        url: window.location,
        data: {
            csrfmiddlewaretoken: $('input[name="csrfmiddlewaretoken"]').val(),
            driver_sheet_id: $('select[name=' + e_name + ']').val(),
            technic_sheet_id: techSheetId
        }
    }).done((d) => {
        window.location.reload()
    })
}

function onInput_tech_description(e) {
    const atID = e.id.replace('app_tech_description_', '');
    $('#apply_' + atID).show();
    $('#reload_' + atID).show();
    $('#reject_' + atID).hide();
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
// $('#applications_container_saved').masonry({
// // указываем элемент-контейнер в котором расположены блоки для динамической верстки
//     itemSelector: '.application_items_saved',
//     // columnWidth: 200,
//     gutter: 20,
// // указываем класс элемента являющегося блоком в нашей сетке
//     singleMode: true,
// // true - если у вас все блоки одинаковой ширины
//     isResizable: true,
// // перестраивает блоки при изменении размеров окна
//     isAnimated: true,
// // анимируем перестроение блоков
//     animationOptions: {
//         queue: false,
//         duration: 500
//     }
// // опции анимации - очередь и продолжительность анимации
// });

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

function selectTechnicTitle(e) {
    const technic_title_id = e.id.replace('technic_title_', '')
    const technic_title = e.value;
    const application_technic_id = e.id.replace('technic_title_', '');
    const select_technic_sheet = $('.' + technic_title + '_' + application_technic_id);
    const technic_driver_selects = $('.technic_driver_selects_' + application_technic_id);
    const button_apply_app_tech = $('#apply_' + technic_title_id);
    const button_reload_app_tech = $('#reload_' + technic_title_id);
    const button_reject_app_tech = $('#reject_' + technic_title_id);

    technic_driver_selects.hide();
    select_technic_sheet.show();
    button_apply_app_tech.show();
    button_reload_app_tech.show();
    button_reject_app_tech.hide();
}

function changeTechnicSheetSelector(e) {
    const tech_sheet_id = e.id.replace('technic_sheet_', '')
    const button_apply_app_tech = $('#apply_' + tech_sheet_id);
    const button_reload_app_tech = $('#reload_' + tech_sheet_id);
    const button_reject_app_tech = $('#reject_' + tech_sheet_id);
    button_apply_app_tech.show();
    button_reload_app_tech.show();
    button_reject_app_tech.hide();
}

$('.technic_driver_selects > option[selected]').parent().show();


function reloadPage(e) {
    window.location.reload()
}

function selectAddTechnicDriver(e) {
    const technic_title = e.value;
    const select_technic_sheet = $('.' + technic_title);
    const technic_driver_selects = $('.technic_driver_selects_add');
    technic_driver_selects.hide();
    select_technic_sheet.show();
    const btn_added = $('#btn_add_technic_sheet');

    if (e.value === "none") {
        btn_added.hide()
    } else {
        btn_added.show()
    }
}

function addTechnicSheetToApp(e) {
    const operation = "add_technic_to_application";
    const select_add_tech_title = $('.select_add_tech_title > option:checked');
    const technic_driver_selects_add = $('.' + select_add_tech_title.val() + ' > option:checked');
    const app_technic_description = $('.app_technic_description');

    $.ajax({
        type: 'POST',
        mode: 'same-origin',
        url: window.location,
        data: {
            csrfmiddlewaretoken: $('input[name="csrfmiddlewaretoken"]').val(),
            app_today_id: $('input[name="application_id"]').val(),
            construction_site_id: $('input[name="construction_site_id"]').val(),
            technic_title_shrt: select_add_tech_title.val(),
            technic_sheet_id: technic_driver_selects_add.val(),
            app_tech_desc: app_technic_description.val(),
            operation: operation
        }
    }).done((d) => {
        window.location.reload()
    })

    $('.technic_driver_selects_add').hide()
    $('#btn_add_technic_sheet').hide()
    $('.select_add_tech_title').val('')
    app_technic_description.val('')
}

function deleteTechSheet(e) {
    const per = e.parentElement.parentElement
    per.remove()

}

function autoResize(elem) {
    elem.style.height = 'auto';
    elem.style.height = (elem.scrollHeight - 4) + 'px';
}

$('.button_reject_app_tech').click(function () {
    const operation = "reject_application_technic";
    const csrf = $('input[name="csrfmiddlewaretoken"]').val();
    const pathname = window.location;
    const applicationTechnicId = this.id.replace('reject_', '')
    $.ajax({
        type: 'POST',
        mode: 'same-origin',
        url: pathname,
        data: {
            csrfmiddlewaretoken: csrf,
            application_technic_id: applicationTechnicId,
            app_today_id: $('input[name="application_id"]').val(),
            construction_site_id: $('input[name="construction_site_id"]').val(),
            operation: operation
        }
    }).done((d) => {window.location.reload()})
})
// const toggleWorkdayStatus = (e) => {
//     const csrf = $('input[name="csrfmiddlewaretoken"]').val();
//     const pathname = window.location.pathname;
//     const [id, status] = e
//     // console.log(id, status)
//     const workDayStatus = $('.status_' + id);
//     // console.log(workDayStatus)
//     if (workDayStatus.is(':checked')) {
//         workDayStatus.prop('checked', false);
//     } else {
//         workDayStatus.prop('checked', true);
//     }
//     // console.log(workDayStatus.checked)
//
//     // $.ajax({
//     //         type: 'POST',
//     //         mode: 'same-origin',
//     //         url: pathname,
//     //         data: {
//     //             csrfmiddlewaretoken: csrf,
//     //             id_day: id,
//     //             status: status
//     //         }
//     //     }).done((d)=>{
//     //         console.log(d)
//     // })
//
// }

function applyChangesAppTechnic(e) {
    const operation = "apply_changes_application_technic";
    const appTechId = e.id.replace('apply_', '')
    const technic_title = $('#technic_title_' + appTechId + ' > option:checked').val();
    const technic_sheet_id = $('.' + technic_title + '_' + appTechId + ' > option:checked').val();
    const app_tech_description = $('#app_tech_description_' + appTechId).val();

    $.ajax({
        type: 'POST',
        mode: 'same-origin',
        url: window.location,
        data: {
            csrfmiddlewaretoken: $('input[name="csrfmiddlewaretoken"]').val(),
            app_today_id: $('input[name="application_id"]').val(),
            construction_site_id: $('input[name="construction_site_id"]').val(),
            application_technic_id: appTechId,
            technic_title_shrt: technic_title,
            technic_sheet_id: technic_sheet_id,
            app_tech_desc: app_tech_description,
            operation: operation
        }
    }).done((d) => {window.location.reload()})
}

function saveApplicationDescription(el) {
    const operation = "save_application_description";
    $.ajax({
        type: 'POST',
        mode: 'same-origin',
        url: window.location,
        data: {
            csrfmiddlewaretoken: $('input[name="csrfmiddlewaretoken"]').val(),
            // changed_desc_app: true,
            app_today_id: $('input[name="application_id"]').val(),
            construction_site_id: $('input[name="construction_site_id"]').val(),
            application_today_description: $('textarea[name="application_description"]').val(),
            operation: operation
        }
    })//.done((d) => {window.location.reload()})
}

function saveApplicationTechnic(el) {
    const app_today_id = $('input[name="application_id"]').val();
    const app_description = $('textarea[name="application_description"]').val();
    const app_material_description = $('.material_description').val();

    console.log(app_today_id)
    console.log(app_description)
    console.log(app_material_description)
}

function saveApplicationMaterials(el) {
    const operation = "save_application_materials";
    $.ajax({
        type: 'POST',
        mode: 'same-origin',
        url: window.location,
        data: {
            csrfmiddlewaretoken: $('input[name="csrfmiddlewaretoken"]').val(),
            app_today_id: $('input[name="application_id"]').val(),
            construction_site_id: $('input[name="construction_site_id"]').val(),
            app_material_id: $('input[name="app_material_id"]').val(),
            material_description: $('textarea[name="app_material_desc"]').val(),
            operation: operation
        }
    }).done((d) => {window.location.reload();})
}


// function myCalendar(){
//
//     const sd = jsCalendar.get('#calendar')
//
//     console.log(sd)
//
//     // sd.onDateClick(function(event, date){
//     //     // inputA.value = date.toString();
//     //     console.log(date)
//     // });
//
//
//
// }
// myCalendar();

$('.io_choice_day').change(function () {
    const current_day = this.value;
    // console.log(current_day)
    location.search = "?current_day=" + current_day
    // const dd = location.search;
    // console.log(dd)
})

$('#conflict_resolution_container').masonry({
// указываем элемент-контейнер в котором расположены блоки для динамической верстки
    itemSelector: '.conflict_resolution_items',
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

function selectTechnicTitleForConflictResolution(e) {
    const technic_title = e.value;
    const app_technic_id = e.id.replace('title_', '');
    const select_technic_sheet = $('.' + technic_title + '.at_' + app_technic_id);
    const technic_driver_CR = $('.technic_driver_CR' + '.at_' + app_technic_id);
    technic_driver_CR.hide();
    select_technic_sheet.show();
    $('.btn_reload_' + app_technic_id).show();
    $('.btn_apply_' + app_technic_id).show();
}

function selectTechnicSheetForConflictResolution(e) {
    const app_technic_id = e.id.replace('tech_sheet_', '');
    $('.btn_reload_' + app_technic_id).show();
    $('.btn_apply_' + app_technic_id).show();
}

$('.technic_driver_CR > option[selected]').parent().show();

function changePriorityForConflictResolution(e) {
    const appTechnicId = e.id.replace('priority_', '');
    const appTechnicPriority = e.value;
    $.ajax({
        type: 'POST',
        mode: 'same-origin',
        url: window.location,
        data: {
            csrfmiddlewaretoken: $('input[name="csrfmiddlewaretoken"]').val(),
            app_technic_id: appTechnicId,
            app_technic_priority: appTechnicPriority
        }
    }).done((d) => {
        window.location.reload()
    })
}

function applyChangesForConflictResolution(e) {
    const appTechnicId = e.id.replace('btn_apply_', '');
    const technic_title_short = $('#title_' + appTechnicId).val();
    const technic_sheet_id = $('.' + technic_title_short + '.at_' + appTechnicId).val();
    const technic_description = $('#app_tech_description_' + appTechnicId).val();
    // console.log(technic_title_short)
    // console.log(technic_sheet_id)
    // console.log(technic_description)
    $.ajax({
        type: 'POST',
        mode: 'same-origin',
        url: window.location,
        data: {
            csrfmiddlewaretoken: $('input[name="csrfmiddlewaretoken"]').val(),
            app_technic_id: appTechnicId,
            technic_title_short: technic_title_short,
            technic_sheet_id: technic_sheet_id,
            technic_description: technic_description
        }
    }).done((d) => {
        window.location.reload()
    })
}

function onInput_app_tech_description(e) {
    const app_technic_id = e.id.replace('app_tech_description_', '');
    $('.btn_reload_' + app_technic_id).show();
    $('.btn_apply_' + app_technic_id).show();
}

$('#technic_sheet_list').masonry({
// указываем элемент-контейнер в котором расположены блоки для динамической верстки
    itemSelector: '.technic_sheet_item',
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

function setViewProps(e) {
    const operation = "set_props_for_view";
    const is_show_saved_app = $('input[name="is_show_saved_app"]').is(':checked');
    const is_show_absent_app = $('input[name="is_show_absent_app"]').is(':checked');
    const is_show_technic_app = $('input[name="is_show_technic_app"]').is(':checked');
    const is_show_material_app = $('input[name="is_show_material_app"]').is(':checked');

    $.ajax({
        type: 'POST',
        mode: 'same-origin',
        url: window.location,
        data: {
            csrfmiddlewaretoken: $('input[name="csrfmiddlewaretoken"]').val(),
            is_show_saved_app: is_show_saved_app,
            is_show_absent_app: is_show_absent_app,
            is_show_technic_app: is_show_technic_app,
            is_show_material_app: is_show_material_app,
            operation: operation,
        }
    }).done((d) => {window.location.reload()})
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
        }
    }).done((d) => {window.location.reload()})
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
        }
    }).done((d) => {
        window.location.reload()
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
        }
    }).done((d) => {
        window.location.reload()
    })
}

function onChangeApplicationMaterialDescription(e) {
    const applicationMaterialId = e.id.replace('app_mat_desc_id_', '');
    const btn_submit = $('.btn_sub_' + applicationMaterialId);
    const text_area_desc = $('#app_mat_desc_id_' + applicationMaterialId);
    const lable_desc = $('.lbl_desc_' + applicationMaterialId);

    lable_desc.removeClass('text-success', 'text-danger')
    lable_desc.addClass('text-danger')
    lable_desc.text('Заявка не сохранена')

    text_area_desc.removeClass('border-success', 'border-danger')
    text_area_desc.addClass('border-danger')

    btn_submit.removeClass('btn-outline-primary', 'btn-outline-success')
    btn_submit.addClass('btn-warning')
    btn_submit.text('Сохранить')
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
        }
    }).done((d) => {
        window.location.reload()
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
        }
    }).done((d) => {
        window.location.reload()
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

        }
    }).done((d) => {
        window.location.reload()
    })
}

function setSpecTask(e, technicSheetId) {
    $.ajax({
        type: 'POST',
        mode: 'same-origin',
        url: window.location,
        data: {
            csrfmiddlewaretoken: $('input[name="csrfmiddlewaretoken"]').val(),
            technic_sheet_id: technicSheetId,
            operation: 'set_spec_task'
        }
    }).done((d) => {
        window.location.reload()
    })
}

function changeReadOnlyMode(readOnly) {
    console.log('dfs')
    $.ajax({
        type: 'POST',
        mode: 'same-origin',
        url: window.location,
        data: {
            csrfmiddlewaretoken: $('input[name="csrfmiddlewaretoken"]').val(),
            read_only: readOnly,
            operation: 'change_read_only_mode'
        }
    }).done((d) => {
        window.location.reload()
    })
}

// function validateApplicationToday(app_today_id, current_day) {
//     // console.log(app_today_id)
//     // console.log(current_day)
//     $.ajax({
//         type: 'POST',
//         mode: 'same-origin',
//         url: window.location,
//         data: {
//             csrfmiddlewaretoken: $('input[name="csrfmiddlewaretoken"]').val(),
//             app_today_id: app_today_id,
//             current_day: current_day,
//             operation: 'validate_application_today'
//         }
//     })
// }