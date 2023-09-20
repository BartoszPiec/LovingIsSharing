// Event handler for clicking the "Mark Done" button
$(".mark-done-btn").click(function () {
    var taskId = $(this).data("task-id");
    var buttonElement = $(this);

    markTaskAsDone(taskId, buttonElement);
});

// Function to handle marking a task as done
function markTaskAsDone(taskId, buttonElement) {
    $.ajax({
        url: "/mark_done/" + taskId,
        type: "POST",
        success: function (response) {
            if (response.success) {
                // Update the UI to reflect the task status change
                const statusElement = $("#task-status-" + taskId);
                if (statusElement.text() === 'Done') {
                    statusElement.text('Not Done');
                    statusElement.removeClass('bg-success').addClass('bg-danger');
                    buttonElement.removeClass('btn-success').addClass('btn-danger');
                } else {
                    statusElement.text('Done');
                    statusElement.removeClass('bg-danger').addClass('bg-success');
                    buttonElement.removeClass('btn-danger').addClass('btn-success');
                }
            } else {
                // Display the error message as a pop-up
                alert(response.error);
            }
        },
        error: function (error) {
            console.error('AJAX Error:', error);
            alert("An error occurred while processing your request.");
        },
    });
}