// $(document).ready(() => {
    // $('#root_container').show();
///////////////////////////////////////////////////////////////////////////

///----------------------------------------------------------
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
///----------------------------------------------------------


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

    $('#div_btn_edit_control_' + technic_title_id).show();
    $('#btn_options_' + technic_title_id).hide();
    technic_driver_selects.hide();
    if (select_technic_sheet.children().length!==0){
        select_technic_sheet.show();
        $('#span_missing_driver_'+application_technic_id).hide();
    }else {
        $('#span_missing_driver_'+application_technic_id).show();
        $('#div_btn_edit_control_'+application_technic_id).hide();
    }

}

function changeTechnicSheetSelector(e) {
    const tech_sheet_id = e.id.replace('technic_sheet_', '')
    $('#div_btn_edit_control_' + tech_sheet_id).show();
    $('#btn_options_' + tech_sheet_id).hide();
}

$('.technic_driver_selects > option[selected]').parent().show();

function cancelAddedTechnic(e){
    const tech_sheet_id = e.id.replace('cancel_', '');
    const orig_technic_sheet_id = $('#orig_technic_sheet_'+tech_sheet_id).val();
    const orig_technic_desc = $('#orig_technic_description_'+tech_sheet_id).val();

    let orig_technic_title = $('#orig_technic_title_'+tech_sheet_id).val();
    orig_technic_title = orig_technic_title.replace(' ','').replace('.','');

    $('#technic_title_'+tech_sheet_id).val(orig_technic_title).change();
    $('.'+orig_technic_title+'_'+tech_sheet_id).val(orig_technic_sheet_id).change();
    $('#app_tech_description_'+tech_sheet_id).val(orig_technic_desc)

    $('#div_btn_edit_control_' + tech_sheet_id).hide();
    $('#btn_options_' + tech_sheet_id).show();
    $('#btn_edit_technics_and_materials').show();
    $('#main_footer').show();
}

function reloadPage() {
    window.location.reload()
}

function selectAddTechnicDriver(e) {
    const technic_title = e.value;
    const select_technic_sheet = $('.' + technic_title);
    const technic_driver_selects = $('.technic_driver_selects_add');
    technic_driver_selects.hide();
    $('#span_driver_name').show();
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
    const application_id = $('input[name="application_id"]');

    const app_tech_container = $('#app_tech_container');
    const app_tech_inst = $('#app_tech_inst');

    $.ajax({
        type: 'POST',
        mode: 'same-origin',
        url: window.location,
        data: {
            operation: operation,
            csrfmiddlewaretoken: $('input[name="csrfmiddlewaretoken"]').val(),

            app_today_id: application_id.val(),
            technic_title_shrt: select_add_tech_title.val(),
            technic_sheet_id: technic_driver_selects_add.val(),
            app_tech_desc: app_technic_description.val()

        },
        success: (response) => {
            let data = parseResponse(response)

            if (data.app_today_id){
                application_id.val(data.app_today_id)
            }
            if (data.status==='ok'){
                $('#modalApplicationTechnic').modal('hide');
                const APP = creatAppTechnicInst(data)
                app_tech_container.append(APP)
                MESS_STATUS_OK();
                $('#btn_apply_for_edit_app').text('СОХРАНИТЬ');
            }else {
                $('#modalApplicationTechnic').modal('hide');
                MESS_STATUS_FAIL();
            }
        }
    })

    $('.technic_driver_selects_add').hide()
    $('#btn_add_technic_sheet').hide()
    $('.select_add_tech_title').val('')
    app_technic_description.val('')
}

function autoResize(elem) {
    elem.style.height = 'auto';
    elem.style.height = (elem.scrollHeight - 4) + 'px';
}

function reject_or_accept_app_tech(appTechnicId){
    const operation = "reject_application_technic";
    const app_tech_description = $('#app_tech_description_'+appTechnicId);
    const csrf = $('input[name="csrfmiddlewaretoken"]').val();
    const pathname = window.location;
    $.ajax({
        type: 'POST',
        mode: 'same-origin',
        url: pathname,
        data: {
            csrfmiddlewaretoken: csrf,
            application_technic_id: appTechnicId,
            app_today_id: $('input[name="application_id"]').val(),
            construction_site_id: $('input[name="construction_site_id"]').val(),
            operation: operation
        },
        success: (response) => {
            if (response==='reject'){
                $('#technic_title_'+appTechnicId).prop('disabled', true);
                $('.technic_driver_selects_'+appTechnicId).prop('disabled', true);
                app_tech_description.prop('disabled', true);
                app_tech_description.addClass('border border-1 border-danger');
                MESS_STATUS_OK();
            }else if (response==='accept'){
                $('#technic_title_'+appTechnicId).prop('disabled', false);
                $('.technic_driver_selects_'+appTechnicId).prop('disabled', false);
                app_tech_description.prop('disabled', false);
                app_tech_description.removeClass('border border-1 border-danger');
                app_tech_description.val(app_tech_description.val().replace('ОТКЛОНЕНА\n',''));
                MESS_STATUS_OK();
            }
            else {
                MESS_STATUS_FAIL();
            }
        }
    })
}

