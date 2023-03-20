from google.protobuf.internal import containers as _containers
from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Iterable as _Iterable, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class Card(_message.Message):
    __slots__ = ["id", "name"]
    ID_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    id: int
    name: str
    def __init__(self, id: _Optional[int] = ..., name: _Optional[str] = ...) -> None: ...

class Chara(_message.Message):
    __slots__ = ["cast_name", "id", "name"]
    CAST_NAME_FIELD_NUMBER: _ClassVar[int]
    ID_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    cast_name: str
    id: int
    name: str
    def __init__(self, id: _Optional[int] = ..., name: _Optional[str] = ..., cast_name: _Optional[str] = ...) -> None: ...

class RaceInstance(_message.Message):
    __slots__ = ["distance", "ground_type", "id", "name"]
    class GroundType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = []
    DIRT: RaceInstance.GroundType
    DISTANCE_FIELD_NUMBER: _ClassVar[int]
    GROUND_TYPE_FIELD_NUMBER: _ClassVar[int]
    ID_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    TURF: RaceInstance.GroundType
    UNKNOWN_GROUND_TYPE: RaceInstance.GroundType
    distance: int
    ground_type: RaceInstance.GroundType
    id: int
    name: str
    def __init__(self, id: _Optional[int] = ..., name: _Optional[str] = ..., distance: _Optional[int] = ..., ground_type: _Optional[_Union[RaceInstance.GroundType, str]] = ...) -> None: ...

class Skill(_message.Message):
    __slots__ = ["grade_value", "id", "name", "tag_id"]
    GRADE_VALUE_FIELD_NUMBER: _ClassVar[int]
    ID_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    TAG_ID_FIELD_NUMBER: _ClassVar[int]
    grade_value: int
    id: int
    name: str
    tag_id: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, id: _Optional[int] = ..., name: _Optional[str] = ..., grade_value: _Optional[int] = ..., tag_id: _Optional[_Iterable[str]] = ...) -> None: ...

