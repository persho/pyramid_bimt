/*global document, jQuery, bootbox */
/*jslint indent: 4, maxlen: 80 */

(function ($) {
    "use strict";

    $(document).ready(function () {

        // Enable bootstrap tooltips
        $("body").tooltip({
            selector: "*[data-toggle='tooltip']"
        });

        // Enable 'secret' spans
        $("span.secret").click(function () {
            $(this).text($(this).data('secret'));
        });

        // Enable 'confirmation button' form functionality: a button that
        // pops-up a confirmation dialog before submitting the form
        $("form .btn-confirmation").click(function (e) {
            var $button = $(this),
                $form = $(this).closest("form");

            e.preventDefault();

            bootbox.confirm($button.attr('value'), function (result) {
                if (result) {
                    // the jquery submit() does not include the button in the
                    // POST so we have to manually append it
                    $('<input />').attr('type', 'hidden')
                        .attr('name', $button.attr('name'))
                        .attr('value', $button.attr('value'))
                        .appendTo($form);

                    $form.submit();
                }
            });
        });

        if ($('.datatable').length > 0 && $('.datatable').dataTable) {
            // Read columns configuration from DOM
            var $table = $('.datatable'),
                sort_direction = $table.data('sortDescending') ? 'desc' : 'asc',
                aoColumns = [];
            $(".table thead th").each(function () {
                var $this = $(this);
                if ($this.data('sortDisabled') === true) {
                    aoColumns.push({ "bSortable": false });
                } else {
                    aoColumns.push(null);
                }
            });

            // Enable datatables
            $table.dataTable({
                "aaSorting"   : [[0, sort_direction]],
                "aoColumns"   : aoColumns
            });

            $('.datatable').each(function () {
            // Add the placeholder for Search and Length and turn them into
            // in-line form controls
                var $datatable = $(this),
                    $dt_wrapper = $datatable.closest('.dataTables_wrapper'),
                    $search_input = $dt_wrapper.find('div[id$=_filter] input'),
                    $length_sel = $dt_wrapper.find('div[id$=_length] select');
                $search_input.attr('placeholder', 'Search');
                $search_input.addClass('form-control input-sm');
                $length_sel.addClass('form-control input-sm');
            });
        }

    });

}(jQuery));
