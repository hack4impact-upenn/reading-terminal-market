// Semantic UI breakpoints
var mobileBreakpoint = '768px';
var tabletBreakpoint = '992px';
var smallMonitorBreakpoint = '1200px';

$(document).ready(function () {

    // Enable dismissable flash messages
    $('.message .close').on('click', function () {
        $(this).closest('.message').transition('fade');
    });

    // Enable mobile navigation
    $('#open-nav').on('click', function () {
        $('.mobile.only .vertical.menu').transition('slide down');
    });

    // Enable dropdowns
    $('.dropdown').dropdown();
    $('select').dropdown();
});



