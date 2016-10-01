from flask.ext.assets import Bundle

app_css = Bundle(
    'app.scss',
    filters='scss',
    output='styles/app.css',
    depends=('*.scss')
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
    'vendor/animate.min.css',
    output='styles/vendor.css'
)

vendor_js = Bundle(
    'vendor/jquery.min.js',
    'vendor/semantic.min.js',
    'vendor/tablesort.min.js',
    'vendor/papaparse.min.js',
    filters='jsmin',
    output='scripts/vendor.js'
)

guiders_js = Bundle(
    'guiders.js',
    output='scripts/guiders.js'
)
