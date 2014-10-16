/*global document, jQuery, bootbox */
/*jslint indent: 4, maxlen: 80 */

(function ($) {
    "use strict";

    function getParameterByName(name) {
        name = name.replace(/[\[]/, "\\[").replace(/[\]]/, "\\]");
        var regex = new RegExp("[\\?&]" + name + "=([^&#]*)"),
            results = regex.exec(location.search);
        return results === null ? null : decodeURIComponent(
            results[1].replace(/\+/g, " "));
    }

    function enableDefaultPlugins() {
        // Enable bootstrap tooltips
        $("body").tooltip({
            html: true,
            selector: "*[data-toggle='tooltip']"
        });

        // Enable jquery.timeago.js
        $("time.timeago").timeago();

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

        // Activate chosen jquery plugin for all selects
        $("select").chosen({search_contains: true});
    }

    $(document).ready(function () {

        enableDefaultPlugins();

        if ($('.datatable').length > 0 && $('.datatable').dataTable) {
            $('.datatable').each(function() {

                // Read columns configuration from DOM
                var $table = $( this ),
                    sort_direction = $table.data('sortDescending') ?
                        'desc' : 'asc',
                    aoColumns = [];
                $table.find("thead th").each(function () {
                    var $this = $(this);
                    if ($this.data('sortDisabled') === true) {
                        aoColumns.push({ "bSortable": false });
                    } else {
                        aoColumns.push(null);
                    }
                });

                // Read sorting parameters from querystring
                var iSortCol_0 = getParameterByName('iSortCol_0'),
                    sSortDir_0 = getParameterByName('sSortDir_0');
                if (iSortCol_0 === null) {
                    iSortCol_0 = 0;
                }
                if (sSortDir_0 === null) {
                    sSortDir_0 = sort_direction;
                }

                // Prepare datatables settings
                var settings = {
                    "aaSorting"   : [[iSortCol_0, sSortDir_0]],
                    "aoColumns"   : aoColumns,
                    "stateSave"   : true,
                };
                if ($table.data('ajax') === true) {
                    /* jshint ignore:start */
                    settings["bProcessing"] = true;
                    settings["bServerSide"] = true;
                    settings["sAjaxSource"] = document.URL;
                    /* jshint ignore:end */
                }

                // Initialize datatable
                $table.dataTable(settings);

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

    $( document ).ajaxComplete(function() {
        enableDefaultPlugins();
    });

}(jQuery));
