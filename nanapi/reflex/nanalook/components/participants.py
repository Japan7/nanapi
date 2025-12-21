import reflex as rx

from nanapi.reflex.nanalook.state import ParticipantLegend


def participant_legend_item(participant: ParticipantLegend) -> rx.Component:
    """Render a single participant in the legend."""
    return rx.hstack(
        rx.box(
            class_name='w-5 h-5 rounded',
            style={'background_color': participant.color},
        ),
        rx.text(participant.username),
        spacing='2',
        align_items='center',
    )
