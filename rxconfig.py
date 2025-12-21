import reflex as rx

config = rx.Config(
    app_name='nanapi',
    app_module_import='nanapi.reflex',
    plugins=[
        rx.plugins.SitemapPlugin(),
        rx.plugins.TailwindV4Plugin(),
    ],
)
