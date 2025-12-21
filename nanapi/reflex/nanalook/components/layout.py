"""Layout component with sidebar and main content area."""

import reflex as rx

from nanapi.database.projection.projo_select import ProjoSelectResult

from ..state import NanalookState, ProjectionNanalookState

DRAWER_CLASS = (
    'h-full w-[min(250px,80vw)] max-w-[80vw] p-6 '
    'bg-[var(--color-background)] border-r border-[var(--gray-6)] '
    'overflow-y-auto overflow-x-hidden'
)


def layout(*children: rx.Component) -> rx.Component:
    """Layout with sidebar and content area.

    Uses drawer for responsive sidebar behavior - drawer on mobile/tablet,
    always visible sidebar on desktop.

    Args:
        *children: Content to display in main area

    Returns:
        Layout component with sidebar and content
    """
    return rx.box(
        rx.desktop_only(
            rx.flex(
                sidebar(),
                rx.box(*children, class_name='flex-1 overflow-y-auto h-screen'),
                class_name='w-full h-screen',
            ),
        ),
        rx.mobile_and_tablet(
            rx.flex(
                rx.drawer.root(
                    rx.drawer.trigger(
                        rx.icon_button(
                            rx.icon('menu', size=40),
                            class_name='fixed bottom-4 right-4 z-10 w-14 h-14',
                        ),
                    ),
                    rx.drawer.overlay(class_name='z-[5]'),
                    rx.drawer.portal(
                        rx.drawer.content(
                            rx.vstack(
                                rx.drawer.close(rx.icon('x', size=30)),
                                sidebar_inner_content(),
                                spacing='5',
                                class_name='w-full',
                            ),
                            class_name=DRAWER_CLASS,
                        ),
                    ),
                    direction='left',
                ),
                rx.box(
                    *children,
                    class_name='w-full max-w-screen h-screen overflow-y-auto overflow-x-hidden',
                ),
                class_name='w-full max-w-screen h-screen overflow-x-hidden',
            ),
        ),
    )


def sidebar() -> rx.Component:
    """Sidebar with list of ongoing projections."""
    return rx.box(
        sidebar_inner_content(),
        class_name='p-6 w-[250px] h-screen border-r border-[var(--gray-6)] overflow-y-auto',
    )


def sidebar_inner_content() -> rx.Component:
    """Render sidebar inner content (heading and projection links)."""
    return rx.vstack(
        rx.heading('NanaLook', size='6', class_name='mb-4'),
        rx.foreach(NanalookState.projections, projection_link),
        align_items='stretch',
        spacing='2',
        class_name='w-full',
    )


def projection_link(projection: ProjoSelectResult) -> rx.Component:
    """Render a single projection link."""
    return rx.link(
        rx.box(
            rx.text(
                projection.name,
                class_name='whitespace-normal break-words overflow-wrap-anywhere w-full',
            ),
            class_name=[
                'p-3 rounded-lg hover:bg-[var(--gray-3)] box-border',
                rx.cond(
                    ProjectionNanalookState.projection_id == projection.id,
                    'bg-[var(--gray-3)]',
                    'bg-transparent',
                ),
            ],
        ),
        href=f'/{NanalookState.client_id}/nanalook/{projection.id}',
        class_name='no-underline text-inherit block w-full',
    )