$('.button_delete_app_tech').click(function () {
    const operation = "delete_application_technic";
    const csrf = $('input[name="csrfmiddlewaretoken"]').val();
    const pathname = window.location;
    const applicationTechnicId = this.id.replace('delete_', '')
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
        },
        success: (response) => {
            if (response==="success"){
                $('#'+applicationTechnicId).hide();
                $('#btn_apply_for_edit_app').text('СОХРАНИТЬ');
                MESS_STATUS_OK()
            }else {
                MESS_STATUS_FAIL()
            }
        }
    })
})

function applyChangesAppTechnic(app_technic_id) {
    const operation = "apply_changes_application_technic";
    const appTechId = app_technic_id// e.id.replace('apply_', '')
    const technic_title = $('#technic_title_' + appTechId +' > option:checked').val();
    const technic_sheet_id = $('.' + technic_title + '_' + appTechId + ' > option:checked').val();
    const app_tech_description = $('#app_tech_description_' + appTechId).val();
    const div_btn_edit_control = $('#div_btn_edit_control_'+appTechId);
    const btn_options = $('#btn_options_'+appTechId);
    const btn_edit_technics_and_materials = $('#btn_edit_technics_and_materials');

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
        },
        success: (response) => {
            if (response==='ok'){
                div_btn_edit_control.hide()
                btn_options.show()
                btn_edit_technics_and_materials.show()
                $('#main_footer').show();
                $('#btn_apply_for_edit_app').text('СОХРАНИТЬ');
                MESS_STATUS_OK()
            }else {
                div_btn_edit_control.hide()
                btn_options.show()
                btn_edit_technics_and_materials.show()
                $('#main_footer').show();
                MESS_STATUS_FAIL()
            }
        }
    })
}

function saveApplicationDescription(){
    const operation = "save_application_description";
    const orig_application_description = $('#orig_application_description');
    const application_today_description = $('textarea[name="application_description"]');
    const application_id = $('input[name="application_id"]');
    $.ajax({
        type: 'POST',
        mode: 'same-origin',
        url: window.location,
        data: {
            csrfmiddlewaretoken: $('input[name="csrfmiddlewaretoken"]').val(),
            app_today_id: application_id.val(),
            application_today_description: application_today_description.val(),
            operation: operation
        },
        success: (response) => {
            let data = parseResponse(response)
            if (data.app_today_id){
                application_id.val(data.app_today_id)
            }
            if(data.status === 'ok'){
                MESS_STATUS_OK()
                $('#div_btn_edit_application_description').hide();
                orig_application_description.val(application_today_description.val());
                $('#btn_apply_for_edit_app').text('СОХРАНИТЬ');
            } else {
                cancelEditedAppDescr()
                MESS_STATUS_FAIL()
            }
        }
    })
}

function cancelEditedAppDescr(){
    const orig_application_description_value = $('#orig_application_description').val();
    const application_description = $('textarea[name="application_description"]');
    application_description.val(orig_application_description_value);

    $('#div_btn_edit_application_description').hide();
}


