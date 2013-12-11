/*global document, jQuery */
/*jslint indent: 4, maxlen: 80 */

(function ($) {
    "use strict";

    $(document).ready(function () {

        // Enable bootstrap tooltips
        $("body").tooltip({
            selector: "span[data-toggle='tooltip']",
            html: true
        });
    });

}(jQuery));