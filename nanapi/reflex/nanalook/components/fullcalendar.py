"""FullCalendar React component wrapper for Reflex."""

from typing import Any

from reflex.components.component import NoSSRComponent
from reflex.utils.imports import ImportVar
from reflex.vars.base import Var


class FullCalendar(NoSSRComponent):
    """FullCalendar component for displaying calendar events."""

    # NPM package
    library = '@fullcalendar/react@6.1.15'

    # React component tag
    tag = 'FullCalendar'

    # FullCalendar is a default export
    is_default = True

    # Additional dependencies
    lib_dependencies: list[str] = [
        '@fullcalendar/core@6.1.15',
        '@fullcalendar/timegrid@6.1.15',
        '@fullcalendar/interaction@6.1.15',
    ]

    # Props
    events: Var[list[dict[str, Any]]]
    plugins: Var[list[Any]]
    initial_view: Var[str]
    height: Var[str]
    now_indicator: Var[bool]
    scroll_time: Var[str]
    locale: Var[Any]
    header_toolbar: Var[dict[str, str]]

    def add_imports(self) -> dict[str, Any]:
        """Add imports for FullCalendar plugins and locale."""
        return {
            '@fullcalendar/timegrid': ImportVar(tag='timeGridPlugin', is_default=True),
            '@fullcalendar/interaction': ImportVar(tag='interactionPlugin', is_default=True),
        }

    def add_custom_code(self) -> list[str]:
        """Add custom import for French locale (subpath import)."""
        return [
            "import frLocale from '@fullcalendar/core/locales/fr';",
        ]


# Convenience function
def full_calendar(events: list[dict[str, Any]], **props: Any) -> FullCalendar:
    """Create a FullCalendar component.

    Args:
        events: List of event dictionaries
        **props: Additional FullCalendar props

    Returns:
        FullCalendar component instance
    """
    # Inject the plugins and locale as raw JavaScript references
    # Set default values
    default_props: dict[str, Any] = {
        'plugins': Var('[timeGridPlugin, interactionPlugin]', _var_type=list),
        'initial_view': 'timeGridWeek',
        'height': 'calc(100vh - 175px)',
        'now_indicator': True,
        'scroll_time': '21:00:00',
        'locale': Var('frLocale', _var_type=str),
    }
    default_props.update(props)
    return FullCalendar.create(events=events, **default_props)
