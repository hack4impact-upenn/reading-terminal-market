from flask.ext.assets import Bundle

app_css = Bundle(
    '*.scss',
    filters='scss',
    output='styles/app.css'
)

images_png = Bundle(
    'clock.gif',
    'images/guiders_x_button.jpg',
    output='guiders_arrows.png'
)

app_js = Bundle(
    'app.js',
    filters='jsmin',
    output='scripts/app.js'
)

vendor_css = Bundle(
    'vendor/semantic.min.css',
    output='styles/vendor.css'
)

vendor_js = Bundle(
    'vendor/jquery.min.js',
    'vendor/semantic.min.js',
    'vendor/tablesort.min.js',
    filters='jsmin',
    output='scripts/vendor.js'
)

guiders_js = Bundle(
    'guiders.js',
    output='scripts/guiders.js'
)
