from enum import StrEnum


class TeamEnum(StrEnum):
    HOME = '*'
    AWAY = 'a'


class SkillEnum(StrEnum):
    ATTACK = 'A'
    BLOCK = 'B'
    DIG = 'D'
    SET = 'E'
    FREE = 'F'
    RECEIVE = 'R'
    SERVE = 'S'

    @property
    def combo(self) -> SkillEnum:
        return _SKILL_COMBO.get(self, self)

_SKILL_COMBO: dict[SkillEnum, SkillEnum] = {
    SkillEnum.ATTACK: SkillEnum.BLOCK,
    SkillEnum.SERVE: SkillEnum.RECEIVE
}


class HitEnum(StrEnum):
    HIGH = 'H'
    MEDIUM = 'M'
    FAST = 'N' # zaguero
    OTHER = 'O'
    QUICK = 'Q'
    TENSE = 'T'
    SUPER = 'U'


class ValueEnum(StrEnum):
    PERFECT = '#'
    POSITIVE = '+'
    EXCLAMATIVE = '!'
    NEGATIVE = '-'
    SLASH = '/'
    ERROR = '='

    def combo(self, skill: SkillEnum) -> ValueEnum:
        values = _VALUE_COMBO.get(skill)
        return values.get(self, self) if values else self

_VALUE_COMBO: dict[SkillEnum, dict[ValueEnum, ValueEnum]] = {
    SkillEnum.BLOCK: {
        ValueEnum.PERFECT: ValueEnum.SLASH,
        ValueEnum.POSITIVE: ValueEnum.NEGATIVE,
        ValueEnum.SLASH: ValueEnum.POSITIVE,
        ValueEnum.NEGATIVE: ValueEnum.POSITIVE,
        ValueEnum.ERROR: ValueEnum.PERFECT,
        ValueEnum.EXCLAMATIVE: ValueEnum.EXCLAMATIVE
    },
    SkillEnum.DIG: {
        ValueEnum.PERFECT: ValueEnum.NEGATIVE,
        ValueEnum.POSITIVE: ValueEnum.NEGATIVE,
        ValueEnum.SLASH: ValueEnum.POSITIVE,
        ValueEnum.NEGATIVE: ValueEnum.POSITIVE,
        ValueEnum.ERROR: ValueEnum.PERFECT,
        ValueEnum.EXCLAMATIVE: ValueEnum.NEGATIVE
    },
    SkillEnum.RECEIVE: {
        ValueEnum.PERFECT: ValueEnum.NEGATIVE,
        ValueEnum.POSITIVE: ValueEnum.NEGATIVE,
        ValueEnum.SLASH: ValueEnum.SLASH,
        ValueEnum.NEGATIVE: ValueEnum.POSITIVE,
        ValueEnum.ERROR: ValueEnum.PERFECT,
        ValueEnum.EXCLAMATIVE: ValueEnum.EXCLAMATIVE
    }
}


class ExtEnum(StrEnum):
    X1 = 'X1'
    X2 = 'X2'
    X3 = 'X3'
    X4 = 'X4'
    X5 = 'X5'
    X6 = 'X6'
    X7 = 'X7'
    X8 = 'X8'
    X9 = 'X9'
    K1 = 'K1'
    K2 = 'K2'
    K3 = 'K3'
    K4 = 'K4'
    K5 = 'K5'
    K6 = 'K6'
    K7 = 'K7'
    K8 = 'K8'
    K9 = 'K9'
    # NONE = ''


class ZoneEnum(StrEnum):
    Z1 = 'Z1'
    Z2 = 'Z2'
    Z3 = 'Z3'
    Z4 = 'Z4'
    Z5 = 'Z5'
    Z6 = 'Z6'
    Z7 = 'Z7'
    Z8 = 'Z8'
    Z9 = 'Z9'
    # NONE = ''