from typing import Callable, Any, TypedDict

import pandas as pd
from pandas import DataFrame

from src.data_processor.data_processor import DataProcessor
from src.eventstream.eventstream import Eventstream
from src.eventstream.schema import EventstreamSchema

EventstreamFilter = Callable[[DataFrame, EventstreamSchema], Any]


class StartEndEventsParams(TypedDict):
    user_col: str
    event_col: str
    time_col: str
    type_col: str


class StartEndEvents(DataProcessor[StartEndEventsParams]):

    def apply(self, eventstream: Eventstream) -> Eventstream:
        events: DataFrame = eventstream.to_dataframe()
        user_col = eventstream.schema.user_id
        time_col = eventstream.schema.event_timestamp
        type_col = eventstream.schema.event_type
        event_col = eventstream.schema.event_name

        matched_events_start: DataFrame = events.groupby(user_col, as_index=False) \
            .apply(lambda group: group.nsmallest(1, columns=time_col)) \
            .reset_index(drop=True)
        matched_events_start[type_col] = 'start'
        matched_events_start[event_col] = 'start'
        matched_events_start["ref"] = matched_events_start[eventstream.schema.event_id]

        matched_events_end = events.groupby(user_col, as_index=False) \
            .apply(lambda group: group.nlargest(1, columns=time_col)) \
            .reset_index(drop=True)
        matched_events_end[type_col] = 'end'
        matched_events_end[event_col] = 'end'
        matched_events_end["ref"] = matched_events_end[eventstream.schema.event_id]

        matched_events = pd.concat([matched_events_start, matched_events_end])

        eventstream = Eventstream(
            raw_data=matched_events,
            raw_data_schema=eventstream.schema.to_raw_data_schema(),
            relations=[{"raw_col": "ref", "evenstream": eventstream}],
        )
        return eventstream
