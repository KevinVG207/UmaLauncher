from google.protobuf.internal import containers as _containers
from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Iterable as _Iterable, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class RaceSimulateData(_message.Message):
    __slots__ = ["header", "distance_diff_max", "horse_num", "horse_frame_size", "horse_result_size", "__padding_size_1", "frame_count", "frame_size", "frame", "__padding_size_2", "horse_result", "__padding_size_3", "event_count", "event"]
    class EventDataWrapper(_message.Message):
        __slots__ = ["event_size", "event"]
        EVENT_SIZE_FIELD_NUMBER: _ClassVar[int]
        EVENT_FIELD_NUMBER: _ClassVar[int]
        event_size: int
        event: RaceSimulateEventData
        def __init__(self, event_size: _Optional[int] = ..., event: _Optional[_Union[RaceSimulateEventData, _Mapping]] = ...) -> None: ...
    HEADER_FIELD_NUMBER: _ClassVar[int]
    DISTANCE_DIFF_MAX_FIELD_NUMBER: _ClassVar[int]
    HORSE_NUM_FIELD_NUMBER: _ClassVar[int]
    HORSE_FRAME_SIZE_FIELD_NUMBER: _ClassVar[int]
    HORSE_RESULT_SIZE_FIELD_NUMBER: _ClassVar[int]
    __PADDING_SIZE_1_FIELD_NUMBER: _ClassVar[int]
    FRAME_COUNT_FIELD_NUMBER: _ClassVar[int]
    FRAME_SIZE_FIELD_NUMBER: _ClassVar[int]
    FRAME_FIELD_NUMBER: _ClassVar[int]
    __PADDING_SIZE_2_FIELD_NUMBER: _ClassVar[int]
    HORSE_RESULT_FIELD_NUMBER: _ClassVar[int]
    __PADDING_SIZE_3_FIELD_NUMBER: _ClassVar[int]
    EVENT_COUNT_FIELD_NUMBER: _ClassVar[int]
    EVENT_FIELD_NUMBER: _ClassVar[int]
    header: RaceSimulateHeaderData
    distance_diff_max: float
    horse_num: int
    horse_frame_size: int
    horse_result_size: int
    __padding_size_1: int
    frame_count: int
    frame_size: int
    frame: _containers.RepeatedCompositeFieldContainer[RaceSimulateFrameData]
    __padding_size_2: int
    horse_result: _containers.RepeatedCompositeFieldContainer[RaceSimulateHorseResultData]
    __padding_size_3: int
    event_count: int
    event: _containers.RepeatedCompositeFieldContainer[RaceSimulateData.EventDataWrapper]
    def __init__(self, header: _Optional[_Union[RaceSimulateHeaderData, _Mapping]] = ..., distance_diff_max: _Optional[float] = ..., horse_num: _Optional[int] = ..., horse_frame_size: _Optional[int] = ..., horse_result_size: _Optional[int] = ..., __padding_size_1: _Optional[int] = ..., frame_count: _Optional[int] = ..., frame_size: _Optional[int] = ..., frame: _Optional[_Iterable[_Union[RaceSimulateFrameData, _Mapping]]] = ..., __padding_size_2: _Optional[int] = ..., horse_result: _Optional[_Iterable[_Union[RaceSimulateHorseResultData, _Mapping]]] = ..., __padding_size_3: _Optional[int] = ..., event_count: _Optional[int] = ..., event: _Optional[_Iterable[_Union[RaceSimulateData.EventDataWrapper, _Mapping]]] = ...) -> None: ...

class RaceSimulateHeaderData(_message.Message):
    __slots__ = ["max_length", "version"]
    MAX_LENGTH_FIELD_NUMBER: _ClassVar[int]
    VERSION_FIELD_NUMBER: _ClassVar[int]
    max_length: int
    version: int
    def __init__(self, max_length: _Optional[int] = ..., version: _Optional[int] = ...) -> None: ...

