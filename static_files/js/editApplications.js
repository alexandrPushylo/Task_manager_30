$('.technic_driver_selects > option[selected]').parent().show();

function selectTechnicTitle(e) {
    const technic_title_id = e.id.replace('technic_title_', '')
    const technic_title = e.value;
    const application_technic_id = e.id.replace('technic_title_', '');
    const select_technic_sheet = $('.' + technic_title + '_' + application_technic_id);
    const technic_driver_selects = $('.technic_driver_selects_' + application_technic_id);

    technic_driver_selects.hide();
    if (select_technic_sheet.children().length!==0){
        select_technic_sheet.show();
        $('#span_missing_driver_'+application_technic_id).hide();
        applyChangesAppTechnic(technic_title_id)
    }else {
        $('#span_missing_driver_'+application_technic_id).show();
    }
}


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

function selectAddTechnicDriver(e) {
    const technic_title = e.value;
    const select_technic_sheet = $('.' + technic_title);
    const technic_driver_selects = $('.technic_driver_selects_add');
    technic_driver_selects.hide();
    $('#span_driver_name').show();
    select_technic_sheet.show();
    const btn_add_tech = $('#btn_add_tech');

    if (select_technic_sheet.children().length===2) {
        select_technic_sheet.children().last().prop('selected', true)
    }
    if (e.value === "none") {
        btn_add_tech.attr('disabled', true);
    } else {
        btn_add_tech.attr('disabled', false);
    }
}

function addTechnicSheetToApp(e) {
    const operation = "add_technic_to_application";
    const select_add_tech_title = $('.select_add_tech_title > option:checked');
    const select_add_tech_driver = $('.' + select_add_tech_title.val());
    const technic_driver_selects_add = $('.' + select_add_tech_title.val() + ' > option:checked');
    const app_technic_description = $('.app_technic_description');
    const application_id = $('input[name="application_id"]');

    const app_tech_container = $('#app_tech_container');

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
    select_add_tech_driver.val('')
}

function reject_or_accept_app_tech(appTechnicId){
    const operation = "reject_application_technic";
    const app_tech_description = $('#app_tech_description_'+appTechnicId);
    const csrf = $('input[name="csrfmiddlewaretoken"]').val();
    const pathname = window.location;

    const btn_accept = $('#accept_'+appTechnicId);
    const btn_reject = $('#reject_'+appTechnicId);

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
                btn_accept.show();
                btn_reject.hide();
                $('#technic_title_'+appTechnicId).prop('disabled', true);
                $('.technic_driver_selects_'+appTechnicId).prop('disabled', true);
                app_tech_description.prop('disabled', true);
                app_tech_description.addClass('border border-1 border-danger');
                MESS_STATUS_OK();
                $('#btn_apply_for_edit_app').text('СОХРАНИТЬ');
            }else if (response==='accept'){
                btn_accept.hide();
                btn_reject.show();
                $('#technic_title_'+appTechnicId).prop('disabled', false);
                $('.technic_driver_selects_'+appTechnicId).prop('disabled', false);
                app_tech_description.prop('disabled', false);
                app_tech_description.css('border', 'none');
                app_tech_description.removeClass('border border-1 border-danger');
                app_tech_description.val(app_tech_description.val().replace('ОТКЛОНЕНА\n',''));
                MESS_STATUS_OK();
                $('#btn_apply_for_edit_app').text('СОХРАНИТЬ');
            }
            else {
                MESS_STATUS_FAIL();
            }
        }
    })
}

function deleteAppTechnic(appTechnicId){
    const operation = "delete_application_technic";
    const csrf = $('input[name="csrfmiddlewaretoken"]').val();
    const pathname = window.location;
    const applicationTechnicId = appTechnicId
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
}

function blurAppTechnic(app_technic_id){
    const orig_technic_description = $('#orig_technic_description_'+app_technic_id);
    const app_tech_description = $('#app_tech_description_'+app_technic_id);

    if (orig_technic_description.val() !== app_tech_description.val()){
        applyChangesAppTechnic(app_technic_id)
    }

    $('#btn_edit_technics_and_materials').show();
    $('#main_footer').show();
}

