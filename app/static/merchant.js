var updateCartQuantity = function(listingID, newQuantity, callback) {
    $.ajax({
        url: '/merchant/add_to_cart/' + listingID,
        data: JSON.stringify({
            quantity: newQuantity
        }),
        contentType: "application/json",
        dataType:"json",
        success: function(data) {
            if (callback !== undefined) {
                callback()
            }
        },
        method: 'PUT'
    });
}
