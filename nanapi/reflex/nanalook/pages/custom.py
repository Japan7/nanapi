"""Custom calendar page for multiple users."""

import reflex as rx

from nanapi.reflex.nanalook.components.participants import participant_legend_item

from ..components.fullcalendar import full_calendar
from ..components.layout import layout
from ..state import CustomNanalookState


@rx.page(
    route='[client_id]/nanalook/custom',
    title='Custom Calendar - NanaLook',
    on_load=[CustomNanalookState.load_projections, CustomNanalookState.load_calendar_events],
)
def custom() -> rx.Component:
    """Custom calendar page for multiple users."""
    return layout(
        rx.vstack(
            rx.heading(
                'Custom Calendar',
                size='7',
                class_name='py-4 px-6 whitespace-normal break-words',
            ),
            rx.box(
                rx.hstack(
                    rx.foreach(
                        CustomNanalookState.participant_legends,
                        participant_legend_item,
                    ),
                    spacing='4',
                    wrap='wrap',
                ),
                class_name=(
                    'p-4 w-full max-w-full overflow-x-hidden border-b border-[var(--gray-6)]'
                ),
            ),
            rx.cond(
                CustomNanalookState.calendar_events,
                rx.box(
                    rx.cond(
                        CustomNanalookState.calendar_events,
                        full_calendar(
                            events=CustomNanalookState.calendar_events,  # pyright: ignore[reportArgumentType]
                            height='calc(100vh - 240px)',
                        ),
                        rx.text('Loading...', size='5'),
                    ),
                    class_name='p-4 w-full max-w-full overflow-x-auto',
                ),
            ),
            spacing='0',
            class_name='w-full max-w-full overflow-x-hidden',
        ),
    )