function applyChangesAppTechnic(app_technic_id) {
    const operation = "apply_changes_application_technic";
    const appTechId = app_technic_id// e.id.replace('apply_', '')
    const orig_technic_description = $('#orig_technic_description_'+app_technic_id);

    const technic_title = $('#technic_title_' + appTechId +' > option:checked').val();
    const technic_sheet_id = $('.' + technic_title + '_' + appTechId + ' > option:checked').val();
    const app_tech_description = $('#app_tech_description_' + appTechId);
    const btn_options = $('#btn_options_'+appTechId);
    const btn_edit_technics_and_materials = $('#btn_edit_technics_and_materials');
    const span_notwork_driver = $('#span_notwork_driver_'+app_technic_id);

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
            app_tech_desc: app_tech_description.val(),
            operation: operation
        },
        success: (response) => {
            let data = parseResponse(response)
            if (data.status==='ok'){
                orig_technic_description.val(app_tech_description.val())
                btn_options.show()
                btn_edit_technics_and_materials.show()
                $('#main_footer').show();
                $('#btn_apply_for_edit_app').text('СОХРАНИТЬ');
                MESS_STATUS_OK()
            }else {
                btn_options.show()
                btn_edit_technics_and_materials.show()
                $('#main_footer').show();
                MESS_STATUS_FAIL()
            }
            if (data.driver_status==='true'){
                span_notwork_driver.hide();
            }else {
                span_notwork_driver.show();
            }
        }
    })
}

function createApplicationDescription(){
    const btn_div_application_desc = $('#btn_div_application_desc');
    const div_application_desc = $('#div_application_desc');

    btn_div_application_desc.hide();
    div_application_desc.show();
    $('#textarea_application_description').focus();
}

function blurApplicationDescription(){
    const btn_div_application_desc = $('#btn_div_application_desc');
    const div_application_desc = $('#div_application_desc');
    const textarea_application_description = $('#textarea_application_description');
    const orig_application_description = $('#orig_application_description');

    if (textarea_application_description.val() !== orig_application_description.val()){
    }else if (orig_application_description.val()){
        textarea_application_description.val(orig_application_description.val())
        $('#div_btn_edit_application_description').hide();

    }else {
        btn_div_application_desc.show();
        div_application_desc.hide();
        $('#div_btn_edit_application_description').hide();
    }
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
                const app_description = data.app_description
                MESS_STATUS_OK()
                $('#div_btn_edit_application_description').hide();
                orig_application_description.val(app_description);
                application_today_description.val(app_description);
                if (app_description){
                    $('#btn_div_application_desc').hide();
                    $('#div_application_desc').show();
                }else {
                    $('#btn_div_application_desc').show();
                    $('#div_application_desc').hide();
                }
                $('#btn_apply_for_edit_app').text('СОХРАНИТЬ');
            } else {
                cancelEditedAppDescr()
                MESS_STATUS_FAIL()
            }
        }
    })
}

function cancelEditedAppDescr(){
    const orig_application_description = $('#orig_application_description');
    const application_description = $('textarea[name="application_description"]');
    application_description.val(orig_application_description.val());
    application_description.css('height', 'auto');
    if (application_description.val()){

    }else {
        $('#btn_div_application_desc').show();
        $('#div_application_desc').hide();
    }
    $('#div_btn_edit_application_description').hide();
}

function saveApplicationMaterials(el) {
    const operation = "save_application_materials";
    const application_id = $('input[name="application_id"]')
    const app_material_id = $('input[name="app_material_id"]')

    const orig_material_description = $('#orig_material_description');
    const app_material_desc = $('#app_material_desc');

    const btn_create_app_mater = $('#btn_create_app_mater')

    if (orig_material_description.val() || app_material_desc.val()){
        $.ajax({
        type: 'POST',
        mode: 'same-origin',
        url: window.location,
        data: {
            csrfmiddlewaretoken: $('input[name="csrfmiddlewaretoken"]').val(),
            app_today_id: application_id.val(),
            construction_site_id: $('input[name="construction_site_id"]').val(),
            app_material_id: app_material_id.val(),
            material_description: app_material_desc.val(),
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
                $('#div_application_materials').show();
                orig_material_description.val(app_material_desc.val());
                $('#btn_apply_for_edit_app').text('СОХРАНИТЬ');
                MESS_STATUS_OK()
            }else if(data.status==='updated') {
                $('#div_application_materials').show();
                orig_material_description.val(app_material_desc.val());
                $('#btn_apply_for_edit_app').text('СОХРАНИТЬ');
                MESS_STATUS_OK()
            }else if (data.status==='deleted'){
                $('#div_application_materials').hide();
                orig_material_description.val('')
                app_material_desc.val('')
                $('#btn_apply_for_edit_app').text('СОХРАНИТЬ');
                MESS_STATUS_OK()
            }else {
                MESS_STATUS_FAIL()
            }
            $('#div_btn_edit_material').hide();
            $('#btn_edit_technics_and_materials').show();
            $('#main_footer').show();
        }
    })
    }else {
        $('#div_application_materials').hide();
        $('#div_btn_edit_material').hide();
        $('#btn_edit_technics_and_materials').show();
        $('#main_footer').show();
    }
}

function createAppMater(){
    $('#div_application_materials').show();
    $('#app_material_desc').focus();
    $('#btn_edit_technics_and_materials').hide();
    $('#main_footer').hide();
}