function saveApplicationMaterials(el) {
    const operation = "save_application_materials";
    const add_materials_desc = $('#add_materials_desc');
    const app_material_desc = $('#app_material_desc');

    const application_id = $('input[name="application_id"]')
    const app_material_id = $('input[name="app_material_id"]')

    $.ajax({
        type: 'POST',
        mode: 'same-origin',
        url: window.location,
        data: {
            csrfmiddlewaretoken: $('input[name="csrfmiddlewaretoken"]').val(),
            app_today_id: application_id.val(),
            construction_site_id: $('input[name="construction_site_id"]').val(),
            app_material_id: app_material_id.val(),
            material_description: $('textarea[name="app_material_desc"]').val(),
            operation: operation
        },
        success: (response) => {
            let data = JSON.parse(response)
            if (data.app_today_id){
               application_id.val(data.app_today_id)
            }
            if (data.app_material_id){
               app_material_id.val(data.app_material_id)
            }

            if (data.status==='created'){
                $('#modalMaterials').modal('hide');
                $('#div_application_materials').show();
                app_material_desc.val(add_materials_desc.val());
                $('#btn_apply_for_edit_app').text('СОХРАНИТЬ');
                MESS_STATUS_OK()
            }else if(data.status==='updated') {
                $('#modalMaterials').modal('hide');
                $('#div_application_materials').show();
                app_material_desc.val(add_materials_desc.val());
                $('#btn_apply_for_edit_app').text('СОХРАНИТЬ');
                MESS_STATUS_OK()
            }else if (data.status==='deleted'){
                $('#modalMaterials').modal('hide');
                $('#div_application_materials').hide();
                add_materials_desc.val('')
                app_material_desc.val('')
                $('#btn_apply_for_edit_app').text('СОХРАНИТЬ');
                MESS_STATUS_OK()
            }else {
                MESS_STATUS_FAIL()
            }
        }
    })
}
function cancelAppMaterial(){
    const app_material_desc = $('#app_material_desc');
    const add_materials_desc = $('#add_materials_desc');
    $('#modalMaterials').modal('hide');
    if (app_material_desc.val()){
        add_materials_desc.val(app_material_desc.val())
    }else {
        add_materials_desc.val('')
    }
}


$('.io_choice_day').change(function () {
    const current_day = this.value;
    location.search = "?current_day=" + current_day
})


function selectTechnicTitleForConflictResolution(e) {
    const technic_title = e.value;
    const app_technic_id = e.id.replace('title_', '');
    const select_technic_sheet = $('.' + technic_title + '.at_' + app_technic_id);
    const technic_driver_CR = $('.technic_driver_CR' + '.at_' + app_technic_id);

    technic_driver_CR.hide();
    technic_driver_CR.attr('disabled', true);

    select_technic_sheet.show();
    select_technic_sheet.attr('disabled', false);

    $('.btn_reload_' + app_technic_id).show();
    $('.btn_apply_' + app_technic_id).show();
}

function selectTechnicSheetForConflictResolution(e) {
    const app_technic_id = e.id.replace('tech_sheet_', '');
    $('.btn_reload_' + app_technic_id).show();
    $('.btn_apply_' + app_technic_id).show();
}

const conflictTechnicDriver = $('.technic_driver_CR > option[selected]').parent();
conflictTechnicDriver.show();
conflictTechnicDriver.removeAttr('disabled');

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
        },
        success: (d) => {
            window.location.reload()
        }
    })
}

function applyChangesForConflictResolution(e) {
    const appTechnicId = e.id.replace('btn_apply_', '');
    const technic_title_short = $('#title_' + appTechnicId).val();
    const technic_sheet_id = $('.' + technic_title_short + '.at_' + appTechnicId).val();
    const technic_description = $('#app_tech_description_' + appTechnicId).val();

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
        },
        success: (d) => {
            window.location.reload()
        }
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


///////////////////////////////////////////////////////////////////////////////////
// })

