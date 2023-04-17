from __future__ import annotations

import uuid
from typing import Any, Optional, Type, Union

from retentioneering.data_processor import DataProcessor
from retentioneering.data_processor.registry import dataprocessor_registry
from retentioneering.eventstream.types import EventstreamType
from retentioneering.params_model.registry import params_model_registry


class BaseNode:
    processor: Optional[DataProcessor]
    events: Optional[EventstreamType]
    pk: str
    description: Optional[str]

    def __init__(self, **kwargs: Any) -> None:
        self.pk = str(uuid.uuid4())

    def __str__(self) -> str:
        data = {"name": self.__class__.__name__, "pk": self.pk}
        return str(data)

    __repr__ = __str__

    def export(self) -> dict:
        data: dict[str, Any] = {"name": self.__class__.__name__, "pk": self.pk}
        if self.description:
            data["description"] = self.description

        if processor := getattr(self, "processor", None):
            data["processor"] = processor.to_dict()
        return data


class SourceNode(BaseNode):
    events: EventstreamType
    description: Optional[str]

    def __init__(self, source: EventstreamType, description: Optional[str] = None) -> None:
        super().__init__()
        self.events = source
        self.description = description


class EventsNode(BaseNode):
    """
    Class for regular nodes of a preprocessing graph.

    Notes
    -----
    See :doc:`Preprocessing user guide</user_guides/preprocessing>` for the details.

    See Also
    --------
    .PreprocessingGraph.add_node : Add a node to Pgraph.
    .PreprocessingGraph.combine : Run calculations of Preprocessing Graph.
    .MergeNode : Merging nodes of a preprocessing graph.

    """

    processor: DataProcessor
    events: Optional[EventstreamType]
    description: Optional[str]

    def __init__(self, processor: DataProcessor, description: Optional[str] = None) -> None:
        super().__init__()
        self.processor = processor
        self.events = None
        self.description = description

    def calc_events(self, parent: EventstreamType) -> None:
        self.events = self.processor.apply(parent)


class MergeNode(BaseNode):
    """
    Class for merging nodes of a preprocessing graph.

    Notes
    -----
    See :doc:`Preprocessing user guide</user_guides/preprocessing>` for the details.

    See Also
    --------
    .PreprocessingGraph.add_node : Add a node to Pgraph.
    .PreprocessingGraph.combine : Run calculations of Preprocessing Graph.
    .EventsNode : Regular nodes of a preprocessing graph.

    """

    events: Optional[EventstreamType]
    description: Optional[str]

    def __init__(self, description: Optional[str] = None) -> None:
        super().__init__()
        self.events = None
        self.description = description


Node = Union[SourceNode, EventsNode, MergeNode]
nodes = {
    "MergeNode": MergeNode,
    "EventsNode": EventsNode,
    "SourceNode": SourceNode,
}


class NotFoundDataprocessor(Exception):
    pass


def build_node(
    source_stream: EventstreamType,
    pk: str,
    node_name: str,
    processor_name: str | None = None,
    processor_params: dict[str, Any] | None = None,
    descriptionn: Optional[str] = None,
) -> Node:
    _node = nodes[node_name]
    node_kwargs = {}

    if node_name == "SourceNode":
        node_kwargs["source"] = source_stream

    if not processor_params:
        processor_params = {}

    if processor_name and node_name == "EventsNode":
        _params_model_registry = params_model_registry.get_registry()
        _dataprocessor_registry = dataprocessor_registry.get_registry()

        _processor: Type[DataProcessor] = _dataprocessor_registry[processor_name]  # type: ignore
        params_name = _processor.__annotations__["params"]
        _params_model = _params_model_registry[params_name] if type(params_name) is str else params_name

        params_model = _params_model(**processor_params)

        processor: DataProcessor = _processor(params=params_model)
        node_kwargs["processor"] = processor  # type: ignore

    node = _node(**node_kwargs)
    node.pk = pk
    node.description = descriptionn
    return node
