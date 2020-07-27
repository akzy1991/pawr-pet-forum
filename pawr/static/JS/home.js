$('#deleteQuestionModal').on('show.bs.modal', function (event) {
    let button = $(event.relatedTarget)
    let question_id = button.data('id')
    let modal = $(this)
    let form = modal.find('#deleteForm')
    let url = `/question/delete/${question_id}`
    form.attr('action', url)
})