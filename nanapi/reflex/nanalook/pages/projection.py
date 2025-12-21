"""Projection page showing calendar for a specific projection."""

import reflex as rx

from nanapi.reflex.nanalook.components.participants import participant_legend_item

from ..components.fullcalendar import full_calendar
from ..components.layout import layout
from ..state import ProjectionNanalookState


@rx.page(
    route='[client_id]/nanalook/[projection_id]',
    title='Projection - NanaLook',
    on_load=[
        ProjectionNanalookState.load_projections,
        ProjectionNanalookState.load_calendar_events,
    ],
)
def projection() -> rx.Component:
    """Projection calendar page."""
    return layout(
        rx.cond(
            ProjectionNanalookState.selected,
            rx.vstack(
                rx.heading(
                    ProjectionNanalookState.selected.name,  # pyright: ignore[reportOptionalMemberAccess]
                    size='7',
                    class_name='py-4 px-6 whitespace-normal break-words overflow-wrap-anywhere',
                ),
                rx.box(
                    rx.hstack(
                        rx.foreach(
                            ProjectionNanalookState.participant_legends,
                            participant_legend_item,
                        ),
                        spacing='4',
                        wrap='wrap',
                    ),
                    class_name=(
                        'p-4 w-full max-w-full overflow-x-hidden border-b border-[var(--gray-6)]'
                    ),
                ),
                rx.box(
                    rx.cond(
                        ProjectionNanalookState.calendar_events,
                        full_calendar(
                            events=ProjectionNanalookState.calendar_events,  # pyright: ignore[reportArgumentType]
                            height='calc(100vh - 240px)',
                        ),
                        rx.text('Loading...', size='5'),
                    ),
                    class_name='p-4 w-full max-w-full overflow-x-auto',
                ),
                spacing='0',
                class_name='w-full max-w-full overflow-x-hidden',
            ),
            rx.center(
                rx.text('Loading...', size='5'),
                class_name='h-[calc(100vh-80px)]',
            ),
        ),
    )