function creatAppTechnicInst(data){
    const app_technic_id =data.app_technic_id
    const is_cancelled =data.is_cancelled
    const technic_title_shrt =data.technic_title_shrt
    const isChecked =data.isChecked
    const technic_title =data.technic_title
    const technic_sheet_id =data.technic_sheet_id
    const app_tech_desc =data.app_tech_desc
    const status =data.status
    let technic_driver_list = parseResponse(data.technic_driver_list)
    for (const i in technic_driver_list){
                technic_driver_list[i].technic_sheets = parseResponse(technic_driver_list[i].technic_sheets)
            }

    const app_tech_container = $('#app_tech_container');
    const div1 = $('<div id="'+app_technic_id+'" class="mt-2 card border border-2" style="box-shadow: 5px 5px 50px"/>');

    const div2 = $('<div class="row m-0 p-1 card-header" style="background: #e8ebfa"/>');
    const div3 = $('<div class="col"/>');

    const label4 = $('<label class="col-auto p-0"/>');

    const select5 = $('<select id="technic_title_'+app_technic_id+'" class="form-control p-1" />');

    select5.change(function (e){selectTechnicTitle(e.target)})

    for (const idx in technic_driver_list){
        //technic_driver_list[item].
        if (technic_title===technic_driver_list[idx].title){
            select5.append($('<option selected value="'+technic_driver_list[idx].title_short+'">'+technic_driver_list[idx].title+'</option>'))
        }else {
            select5.append($('<option value="'+technic_driver_list[idx].title_short+'">'+technic_driver_list[idx].title+'</option>'))
        }
    }
    label4.append(select5)

    const label6 = $('<label class="col-auto p-0"/>');
    for (const i in technic_driver_list){
        const select7 = $('<select id="technic_sheet_'+app_technic_id+'" class="'+technic_driver_list[i].title_short+'_'+app_technic_id+' technic_driver_selects000 technic_driver_selects_'+app_technic_id+' form-control p-1"/>');
        if (technic_title_shrt!==technic_driver_list[i].title_short){select7.hide()}
        select7.change(function (e){changeTechnicSheetSelector(e.target)})
        for (const j in technic_driver_list[i].technic_sheets){
            const item = technic_driver_list[i].technic_sheets[j]
            if (technic_sheet_id===item.id){
                select7.append($('<option selected value="'+item.id+'" >'+item.driver_sheet__driver__last_name+'</option>'));
            }else {
                select7.append($('<option value="'+item.id+'" >'+item.driver_sheet__driver__last_name+'</option>'));
            }
        }
        label6.append(select7);
    }
    div3.append(label4, label6)
    const div8 = $('<div class="col-auto" id="btn_options_'+app_technic_id+'"/>');
    const divIn1 = $('<div class="dropdown" style="margin-top: 0.1rem">')
    const buttonIn3 = $('<button class="btn btn-sm btn-outline-secondary dropdown-toggle" type="button" data-bs-toggle="dropdown" aria-expanded="false"><i class="fa-solid fa-ellipsis"></i></button>')
    const ul1 = $('<ul class="dropdown-menu dropdown-menu-end">')

    const li2 = $('<li/>')
    if (is_cancelled || isChecked){
        const buttonIn5 = $('<button type="button" class="dropdown-item fw-bolder text-success">Принять заявку</button>')
        buttonIn5.click(function (e){reject_or_accept_app_tech(app_technic_id)})
        li2.append(buttonIn5)
    }else {
        const buttonIn5 = $('<button type="button" class="dropdown-item fw-bolder text-primary">Отменить заявку</button>')
        buttonIn5.click(function (e){reject_or_accept_app_tech(app_technic_id)})
        li2.append(buttonIn5)
    }

    const li3 = $('<li/>').append($('<hr class=" dropdown-divider">'))
    const li4 = $('<li/>').append($('<button id="delete_'+app_technic_id+'" type="button" class="dropdown-item fw-bolder text-danger button_delete_app_tech">Удалить заявку</button>'))

    ul1.append(li2, li3, li4)
    divIn1.append(buttonIn3, ul1)
    div8.append(divIn1)
    div2.append(div3, div8)

    const div9 = $('<div/>');
    const input10 = $('<input type="hidden" id="orig_technic_title_'+app_technic_id+'" value="'+technic_title+'"/>');
    const input11 = $('<input type="hidden" id="orig_technic_sheet_'+app_technic_id+'" value="'+technic_sheet_id+'"/>');
    const input12 = $('<input type="hidden" id="orig_technic_description_'+app_technic_id+'" value="'+app_tech_desc+'"/>');
    div9.append(input10, input11, input12)

    const divDesc1 = $('<div class="row"/>')
    const labelDesc2 = $('<label/>')
    const textareaDesc3 = $('<textarea id="app_tech_description_'+app_technic_id+'" style="width: 100%;" class="form-control app_tech_description app_technic_description_'+app_technic_id+' general_tech_description_font">'+app_tech_desc+'</textarea>')
    textareaDesc3.on('input',function (e){onInput_tech_description(e.target); autoResize(e.target);})
    labelDesc2.append(textareaDesc3)
    divDesc1.append(labelDesc2)

    const div13 = $('<div class="m-1 p-1 row" id="div_btn_edit_control_'+app_technic_id+'" style="justify-content: space-between; display: none;"/>');
    const button14 = $('<button id="cancel_'+app_technic_id+'" type="button" class="btn btn-outline-primary button_reload_app_tech w-auto">Отмена</button>');
    button14.click(function (e){cancelAddedTechnic(e.target)})
    const button15 = $('<button id="apply_'+app_technic_id+'" type="button" class="btn btn-success button_apply_app_tech w-auto">Сохранить изменения</button>');
    button15.click(function (e){applyChangesAppTechnic(app_technic_id)})

    div13.append(button14, button15)
    div1.append(div2, div9, divDesc1, div13)
    return div1
}
