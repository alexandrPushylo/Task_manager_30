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