class SpecialCaseRace(_message.Message):
    __slots__ = ["chara_id", "program_group", "race_instance_id", "race_permission"]
    class RacePermission(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = []
    CHARA_ID_FIELD_NUMBER: _ClassVar[int]
    EX: SpecialCaseRace.RacePermission
    FIRST_YEAR: SpecialCaseRace.RacePermission
    PROGRAM_GROUP_FIELD_NUMBER: _ClassVar[int]
    RACE_INSTANCE_ID_FIELD_NUMBER: _ClassVar[int]
    RACE_PERMISSION_FIELD_NUMBER: _ClassVar[int]
    SECOND_OR_THIRD_YEAR: SpecialCaseRace.RacePermission
    SECOND_YEAR: SpecialCaseRace.RacePermission
    THIRD_YEAR: SpecialCaseRace.RacePermission
    UNKNOWN_RACE_PERMISSION: SpecialCaseRace.RacePermission
    chara_id: _containers.RepeatedScalarFieldContainer[int]
    program_group: int
    race_instance_id: int
    race_permission: SpecialCaseRace.RacePermission
    def __init__(self, race_instance_id: _Optional[int] = ..., program_group: _Optional[int] = ..., race_permission: _Optional[_Union[SpecialCaseRace.RacePermission, str]] = ..., chara_id: _Optional[_Iterable[int]] = ...) -> None: ...

class Story(_message.Message):
    __slots__ = ["id", "name"]
    ID_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    id: int
    name: str
    def __init__(self, id: _Optional[int] = ..., name: _Optional[str] = ...) -> None: ...

class SuccessionRelation(_message.Message):
    __slots__ = ["member", "relation_point", "relation_type"]
    class Member(_message.Message):
        __slots__ = ["chara_id", "id"]
        CHARA_ID_FIELD_NUMBER: _ClassVar[int]
        ID_FIELD_NUMBER: _ClassVar[int]
        chara_id: int
        id: int
        def __init__(self, id: _Optional[int] = ..., chara_id: _Optional[int] = ...) -> None: ...
    MEMBER_FIELD_NUMBER: _ClassVar[int]
    RELATION_POINT_FIELD_NUMBER: _ClassVar[int]
    RELATION_TYPE_FIELD_NUMBER: _ClassVar[int]
    member: _containers.RepeatedCompositeFieldContainer[SuccessionRelation.Member]
    relation_point: int
    relation_type: int
    def __init__(self, relation_type: _Optional[int] = ..., relation_point: _Optional[int] = ..., member: _Optional[_Iterable[_Union[SuccessionRelation.Member, _Mapping]]] = ...) -> None: ...

class SupportCard(_message.Message):
    __slots__ = ["chara_id", "id", "name"]
    CHARA_ID_FIELD_NUMBER: _ClassVar[int]
    ID_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    chara_id: int
    id: int
    name: str
    def __init__(self, id: _Optional[int] = ..., name: _Optional[str] = ..., chara_id: _Optional[int] = ...) -> None: ...

class TeamStadiumScoreBonus(_message.Message):
    __slots__ = ["id", "name"]
    ID_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    id: int
    name: str
    def __init__(self, id: _Optional[int] = ..., name: _Optional[str] = ...) -> None: ...

class UMDatabase(_message.Message):
    __slots__ = ["card", "chara", "race_instance", "skill", "special_case_race", "story", "succession_relation", "support_card", "team_stadium_score_bonus", "version", "wins_saddle"]
    CARD_FIELD_NUMBER: _ClassVar[int]
    CHARA_FIELD_NUMBER: _ClassVar[int]
    RACE_INSTANCE_FIELD_NUMBER: _ClassVar[int]
    SKILL_FIELD_NUMBER: _ClassVar[int]
    SPECIAL_CASE_RACE_FIELD_NUMBER: _ClassVar[int]
    STORY_FIELD_NUMBER: _ClassVar[int]
    SUCCESSION_RELATION_FIELD_NUMBER: _ClassVar[int]
    SUPPORT_CARD_FIELD_NUMBER: _ClassVar[int]
    TEAM_STADIUM_SCORE_BONUS_FIELD_NUMBER: _ClassVar[int]
    VERSION_FIELD_NUMBER: _ClassVar[int]
    WINS_SADDLE_FIELD_NUMBER: _ClassVar[int]
    card: _containers.RepeatedCompositeFieldContainer[Card]
    chara: _containers.RepeatedCompositeFieldContainer[Chara]
    race_instance: _containers.RepeatedCompositeFieldContainer[RaceInstance]
    skill: _containers.RepeatedCompositeFieldContainer[Skill]
    special_case_race: _containers.RepeatedCompositeFieldContainer[SpecialCaseRace]
    story: _containers.RepeatedCompositeFieldContainer[Story]
    succession_relation: _containers.RepeatedCompositeFieldContainer[SuccessionRelation]
    support_card: _containers.RepeatedCompositeFieldContainer[SupportCard]
    team_stadium_score_bonus: _containers.RepeatedCompositeFieldContainer[TeamStadiumScoreBonus]
    version: str
    wins_saddle: _containers.RepeatedCompositeFieldContainer[WinsSaddle]
    def __init__(self, version: _Optional[str] = ..., chara: _Optional[_Iterable[_Union[Chara, _Mapping]]] = ..., card: _Optional[_Iterable[_Union[Card, _Mapping]]] = ..., support_card: _Optional[_Iterable[_Union[SupportCard, _Mapping]]] = ..., succession_relation: _Optional[_Iterable[_Union[SuccessionRelation, _Mapping]]] = ..., race_instance: _Optional[_Iterable[_Union[RaceInstance, _Mapping]]] = ..., wins_saddle: _Optional[_Iterable[_Union[WinsSaddle, _Mapping]]] = ..., special_case_race: _Optional[_Iterable[_Union[SpecialCaseRace, _Mapping]]] = ..., skill: _Optional[_Iterable[_Union[Skill, _Mapping]]] = ..., team_stadium_score_bonus: _Optional[_Iterable[_Union[TeamStadiumScoreBonus, _Mapping]]] = ..., story: _Optional[_Iterable[_Union[Story, _Mapping]]] = ...) -> None: ...

class WinsSaddle(_message.Message):
    __slots__ = ["group_id", "id", "name", "priority", "race_instance_id", "type"]
    class WinSaddleType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = []
    G1: WinsSaddle.WinSaddleType
    G2: WinsSaddle.WinSaddleType
    G3: WinsSaddle.WinSaddleType
    GROUP_ID_FIELD_NUMBER: _ClassVar[int]
    ID_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    PRIORITY_FIELD_NUMBER: _ClassVar[int]
    RACE_INSTANCE_ID_FIELD_NUMBER: _ClassVar[int]
    SPECIAL: WinsSaddle.WinSaddleType
    TYPE_FIELD_NUMBER: _ClassVar[int]
    group_id: int
    id: int
    name: str
    priority: int
    race_instance_id: _containers.RepeatedScalarFieldContainer[int]
    type: WinsSaddle.WinSaddleType
    def __init__(self, id: _Optional[int] = ..., name: _Optional[str] = ..., race_instance_id: _Optional[_Iterable[int]] = ..., priority: _Optional[int] = ..., group_id: _Optional[int] = ..., type: _Optional[_Union[WinsSaddle.WinSaddleType, str]] = ...) -> None: ...
