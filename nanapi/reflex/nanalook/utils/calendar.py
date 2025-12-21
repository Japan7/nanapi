"""ICS parsing and color generation utilities for nanalook calendar."""

from typing import Any

from icalendar import Calendar


def string_to_hsl(s: str, saturation: int = 70, lightness: int = 60) -> str:
    """Convert a string to an HSL color using hash-based hue calculation.

    Ported from nanalook's calendar.ts stringToHue function (used by uniqolor).

    Args:
        s: Input string (typically discord_id)
        saturation: HSL saturation percentage (0-100)
        lightness: HSL lightness percentage (0-100)

    Returns:
        HSL color string like "hsl(123, 70%, 60%)"
    """
    # Hash string to generate hue (0-360)
    hash_val = 0
    for char in s:
        hash_val = ord(char) + ((hash_val << 5) - hash_val)
        hash_val = hash_val & 0xFFFFFFFF  # Keep it 32-bit

    hue = abs(hash_val) % 360
    return f'hsl({hue}, {saturation}%, {lightness}%)'


def calendar_to_events(calendar: Calendar, username: str, color: str) -> list[dict[str, Any]]:
    """Convert an already-parsed `icalendar.Calendar` to FullCalendar event format."""
    events: list[dict[str, Any]] = []
    for event in calendar.events:
        event_dict = {
            'id': f'{username}_{event.uid}',
            'title': event.summary,
            'start': event.start.isoformat() if event.start else '',
            'end': event.end.isoformat() if event.end else '',
            'backgroundColor': color,
            'borderColor': color,
            'extendedProps': {
                'source': username,
            },
        }
        events.append(event_dict)

    return events
