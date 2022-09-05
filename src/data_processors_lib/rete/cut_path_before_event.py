from __future__ import annotations

import logging
from typing import Any, Callable, List

from pandas import DataFrame

from src.data_processor.data_processor import DataProcessor
from src.eventstream.eventstream import Eventstream
from src.eventstream.schema import EventstreamSchema
from src.params_model import ParamsModel

log = logging.getLogger(__name__)

EventstreamFilter = Callable[[DataFrame, EventstreamSchema], Any]


class CutPathBeforeEventParams(ParamsModel):
    cutoff_events: List[str]
    cut_shift: int
    min_cjm: int


class CutPathBeforeEvent(DataProcessor):
    params: CutPathBeforeEventParams

    def __init__(self, params: CutPathBeforeEventParams):
        super().__init__(params=params)

    def apply(self, eventstream: Eventstream) -> Eventstream:
        user_col = eventstream.schema.user_id
        time_col = eventstream.schema.event_timestamp
        event_col = eventstream.schema.event_name
        id_col = eventstream.schema.event_id

        cutoff_events = self.params.cutoff_events
        min_cjm = self.params.min_cjm
        cut_shift = self.params.cut_shift

        df = eventstream.to_dataframe(copy=True)

        df["_point"] = 0
        df.loc[df[event_col].isin(cutoff_events), "_point"] = 1
        df["_point"] = df.groupby([user_col, time_col])._point.transform(max)

        _cumsum = df.groupby([user_col])._point.cumsum()
        df_cut = df[_cumsum > 0]
        ids_to_del = df[_cumsum == 0][id_col].to_list()

        df_cut["num_groups"] = df_cut.groupby([user_col])[time_col].transform(
            lambda x: x.diff().astype(int).ne(0).cumsum()
        )

        if cut_shift > 0:
            ids_to_del = ids_to_del + df_cut[df_cut["num_groups"] <= cut_shift][id_col].to_list()
            df_cut = df_cut[df_cut["num_groups"] > cut_shift]

        if min_cjm > 0:
            df_cut = df_cut.groupby([user_col])[["num_groups"]].max().reset_index()
            users_to_del = df_cut[df_cut["num_groups"] < min_cjm][user_col].to_list()
            # TODO dasha - после fix поменять на soft
            df = df.loc[df[user_col].apply(lambda x: x in users_to_del)]  # type: ignore

        # TODO dasha - после fix поменять на soft
        df = df.loc[df[id_col].apply(lambda x: x in ids_to_del)]  # type: ignore
        df["ref"] = df[eventstream.schema.event_id]

        eventstream = Eventstream(
            raw_data_schema=eventstream.schema.to_raw_data_schema(),
            raw_data=df,
            relations=[{"raw_col": "ref", "evenstream": eventstream}],
        )
        return eventstream
