$('#deleteQuestionModal').on('show.bs.modal', function (event) {
    let button = $(event.relatedTarget);
    let question_id = button.data('id');
    let modal = $(this);
    let form = modal.find('#deleteQuestionForm');
    let url = `/question/delete/${question_id}`;
    form.attr('action', url);
});

$('#deleteAnswerModal').on('show.bs.modal', function (event) {
    let button = $(event.relatedTarget);
    let answer_id = button.data('id');
    let modal = $(this);
    let form = modal.find('#deleteAnswerForm');
    let url = `/question/answer/delete/${answer_id}`;
    form.attr('action', url);
});


