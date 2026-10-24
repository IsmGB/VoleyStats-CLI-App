from enum import StrEnum, IntEnum


class ColorValue(StrEnum):
    PERFECT = "#077237"
    POSITIVE = "#66C24A"
    EXCLAMATIVE = "#FFD966"
    NEGATIVE = "#E6A056"
    SLASH = "#E06666"
    ERROR = "#8D0808"



class ColorError(StrEnum):
    DEFAULT = "#cc0000"
    ATTACK = "#8B0000"
    BLOCK = "#D7191C"
    DIG = "#F04438"
    SET = "#F4511E"
    FREE = "#F57C00"
    RECEIVE = "#FF9800"
    SERVE = "#FFB74D"



class ColorPoint(StrEnum):
    DEFAULT = "#009900"
    ATTACK = "#14532D"
    BLOCK = "#15803D"
    DIG = "#16A34A"
    SET = "#10B981"
    FREE = "#0D9488"
    RECEIVE = "#84CC16"
    SERVE = "#BEF264"



class ColorCourt(StrEnum):
    DEFAUL = "#ffffff"
    HIGHLIGHT = "#ad7d7d"



class ColorPlayers(StrEnum):
    P1 = "#E6194B"
    P2 = "#3CB44B"
    P3 = "#4363D8"
    P4 = "#F58231"
    P5 = "#911EB4"
    P6 = "#42D4F4"
    P7 = "#F032E6"
    P8 = "#BFEF45"
    P9 = "#FABED4"
    P10 = "#469990"
    P11 = "#DCBEFF"
    P12 = "#9A6324"
    P13 = "#FFE119"
    P14 = "#800000"


class Colors(StrEnum):
    BLUE = "#0057B8"
    ORANGE = "#E69F00"
    GREEN = "#236121"
    RED = "#C00000"
    PURPLE = "#6A3D9A"
    CYAN = "#17BECF"
    BROWN = "#8C564B"
    GREY = "#4D4D4D"
    LIME = "#06A529"
    BLACK = "#000000"
    LIGHT_GREY = "#A0A0A0"
    WHITE = "#FFFFFF"


class ColorsHit(StrEnum):
    HIGH = Colors.PURPLE.value
    MEDIUM = Colors.ORANGE.value
    FAST = Colors.BLUE.value
    OTHER = Colors.BROWN.value
    QUICK = Colors.LIME.value
    TENSE = Colors.RED.value
    SUPER = Colors.GREY.value


class ColorsExt(StrEnum):
    X1 = Colors.BLUE.value
    X2 = Colors.ORANGE.value
    X3 = Colors.GREEN.value
    X4 = Colors.RED.value
    X5 = Colors.PURPLE.value
    X6 = Colors.CYAN.value
    X7 = Colors.BROWN.value
    X8 = Colors.GREY.value
    X9 = Colors.LIME.value
    K1 = Colors.PURPLE.value
    K2 = Colors.ORANGE.value
    K3 = Colors.BLUE.value
    K4 = Colors.RED.value
    K5 = Colors.CYAN.value
    K6 = Colors.LIME.value
    K7 = Colors.GREY.value
    K8 = Colors.BROWN.value
    K9 = Colors.GREEN.value

COLORS_HIT_EXT = {**ColorsHit.__members__, **ColorsExt.__members__}