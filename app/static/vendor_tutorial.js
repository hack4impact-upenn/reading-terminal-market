var x = function() {
console.log('fuck');
    guiders.createGuider({
      buttons: [{name: "Next"}],
      description: "Guiders are a user interface design pattern for introducing features of software. This dialog box, for example, is the first in a series of guiders that together make up a guide.",
      id: "first",
      next: "second",
      overlay: true,
      title: "Welcome to Guiders.js!"
    }).show();
    /* .show() means that this guider will get shown immediately after creation. */

    guiders.createGuider({
      attachTo: "#clock",
      buttons: [{name: "Close, then click on the clock.", onclick: guiders.hideAll}],
      description: "Custom event handlers can be used to hide and show guiders. This allows you to interactively show the user how to use your software by having them complete steps. To try it, click on the clock.",
      id: "third",
      next: "fourth",
      position: 2,
      title: "You can also advance guiders from custom event handlers.",
      width: 450
    });
}