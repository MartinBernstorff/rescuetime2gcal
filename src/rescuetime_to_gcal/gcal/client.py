import logging
import time
from datetime import datetime
from typing import Sequence

from gcsa.event import Event as GCSAEvent
from gcsa.google_calendar import GoogleCalendar
from google.oauth2.credentials import Credentials

from rescuetime_to_gcal.constants import required_scopes
from rescuetime_to_gcal.event import Event


def _deduplicate_events(
    events: Sequence[GCSAEvent], events_in_calendar: Sequence[GCSAEvent]
) -> Sequence[GCSAEvent]:
    # Filter out events that are in the calendar, based on the start, end and summary attributes
    events_to_sync = [
        event
        for event in events
        if not any(
            [
                event.start == calendar_event.start
                and event.end == calendar_event.end
                and event.summary == calendar_event.summary
                for calendar_event in events_in_calendar
            ]
        )
    ]

    return events_to_sync


def _update_event_if_exists(
    event_to_sync: GCSAEvent,
    events_in_calendar: Sequence[GCSAEvent],
    calendar: GoogleCalendar,
) -> bool:
    # Check if event exists in calendar based on summary and start time
    event_matches = [
        event
        for event in events_in_calendar
        if event.summary == event_to_sync.summary and event.start == event_to_sync.start
    ]

    if len(event_matches) == 0:
        return False

    matched_event = event_matches[0]
    event_matches[0].end = event_to_sync.end
    calendar.update_event(matched_event)
    logging.info(
        f"Updated event in calendar, {matched_event.start} - {matched_event.summary}"
    )
    return True


def _sync_event(
    event_to_sync: GCSAEvent,
    events_in_calendar: Sequence[GCSAEvent],
    calendar: GoogleCalendar,
):
    event_updated = _update_event_if_exists(
        event_to_sync=event_to_sync,
        events_in_calendar=events_in_calendar,
        calendar=calendar,
    )

    if not event_updated:
        # Add event to calendar
        calendar.add_event(event_to_sync)
        logging.info(
            f"Added event to calendar, {event_to_sync.start} - {event_to_sync.summary}"
        )
        time.sleep(5)


def sync(
    email: str,
    client_id: str,
    client_secret: str,
    refresh_token: str,
    events: Sequence[Event],
) -> None:
    calendar = GoogleCalendar(
        email,
        credentials=Credentials(
            token=None,
            refresh_token=refresh_token,
            token_uri="https://oauth2.googleapis.com/token",
            scopes=required_scopes,
            client_id=client_id,
            client_secret=client_secret,
        ),
    )

    events_in_calendar = list(
        calendar.get_events(
            min([event.start for event in events]),
            datetime.today(),
            order_by="updated",
            single_events=True,
        )
    )

    deduped_events = _deduplicate_events(
        events=[
            GCSAEvent(
                summary=e.title,
                start=e.start,
                end=e.end,
            )
            for e in events
        ],
        events_in_calendar=events_in_calendar,
    )

    # Update events if already exists with identical start time
    for event in deduped_events:
        _sync_event(
            event_to_sync=event,
            events_in_calendar=events_in_calendar,
            calendar=calendar,
        )