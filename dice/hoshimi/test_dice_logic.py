import unittest

from dice_logic import judge, normalize_input, parse_command, roll_cc


class SequenceRandom:
    def __init__(self, values):
        self.values = iter(values)

    def __call__(self, upper):
        value = next(self.values)
        if not 0 <= value < upper:
            raise AssertionError(f"乱数fixture {value} は0～{upper - 1}の範囲外です")
        return value


class ParseCommandTests(unittest.TestCase):
    def test_basic_command_and_label(self):
        parsed = parse_command("CC<=45 【マイン：離脱する】")
        self.assertEqual(parsed.success_value, 45)
        self.assertEqual(parsed.label, "【マイン：離脱する】")
        self.assertIsNone(parsed.command_bonus)

    def test_fullwidth_and_newline(self):
        parsed = parse_command("ＣＣ＜＝３５\n【判定】")
        self.assertEqual(parsed.success_value, 35)
        self.assertEqual(parsed.label, "【判定】")

    def test_bonus_formats(self):
        self.assertEqual(parse_command("CC(+2)<=50").command_bonus, 2)
        self.assertEqual(parse_command("CC-1<=50").command_bonus, -1)

    def test_rejects_unrelated_text(self):
        with self.assertRaises(ValueError):
            parse_command("1D100<=45")

    def test_uses_last_command_when_paste_was_appended(self):
        parsed = parse_command("CC<=30 【古い判定】 CC<=35 【新しい判定】")
        self.assertEqual(parsed.success_value, 35)
        self.assertEqual(parsed.label, "【新しい判定】")


class JudgeTests(unittest.TestCase):
    def test_normal_levels(self):
        self.assertEqual(judge(45, 1), "クリティカル")
        self.assertEqual(judge(45, 9), "イクストリーム成功")
        self.assertEqual(judge(45, 22), "ハード成功")
        self.assertEqual(judge(45, 45), "レギュラー成功")
        self.assertEqual(judge(45, 46), "失敗")
        self.assertEqual(judge(45, 96), "ファンブル")
        self.assertEqual(judge(50, 99), "失敗")
        self.assertEqual(judge(50, 100), "ファンブル")

    def test_over_100_uses_hoshimichi_rules(self):
        self.assertEqual(judge(105, 5), "クリティカル")
        self.assertEqual(judge(105, 6), "イクストリーム成功")
        self.assertEqual(judge(105, 52), "ハード成功")
        self.assertEqual(judge(105, 53), "自動成功")
        self.assertEqual(judge(105, 100), "ファンブル")


class RollTests(unittest.TestCase):
    def test_regular_roll_matches_bcdice_style(self):
        result = roll_cc(45, "【判定】", 0, SequenceRandom([2, 5]))
        self.assertEqual(result.selected, 25)
        self.assertEqual(
            result.result_line,
            "(1D100<=45) ボーナス・ペナルティダイス[0] ＞ 25 ＞ 25 ＞ レギュラー成功",
        )

    def test_bonus_uses_lowest_candidate(self):
        result = roll_cc(45, "", 1, SequenceRandom([4, 2, 5]))
        self.assertEqual(result.candidates, (45, 25))
        self.assertEqual(result.selected, 25)
        self.assertEqual(result.command, "CC+1<=45")

    def test_penalty_uses_highest_candidate(self):
        result = roll_cc(45, "", -1, SequenceRandom([4, 2, 5]))
        self.assertEqual(result.candidates, (45, 25))
        self.assertEqual(result.selected, 45)
        self.assertEqual(result.command, "CC-1<=45")

    def test_auto_failure_does_not_generate_random_value(self):
        def must_not_run(_upper):
            raise AssertionError("自動失敗で乱数を生成してはいけません")

        result = roll_cc(0, "【不可能な試み】", 0, must_not_run)
        self.assertIsNone(result.selected)
        self.assertIn("自動失敗", result.result_line)


if __name__ == "__main__":
    unittest.main()
