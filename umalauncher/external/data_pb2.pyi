from google.protobuf.internal import containers as _containers
from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Iterable as _Iterable, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class UMDatabase(_message.Message):
    __slots__ = ["version", "chara", "card", "support_card", "succession_relation", "race_instance", "wins_saddle", "special_case_race", "skill", "team_stadium_score_bonus", "story"]
    VERSION_FIELD_NUMBER: _ClassVar[int]
    CHARA_FIELD_NUMBER: _ClassVar[int]
    CARD_FIELD_NUMBER: _ClassVar[int]
    SUPPORT_CARD_FIELD_NUMBER: _ClassVar[int]
    SUCCESSION_RELATION_FIELD_NUMBER: _ClassVar[int]
    RACE_INSTANCE_FIELD_NUMBER: _ClassVar[int]
    WINS_SADDLE_FIELD_NUMBER: _ClassVar[int]
    SPECIAL_CASE_RACE_FIELD_NUMBER: _ClassVar[int]
    SKILL_FIELD_NUMBER: _ClassVar[int]
    TEAM_STADIUM_SCORE_BONUS_FIELD_NUMBER: _ClassVar[int]
    STORY_FIELD_NUMBER: _ClassVar[int]
    version: str
    chara: _containers.RepeatedCompositeFieldContainer[Chara]
    card: _containers.RepeatedCompositeFieldContainer[Card]
    support_card: _containers.RepeatedCompositeFieldContainer[SupportCard]
    succession_relation: _containers.RepeatedCompositeFieldContainer[SuccessionRelation]
    race_instance: _containers.RepeatedCompositeFieldContainer[RaceInstance]
    wins_saddle: _containers.RepeatedCompositeFieldContainer[WinsSaddle]
    special_case_race: _containers.RepeatedCompositeFieldContainer[SpecialCaseRace]
    skill: _containers.RepeatedCompositeFieldContainer[Skill]
    team_stadium_score_bonus: _containers.RepeatedCompositeFieldContainer[TeamStadiumScoreBonus]
    story: _containers.RepeatedCompositeFieldContainer[Story]
    def __init__(self, version: _Optional[str] = ..., chara: _Optional[_Iterable[_Union[Chara, _Mapping]]] = ..., card: _Optional[_Iterable[_Union[Card, _Mapping]]] = ..., support_card: _Optional[_Iterable[_Union[SupportCard, _Mapping]]] = ..., succession_relation: _Optional[_Iterable[_Union[SuccessionRelation, _Mapping]]] = ..., race_instance: _Optional[_Iterable[_Union[RaceInstance, _Mapping]]] = ..., wins_saddle: _Optional[_Iterable[_Union[WinsSaddle, _Mapping]]] = ..., special_case_race: _Optional[_Iterable[_Union[SpecialCaseRace, _Mapping]]] = ..., skill: _Optional[_Iterable[_Union[Skill, _Mapping]]] = ..., team_stadium_score_bonus: _Optional[_Iterable[_Union[TeamStadiumScoreBonus, _Mapping]]] = ..., story: _Optional[_Iterable[_Union[Story, _Mapping]]] = ...) -> None: ...

class Chara(_message.Message):
    __slots__ = ["id", "name", "cast_name"]
    ID_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    CAST_NAME_FIELD_NUMBER: _ClassVar[int]
    id: int
    name: str
    cast_name: str
    def __init__(self, id: _Optional[int] = ..., name: _Optional[str] = ..., cast_name: _Optional[str] = ...) -> None: ...

class Card(_message.Message):
    __slots__ = ["id", "name"]
    ID_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    id: int
    name: str
    def __init__(self, id: _Optional[int] = ..., name: _Optional[str] = ...) -> None: ...

class SupportCard(_message.Message):
    __slots__ = ["id", "name", "chara_id"]
    ID_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    CHARA_ID_FIELD_NUMBER: _ClassVar[int]
    id: int
    name: str
    chara_id: int
    def __init__(self, id: _Optional[int] = ..., name: _Optional[str] = ..., chara_id: _Optional[int] = ...) -> None: ...

class SuccessionRelation(_message.Message):
    __slots__ = ["relation_type", "relation_point", "member"]
    class Member(_message.Message):
        __slots__ = ["id", "chara_id"]
        ID_FIELD_NUMBER: _ClassVar[int]
        CHARA_ID_FIELD_NUMBER: _ClassVar[int]
        id: int
        chara_id: int
        def __init__(self, id: _Optional[int] = ..., chara_id: _Optional[int] = ...) -> None: ...
    RELATION_TYPE_FIELD_NUMBER: _ClassVar[int]
    RELATION_POINT_FIELD_NUMBER: _ClassVar[int]
    MEMBER_FIELD_NUMBER: _ClassVar[int]
    relation_type: int
    relation_point: int
    member: _containers.RepeatedCompositeFieldContainer[SuccessionRelation.Member]
    def __init__(self, relation_type: _Optional[int] = ..., relation_point: _Optional[int] = ..., member: _Optional[_Iterable[_Union[SuccessionRelation.Member, _Mapping]]] = ...) -> None: ...

