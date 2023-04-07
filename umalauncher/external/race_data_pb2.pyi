from google.protobuf.internal import containers as _containers
from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Iterable as _Iterable, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class RaceSimulateData(_message.Message):
    __slots__ = ["__padding_size_1", "__padding_size_2", "__padding_size_3", "distance_diff_max", "event", "event_count", "frame", "frame_count", "frame_size", "header", "horse_frame_size", "horse_num", "horse_result", "horse_result_size"]
    class EventDataWrapper(_message.Message):
        __slots__ = ["event", "event_size"]
        EVENT_FIELD_NUMBER: _ClassVar[int]
        EVENT_SIZE_FIELD_NUMBER: _ClassVar[int]
        event: RaceSimulateEventData
        event_size: int
        def __init__(self, event_size: _Optional[int] = ..., event: _Optional[_Union[RaceSimulateEventData, _Mapping]] = ...) -> None: ...
    DISTANCE_DIFF_MAX_FIELD_NUMBER: _ClassVar[int]
    EVENT_COUNT_FIELD_NUMBER: _ClassVar[int]
    EVENT_FIELD_NUMBER: _ClassVar[int]
    FRAME_COUNT_FIELD_NUMBER: _ClassVar[int]
    FRAME_FIELD_NUMBER: _ClassVar[int]
    FRAME_SIZE_FIELD_NUMBER: _ClassVar[int]
    HEADER_FIELD_NUMBER: _ClassVar[int]
    HORSE_FRAME_SIZE_FIELD_NUMBER: _ClassVar[int]
    HORSE_NUM_FIELD_NUMBER: _ClassVar[int]
    HORSE_RESULT_FIELD_NUMBER: _ClassVar[int]
    HORSE_RESULT_SIZE_FIELD_NUMBER: _ClassVar[int]
    __PADDING_SIZE_1_FIELD_NUMBER: _ClassVar[int]
    __PADDING_SIZE_2_FIELD_NUMBER: _ClassVar[int]
    __PADDING_SIZE_3_FIELD_NUMBER: _ClassVar[int]
    __padding_size_1: int
    __padding_size_2: int
    __padding_size_3: int
    distance_diff_max: float
    event: _containers.RepeatedCompositeFieldContainer[RaceSimulateData.EventDataWrapper]
    event_count: int
    frame: _containers.RepeatedCompositeFieldContainer[RaceSimulateFrameData]
    frame_count: int
    frame_size: int
    header: RaceSimulateHeaderData
    horse_frame_size: int
    horse_num: int
    horse_result: _containers.RepeatedCompositeFieldContainer[RaceSimulateHorseResultData]
    horse_result_size: int
    def __init__(self, header: _Optional[_Union[RaceSimulateHeaderData, _Mapping]] = ..., distance_diff_max: _Optional[float] = ..., horse_num: _Optional[int] = ..., horse_frame_size: _Optional[int] = ..., horse_result_size: _Optional[int] = ..., __padding_size_1: _Optional[int] = ..., frame_count: _Optional[int] = ..., frame_size: _Optional[int] = ..., frame: _Optional[_Iterable[_Union[RaceSimulateFrameData, _Mapping]]] = ..., __padding_size_2: _Optional[int] = ..., horse_result: _Optional[_Iterable[_Union[RaceSimulateHorseResultData, _Mapping]]] = ..., __padding_size_3: _Optional[int] = ..., event_count: _Optional[int] = ..., event: _Optional[_Iterable[_Union[RaceSimulateData.EventDataWrapper, _Mapping]]] = ...) -> None: ...

class RaceSimulateEventData(_message.Message):
    __slots__ = ["frame_time", "param", "param_count", "type"]
    class SimulateEventType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = []
    CHALLENGE_MATCH_POINT: RaceSimulateEventData.SimulateEventType
    COMPETE_FIGHT: RaceSimulateEventData.SimulateEventType
    COMPETE_TOP: RaceSimulateEventData.SimulateEventType
    FRAME_TIME_FIELD_NUMBER: _ClassVar[int]
    NOUSE_2: RaceSimulateEventData.SimulateEventType
    PARAM_COUNT_FIELD_NUMBER: _ClassVar[int]
    PARAM_FIELD_NUMBER: _ClassVar[int]
    RELEASE_CONSERVE_POWER: RaceSimulateEventData.SimulateEventType
    SCORE: RaceSimulateEventData.SimulateEventType
    SKILL: RaceSimulateEventData.SimulateEventType
    TYPE_FIELD_NUMBER: _ClassVar[int]
    frame_time: float
    param: _containers.RepeatedScalarFieldContainer[int]
    param_count: int
    type: RaceSimulateEventData.SimulateEventType
    def __init__(self, frame_time: _Optional[float] = ..., type: _Optional[_Union[RaceSimulateEventData.SimulateEventType, str]] = ..., param_count: _Optional[int] = ..., param: _Optional[_Iterable[int]] = ...) -> None: ...