class RaceSimulateFrameData(_message.Message):
    __slots__ = ["time", "horse_frame"]
    TIME_FIELD_NUMBER: _ClassVar[int]
    HORSE_FRAME_FIELD_NUMBER: _ClassVar[int]
    time: float
    horse_frame: _containers.RepeatedCompositeFieldContainer[RaceSimulateHorseFrameData]
    def __init__(self, time: _Optional[float] = ..., horse_frame: _Optional[_Iterable[_Union[RaceSimulateHorseFrameData, _Mapping]]] = ...) -> None: ...

class RaceSimulateHorseFrameData(_message.Message):
    __slots__ = ["distance", "lane_position", "speed", "hp", "temptation_mode", "block_front_horse_index"]
    class TemptationMode(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = []
        NULL: _ClassVar[RaceSimulateHorseFrameData.TemptationMode]
        POSITION_SASHI: _ClassVar[RaceSimulateHorseFrameData.TemptationMode]
        POSITION_SENKO: _ClassVar[RaceSimulateHorseFrameData.TemptationMode]
        POSITION_NIGE: _ClassVar[RaceSimulateHorseFrameData.TemptationMode]
        BOOST: _ClassVar[RaceSimulateHorseFrameData.TemptationMode]
    NULL: RaceSimulateHorseFrameData.TemptationMode
    POSITION_SASHI: RaceSimulateHorseFrameData.TemptationMode
    POSITION_SENKO: RaceSimulateHorseFrameData.TemptationMode
    POSITION_NIGE: RaceSimulateHorseFrameData.TemptationMode
    BOOST: RaceSimulateHorseFrameData.TemptationMode
    DISTANCE_FIELD_NUMBER: _ClassVar[int]
    LANE_POSITION_FIELD_NUMBER: _ClassVar[int]
    SPEED_FIELD_NUMBER: _ClassVar[int]
    HP_FIELD_NUMBER: _ClassVar[int]
    TEMPTATION_MODE_FIELD_NUMBER: _ClassVar[int]
    BLOCK_FRONT_HORSE_INDEX_FIELD_NUMBER: _ClassVar[int]
    distance: float
    lane_position: int
    speed: int
    hp: int
    temptation_mode: RaceSimulateHorseFrameData.TemptationMode
    block_front_horse_index: int
    def __init__(self, distance: _Optional[float] = ..., lane_position: _Optional[int] = ..., speed: _Optional[int] = ..., hp: _Optional[int] = ..., temptation_mode: _Optional[_Union[RaceSimulateHorseFrameData.TemptationMode, str]] = ..., block_front_horse_index: _Optional[int] = ...) -> None: ...

class RaceSimulateHorseResultData(_message.Message):
    __slots__ = ["finish_order", "finish_time", "finish_diff_time", "start_delay_time", "guts_order", "wiz_order", "last_spurt_start_distance", "running_style", "defeat", "finish_time_raw"]
    class RunningStyle(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = []
        NONE: _ClassVar[RaceSimulateHorseResultData.RunningStyle]
        NIGE: _ClassVar[RaceSimulateHorseResultData.RunningStyle]
        SENKO: _ClassVar[RaceSimulateHorseResultData.RunningStyle]
        SASHI: _ClassVar[RaceSimulateHorseResultData.RunningStyle]
        OIKOMI: _ClassVar[RaceSimulateHorseResultData.RunningStyle]
    NONE: RaceSimulateHorseResultData.RunningStyle
    NIGE: RaceSimulateHorseResultData.RunningStyle
    SENKO: RaceSimulateHorseResultData.RunningStyle
    SASHI: RaceSimulateHorseResultData.RunningStyle
    OIKOMI: RaceSimulateHorseResultData.RunningStyle
    FINISH_ORDER_FIELD_NUMBER: _ClassVar[int]
    FINISH_TIME_FIELD_NUMBER: _ClassVar[int]
    FINISH_DIFF_TIME_FIELD_NUMBER: _ClassVar[int]
    START_DELAY_TIME_FIELD_NUMBER: _ClassVar[int]
    GUTS_ORDER_FIELD_NUMBER: _ClassVar[int]
    WIZ_ORDER_FIELD_NUMBER: _ClassVar[int]
    LAST_SPURT_START_DISTANCE_FIELD_NUMBER: _ClassVar[int]
    RUNNING_STYLE_FIELD_NUMBER: _ClassVar[int]
    DEFEAT_FIELD_NUMBER: _ClassVar[int]
    FINISH_TIME_RAW_FIELD_NUMBER: _ClassVar[int]
    finish_order: int
    finish_time: float
    finish_diff_time: float
    start_delay_time: float
    guts_order: int
    wiz_order: int
    last_spurt_start_distance: float
    running_style: RaceSimulateHorseResultData.RunningStyle
    defeat: int
    finish_time_raw: float
    def __init__(self, finish_order: _Optional[int] = ..., finish_time: _Optional[float] = ..., finish_diff_time: _Optional[float] = ..., start_delay_time: _Optional[float] = ..., guts_order: _Optional[int] = ..., wiz_order: _Optional[int] = ..., last_spurt_start_distance: _Optional[float] = ..., running_style: _Optional[_Union[RaceSimulateHorseResultData.RunningStyle, str]] = ..., defeat: _Optional[int] = ..., finish_time_raw: _Optional[float] = ...) -> None: ...

class RaceSimulateEventData(_message.Message):
    __slots__ = ["frame_time", "type", "param_count", "param"]
    class SimulateEventType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = []
        SCORE: _ClassVar[RaceSimulateEventData.SimulateEventType]
        CHALLENGE_MATCH_POINT: _ClassVar[RaceSimulateEventData.SimulateEventType]
        NOUSE_2: _ClassVar[RaceSimulateEventData.SimulateEventType]
        SKILL: _ClassVar[RaceSimulateEventData.SimulateEventType]
        COMPETE_TOP: _ClassVar[RaceSimulateEventData.SimulateEventType]
        COMPETE_FIGHT: _ClassVar[RaceSimulateEventData.SimulateEventType]
        RELEASE_CONSERVE_POWER: _ClassVar[RaceSimulateEventData.SimulateEventType]
        STAMINA_LIMIT_BREAK_BUFF: _ClassVar[RaceSimulateEventData.SimulateEventType]
        COMPETE_BEFORE_SPURT: _ClassVar[RaceSimulateEventData.SimulateEventType]
        STAMINA_KEEP: _ClassVar[RaceSimulateEventData.SimulateEventType]
        SECURE_LEAD: _ClassVar[RaceSimulateEventData.SimulateEventType]
    SCORE: RaceSimulateEventData.SimulateEventType
    CHALLENGE_MATCH_POINT: RaceSimulateEventData.SimulateEventType
    NOUSE_2: RaceSimulateEventData.SimulateEventType
    SKILL: RaceSimulateEventData.SimulateEventType
    COMPETE_TOP: RaceSimulateEventData.SimulateEventType
    COMPETE_FIGHT: RaceSimulateEventData.SimulateEventType
    RELEASE_CONSERVE_POWER: RaceSimulateEventData.SimulateEventType
    STAMINA_LIMIT_BREAK_BUFF: RaceSimulateEventData.SimulateEventType
    COMPETE_BEFORE_SPURT: RaceSimulateEventData.SimulateEventType
    STAMINA_KEEP: RaceSimulateEventData.SimulateEventType
    SECURE_LEAD: RaceSimulateEventData.SimulateEventType
    FRAME_TIME_FIELD_NUMBER: _ClassVar[int]
    TYPE_FIELD_NUMBER: _ClassVar[int]
    PARAM_COUNT_FIELD_NUMBER: _ClassVar[int]
    PARAM_FIELD_NUMBER: _ClassVar[int]
    frame_time: float
    type: RaceSimulateEventData.SimulateEventType
    param_count: int
    param: _containers.RepeatedScalarFieldContainer[int]
    def __init__(self, frame_time: _Optional[float] = ..., type: _Optional[_Union[RaceSimulateEventData.SimulateEventType, str]] = ..., param_count: _Optional[int] = ..., param: _Optional[_Iterable[int]] = ...) -> None: ...
