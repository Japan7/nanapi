"""Index page for nanalook."""

import reflex as rx

from nanapi.reflex.nanalook.state import NanalookState

from ..components.layout import layout


@rx.page(route='[client_id]/nanalook/', title='NanaLook', on_load=NanalookState.load_projections)
def index() -> rx.Component:
    return layout(
        rx.center(
            rx.vstack(
                rx.heading('NanaLook', size='9'),
                rx.text('Select a projection from the sidebar', size='5', color='gray'),
            ),
            height='100vh',
        ),
    )