function blurAppMaterial(){
    // $('#btn_create_app_mater').hide();
    $('#btn_edit_technics_and_materials').show();
    $('#main_footer').show();
}

function onInput_material_description() {
    $('#div_btn_edit_material').show();
    $('#btn_edit_technics_and_materials').hide();
    $('#main_footer').hide();
}

function cancelAddedMaterial(){
    const app_material_desc = $('#app_material_desc');

    const orig_material_description = $('#orig_material_description');
    if (orig_material_description.val()){
        app_material_desc.val(orig_material_description.val())
    }else {
        app_material_desc.val('')
        $('#div_application_materials').hide()
    }
    app_material_desc.css('height', 'auto');
    $('#div_btn_edit_material').hide();

    $('#btn_edit_technics_and_materials').show();
    $('#main_footer').show();
}

function creatAppTechnicInst(data){
    const app_technic_id = data.app_technic_id
    const is_cancelled = data.is_cancelled
    const technic_title_shrt = data.technic_title_shrt
    const isChecked = data.isChecked
    const technic_title = data.technic_title
    const technic_sheet_id = data.technic_sheet_id
    const app_tech_desc = data.app_tech_desc
    const status = data.status
    const font_size = data.font_size
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
        select7.change(function (e){applyChangesAppTechnic(app_technic_id)})
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

    if (!is_cancelled || isChecked){
        const buttonIn5 = $('<button id="accept_' + app_technic_id + '" type="button" style="display: none" class="dropdown-item fw-bolder text-success">Принять заявку</button>')
        buttonIn5.click(function (e) {
            reject_or_accept_app_tech(app_technic_id)
        })
        const buttonIn6 = $('<button id="reject_' + app_technic_id + '" type="button" class="dropdown-item fw-bolder text-primary">Отменить заявку</button>')
        buttonIn6.click(function (e) {
            reject_or_accept_app_tech(app_technic_id)
        })

        li2.append(buttonIn5, buttonIn6)
    }else if (is_cancelled){
        const buttonIn5 = $('<button id="accept_' + app_technic_id + '" type="button" class="dropdown-item fw-bolder text-success">Принять заявку</button>')
        buttonIn5.click(function (e) {
            reject_or_accept_app_tech(app_technic_id)
        })
        const buttonIn6 = $('<button id="reject_' + app_technic_id + '" type="button" style="display: none" class="dropdown-item fw-bolder text-primary">Отменить заявку</button>')
        buttonIn6.click(function (e) {
            reject_or_accept_app_tech(app_technic_id)
        })

        li2.append(buttonIn5, buttonIn6)
    }

    const li3 = $('<li/>').append($('<hr class=" dropdown-divider">'))
    const button_del = $('<button id="delete_'+app_technic_id+'" type="button" class="dropdown-item fw-bolder text-danger button_delete_app_tech">Удалить заявку</button>')
    button_del.click(function (e){deleteAppTechnic(app_technic_id)})
    const li4 = $('<li/>').append(button_del)
    ul1.append(li2, li3, li4)
    divIn1.append(buttonIn3, ul1)
    div8.append(divIn1)
    const spanMissingDriver = $('<span id="span_missing_driver_'+app_technic_id+'" style="display: none" class="small text-warning">На данный момент водитель отсутствует</span>');
    div2.append(div3, div8, spanMissingDriver)

    const div9 = $('<div/>');
    const input10 = $('<input type="hidden" id="orig_technic_title_'+app_technic_id+'" value="'+technic_title+'"/>');
    const input11 = $('<input type="hidden" id="orig_technic_sheet_'+app_technic_id+'" value="'+technic_sheet_id+'"/>');
    const input12 = $('<input type="hidden" id="orig_technic_description_'+app_technic_id+'" value="'+app_tech_desc+'"/>');
    div9.append(input10, input11, input12)

    const divDesc1 = $('<div class="row"/>')
    const labelDesc2 = $('<label/>')
    const textareaDesc3 = $('<textarea id="app_tech_description_'+app_technic_id+'" style="width: 100%; font-size: '+font_size+'pt;" class="form-control app_tech_description app_technic_description_'+app_technic_id+' general_tech_description_font">'+app_tech_desc+'</textarea>')
    // textareaDesc3.on('input',function (e){autoResize(e.target); $('#btn_edit_technics_and_materials').hide(); $('#main_footer').hide();})
    textareaDesc3.on('input',function (e){autoResize(e.target);})
    textareaDesc3.on('blur',function (e){blurAppTechnic(app_technic_id)})
    labelDesc2.append(textareaDesc3)
    divDesc1.append(labelDesc2)

    div1.append(div2, div9, divDesc1)
    return div1
}