class RaceSimulateFrameData(_message.Message):
    __slots__ = ["horse_frame", "time"]
    HORSE_FRAME_FIELD_NUMBER: _ClassVar[int]
    TIME_FIELD_NUMBER: _ClassVar[int]
    horse_frame: _containers.RepeatedCompositeFieldContainer[RaceSimulateHorseFrameData]
    time: float
    def __init__(self, time: _Optional[float] = ..., horse_frame: _Optional[_Iterable[_Union[RaceSimulateHorseFrameData, _Mapping]]] = ...) -> None: ...

class RaceSimulateHeaderData(_message.Message):
    __slots__ = ["max_length", "version"]
    MAX_LENGTH_FIELD_NUMBER: _ClassVar[int]
    VERSION_FIELD_NUMBER: _ClassVar[int]
    max_length: int
    version: int
    def __init__(self, max_length: _Optional[int] = ..., version: _Optional[int] = ...) -> None: ...

class RaceSimulateHorseFrameData(_message.Message):
    __slots__ = ["block_front_horse_index", "distance", "hp", "lane_position", "speed", "temptation_mode"]
    class TemptationMode(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = []
    BLOCK_FRONT_HORSE_INDEX_FIELD_NUMBER: _ClassVar[int]
    BOOST: RaceSimulateHorseFrameData.TemptationMode
    DISTANCE_FIELD_NUMBER: _ClassVar[int]
    HP_FIELD_NUMBER: _ClassVar[int]
    LANE_POSITION_FIELD_NUMBER: _ClassVar[int]
    NULL: RaceSimulateHorseFrameData.TemptationMode
    POSITION_NIGE: RaceSimulateHorseFrameData.TemptationMode
    POSITION_SASHI: RaceSimulateHorseFrameData.TemptationMode
    POSITION_SENKO: RaceSimulateHorseFrameData.TemptationMode
    SPEED_FIELD_NUMBER: _ClassVar[int]
    TEMPTATION_MODE_FIELD_NUMBER: _ClassVar[int]
    block_front_horse_index: int
    distance: float
    hp: int
    lane_position: int
    speed: int
    temptation_mode: RaceSimulateHorseFrameData.TemptationMode
    def __init__(self, distance: _Optional[float] = ..., lane_position: _Optional[int] = ..., speed: _Optional[int] = ..., hp: _Optional[int] = ..., temptation_mode: _Optional[_Union[RaceSimulateHorseFrameData.TemptationMode, str]] = ..., block_front_horse_index: _Optional[int] = ...) -> None: ...

class RaceSimulateHorseResultData(_message.Message):
    __slots__ = ["defeat", "finish_diff_time", "finish_order", "finish_time", "finish_time_raw", "guts_order", "last_spurt_start_distance", "running_style", "start_delay_time", "wiz_order"]
    class RunningStyle(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = []
    DEFEAT_FIELD_NUMBER: _ClassVar[int]
    FINISH_DIFF_TIME_FIELD_NUMBER: _ClassVar[int]
    FINISH_ORDER_FIELD_NUMBER: _ClassVar[int]
    FINISH_TIME_FIELD_NUMBER: _ClassVar[int]
    FINISH_TIME_RAW_FIELD_NUMBER: _ClassVar[int]
    GUTS_ORDER_FIELD_NUMBER: _ClassVar[int]
    LAST_SPURT_START_DISTANCE_FIELD_NUMBER: _ClassVar[int]
    NIGE: RaceSimulateHorseResultData.RunningStyle
    NONE: RaceSimulateHorseResultData.RunningStyle
    OIKOMI: RaceSimulateHorseResultData.RunningStyle
    RUNNING_STYLE_FIELD_NUMBER: _ClassVar[int]
    SASHI: RaceSimulateHorseResultData.RunningStyle
    SENKO: RaceSimulateHorseResultData.RunningStyle
    START_DELAY_TIME_FIELD_NUMBER: _ClassVar[int]
    WIZ_ORDER_FIELD_NUMBER: _ClassVar[int]
    defeat: int
    finish_diff_time: float
    finish_order: int
    finish_time: float
    finish_time_raw: float
    guts_order: int
    last_spurt_start_distance: float
    running_style: RaceSimulateHorseResultData.RunningStyle
    start_delay_time: float
    wiz_order: int
    def __init__(self, finish_order: _Optional[int] = ..., finish_time: _Optional[float] = ..., finish_diff_time: _Optional[float] = ..., start_delay_time: _Optional[float] = ..., guts_order: _Optional[int] = ..., wiz_order: _Optional[int] = ..., last_spurt_start_distance: _Optional[float] = ..., running_style: _Optional[_Union[RaceSimulateHorseResultData.RunningStyle, str]] = ..., defeat: _Optional[int] = ..., finish_time_raw: _Optional[float] = ...) -> None: ...