class RaceInstance(_message.Message):
    __slots__ = ["id", "name", "distance", "ground_type"]
    class GroundType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = []
        UNKNOWN_GROUND_TYPE: _ClassVar[RaceInstance.GroundType]
        TURF: _ClassVar[RaceInstance.GroundType]
        DIRT: _ClassVar[RaceInstance.GroundType]
    UNKNOWN_GROUND_TYPE: RaceInstance.GroundType
    TURF: RaceInstance.GroundType
    DIRT: RaceInstance.GroundType
    ID_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    DISTANCE_FIELD_NUMBER: _ClassVar[int]
    GROUND_TYPE_FIELD_NUMBER: _ClassVar[int]
    id: int
    name: str
    distance: int
    ground_type: RaceInstance.GroundType
    def __init__(self, id: _Optional[int] = ..., name: _Optional[str] = ..., distance: _Optional[int] = ..., ground_type: _Optional[_Union[RaceInstance.GroundType, str]] = ...) -> None: ...

class WinsSaddle(_message.Message):
    __slots__ = ["id", "name", "race_instance_id", "priority", "group_id", "type"]
    class WinSaddleType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = []
        SPECIAL: _ClassVar[WinsSaddle.WinSaddleType]
        G3: _ClassVar[WinsSaddle.WinSaddleType]
        G2: _ClassVar[WinsSaddle.WinSaddleType]
        G1: _ClassVar[WinsSaddle.WinSaddleType]
    SPECIAL: WinsSaddle.WinSaddleType
    G3: WinsSaddle.WinSaddleType
    G2: WinsSaddle.WinSaddleType
    G1: WinsSaddle.WinSaddleType
    ID_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    RACE_INSTANCE_ID_FIELD_NUMBER: _ClassVar[int]
    PRIORITY_FIELD_NUMBER: _ClassVar[int]
    GROUP_ID_FIELD_NUMBER: _ClassVar[int]
    TYPE_FIELD_NUMBER: _ClassVar[int]
    id: int
    name: str
    race_instance_id: _containers.RepeatedScalarFieldContainer[int]
    priority: int
    group_id: int
    type: WinsSaddle.WinSaddleType
    def __init__(self, id: _Optional[int] = ..., name: _Optional[str] = ..., race_instance_id: _Optional[_Iterable[int]] = ..., priority: _Optional[int] = ..., group_id: _Optional[int] = ..., type: _Optional[_Union[WinsSaddle.WinSaddleType, str]] = ...) -> None: ...

class SpecialCaseRace(_message.Message):
    __slots__ = ["race_instance_id", "program_group", "race_permission", "chara_id"]
    class RacePermission(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = []
        UNKNOWN_RACE_PERMISSION: _ClassVar[SpecialCaseRace.RacePermission]
        JUNIOR_ONLY: _ClassVar[SpecialCaseRace.RacePermission]
        CLASSIC_ONLY: _ClassVar[SpecialCaseRace.RacePermission]
        CLASSIC_AFTER: _ClassVar[SpecialCaseRace.RacePermission]
        SENIOR_AFTER: _ClassVar[SpecialCaseRace.RacePermission]
        ORIGINAL: _ClassVar[SpecialCaseRace.RacePermission]
        HIDE_CLASSIC_AFTER: _ClassVar[SpecialCaseRace.RacePermission]
        CLASSIC_ONLY_SENIOR: _ClassVar[SpecialCaseRace.RacePermission]
        SENIOR_AFTER_CLASSIC: _ClassVar[SpecialCaseRace.RacePermission]
    UNKNOWN_RACE_PERMISSION: SpecialCaseRace.RacePermission
    JUNIOR_ONLY: SpecialCaseRace.RacePermission
    CLASSIC_ONLY: SpecialCaseRace.RacePermission
    CLASSIC_AFTER: SpecialCaseRace.RacePermission
    SENIOR_AFTER: SpecialCaseRace.RacePermission
    ORIGINAL: SpecialCaseRace.RacePermission
    HIDE_CLASSIC_AFTER: SpecialCaseRace.RacePermission
    CLASSIC_ONLY_SENIOR: SpecialCaseRace.RacePermission
    SENIOR_AFTER_CLASSIC: SpecialCaseRace.RacePermission
    RACE_INSTANCE_ID_FIELD_NUMBER: _ClassVar[int]
    PROGRAM_GROUP_FIELD_NUMBER: _ClassVar[int]
    RACE_PERMISSION_FIELD_NUMBER: _ClassVar[int]
    CHARA_ID_FIELD_NUMBER: _ClassVar[int]
    race_instance_id: int
    program_group: int
    race_permission: SpecialCaseRace.RacePermission
    chara_id: _containers.RepeatedScalarFieldContainer[int]
    def __init__(self, race_instance_id: _Optional[int] = ..., program_group: _Optional[int] = ..., race_permission: _Optional[_Union[SpecialCaseRace.RacePermission, str]] = ..., chara_id: _Optional[_Iterable[int]] = ...) -> None: ...

class Skill(_message.Message):
    __slots__ = ["id", "name", "grade_value", "tag_id"]
    ID_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    GRADE_VALUE_FIELD_NUMBER: _ClassVar[int]
    TAG_ID_FIELD_NUMBER: _ClassVar[int]
    id: int
    name: str
    grade_value: int
    tag_id: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, id: _Optional[int] = ..., name: _Optional[str] = ..., grade_value: _Optional[int] = ..., tag_id: _Optional[_Iterable[str]] = ...) -> None: ...

class TeamStadiumScoreBonus(_message.Message):
    __slots__ = ["id", "name"]
    ID_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    id: int
    name: str
    def __init__(self, id: _Optional[int] = ..., name: _Optional[str] = ...) -> None: ...

class Story(_message.Message):
    __slots__ = ["id", "name"]
    ID_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    id: int
    name: str
    def __init__(self, id: _Optional[int] = ..., name: _Optional[str] = ...) -> None: ...
