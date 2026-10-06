"""ほしみのダイスロールの入力解析とD100判定処理。"""

from __future__ import annotations

from dataclasses import dataclass
import re
import secrets
from typing import Callable


RandBelow = Callable[[int], int]


@dataclass(frozen=True)
class ParsedCommand:
    success_value: int
    label: str
    command_bonus: int | None


@dataclass(frozen=True)
class DiceResult:
    command: str
    result_line: str
    level: str
    candidates: tuple[int, ...]
    selected: int | None


_COMMAND_RE = re.compile(
    r"^CC(?:(?:\(\s*([+-]?\d+)\s*\))|([+-]?\d+))?\s*<=\s*([+-]?\d+)\s*(.*)$",
    re.IGNORECASE,
)
_COMMAND_START_RE = re.compile(
    r"(?<![A-Z0-9])CC(?:(?:\(\s*[+-]?\d+\s*\))|[+-]?\d+)?\s*<=",
    re.IGNORECASE,
)

_COMMAND_CHARACTERS = str.maketrans(
    "Ｃｃ＜＝＋－（）０１２３４５６７８９",
    "Cc<=+-()0123456789",
)


def normalize_input(text: str) -> str:
    """コマンド用の全角文字だけ整え、日本語本文は保ったまま一行にする。"""
    normalized = text.translate(_COMMAND_CHARACTERS)
    return re.sub(r"\s+", " ", normalized).strip()


def parse_command(text: str) -> ParsedCommand:
    """CC<=45 【判定名】形式を読み取る。"""
    normalized = normalize_input(text)
    starts = [match.start() for match in _COMMAND_START_RE.finditer(normalized)]
    if len(starts) > 1:
        normalized = normalized[starts[-1] :]
    match = _COMMAND_RE.fullmatch(normalized)
    if not match:
        raise ValueError("『CC<=成功値 【判定名】』の形で貼り付けてください。")

    raw_bonus = match.group(1) if match.group(1) is not None else match.group(2)
    command_bonus = int(raw_bonus) if raw_bonus is not None else None
    if command_bonus is not None and abs(command_bonus) > 2:
        raise ValueError("ボーナス・ペナルティは-2～+2にしてください。")

    success_value = int(match.group(3))
    if success_value > 999:
        raise ValueError("成功値は999以下にしてください。")

    label = match.group(4).strip()
    return ParsedCommand(success_value, label, command_bonus)


def format_command(success_value: int, label: str, bonus: int) -> str:
    bonus_text = "" if bonus == 0 else f"{bonus:+d}"
    suffix = f" {label}" if label else ""
    return f"CC{bonus_text}<={success_value}{suffix}"


def judge(success_value: int, rolled: int) -> str:
    """星みちTRPG正本の成功段階を返す。"""
    if success_value <= 0:
        return "自動失敗"

    if success_value >= 100:
        if rolled == 100:
            return "ファンブル"
        critical_max = min(99, max(1, success_value - 100))
        if rolled <= critical_max:
            return "クリティカル"
        if rolled <= success_value // 5:
            return "イクストリーム成功"
        if rolled <= success_value // 2:
            return "ハード成功"
        return "自動成功"

    if rolled == 1:
        return "クリティカル"
    fumble_from = 96 if success_value <= 49 else 100
    if rolled >= fumble_from:
        return "ファンブル"
    if rolled <= success_value // 5:
        return "イクストリーム成功"
    if rolled <= success_value // 2:
        return "ハード成功"
    if rolled <= success_value:
        return "レギュラー成功"
    return "失敗"


def _roll_with_bonus(bonus: int, randbelow: RandBelow) -> tuple[tuple[int, ...], int]:
    """BCDiceのCCと同じく、一の位を共有する候補を作る。"""
    tens = [randbelow(10) * 10 for _ in range(abs(bonus) + 1)]
    ones = randbelow(10)
    candidates = tuple((ten + ones) or 100 for ten in tens)
    selected = min(candidates) if bonus >= 0 else max(candidates)
    return candidates, selected


def roll_cc(
    success_value: int,
    label: str = "",
    bonus: int = 0,
    randbelow: RandBelow = secrets.randbelow,
) -> DiceResult:
    if abs(bonus) > 2:
        raise ValueError("ボーナス・ペナルティは-2～+2にしてください。")

    command = format_command(success_value, label, bonus)
    expression = f"(1D100<={success_value}) ボーナス・ペナルティダイス[{bonus}]"

    if success_value <= 0:
        return DiceResult(
            command=command,
            result_line=f"{expression} ＞ — ＞ — ＞ 自動失敗",
            level="自動失敗",
            candidates=(),
            selected=None,
        )

    candidates, selected = _roll_with_bonus(bonus, randbelow)
    level = judge(success_value, selected)
    candidates_text = ", ".join(str(value) for value in candidates)
    result_line = f"{expression} ＞ {candidates_text} ＞ {selected} ＞ {level}"
    return DiceResult(command, result_line, level, candidates, selected)
