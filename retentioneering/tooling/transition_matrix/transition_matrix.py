from __future__ import annotations

import networkx as nx
import pandas as pd
from IPython.display import display

from retentioneering.edgelist import Edgelist
from retentioneering.eventstream.types import EventstreamType
from retentioneering.nodelist import Nodelist
from retentioneering.tooling.typing.transition_graph import NormType


class TransitionMatrix:
    __edgelist: Edgelist

    def __init__(self, eventstream: EventstreamType) -> None:
        self.__eventstream = eventstream
        self.__nodelist = Nodelist(
            nodelist_default_col=eventstream.schema.event_name,
            custom_cols=eventstream.schema.custom_cols,
            time_col=eventstream.schema.event_timestamp,
            event_col=eventstream.schema.event_name,
        )
        self.__nodelist.calculate_nodelist(self.__eventstream.to_dataframe())
        self.__edgelist = Edgelist(eventstream=eventstream)

    def values(self, weight_col: str | None = None, norm_type: NormType = None) -> pd.DataFrame:
        """
        Parameters
        ----------
        weight_col : str or None
        norm_type : {"full", "node", None}

        Returns
        -------
        pd.DataFrame
            Transition matrix
        """
        if weight_col is None:
            weight_col = "event_id"
        self.__edgelist.calculate_edgelist(norm_type=norm_type, weight_cols=[weight_col])
        edgelist: pd.DataFrame = self.__edgelist.edgelist_df
        graph = nx.DiGraph()
        graph.add_weighted_edges_from(edgelist.values)
        return nx.to_pandas_adjacency(G=graph)

    def display(self, weight_col: str | None, norm_type: NormType) -> None:
        transition_matrix = self.values(weight_col=weight_col, norm_type=norm_type)
        display(transition_matrix)
