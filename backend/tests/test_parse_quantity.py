"""Tests for parse_quantity — the most fragile function in the codebase.

Covers: plain integers, decimals, unicode fractions (¼ ½ ¾ ⅓ ⅔),
mixed numbers ("1 1/2"), ASCII fractions ("3/4"), leading qty in strings,
approx flags for weight/volume units, and edge cases.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.api.routes.meal_plans import parse_quantity


class TestParseQuantityPlainNumbers:
    def test_integer(self):
        assert parse_quantity("4") == (4.0, False)

    def test_decimal(self):
        assert parse_quantity("1.5") == (1.5, False)

    def test_zero(self):
        assert parse_quantity("0") == (0.0, False)

    def test_large_number(self):
        assert parse_quantity("100") == (100.0, False)


class TestParseQuantityUnicodeFractions:
    def test_half(self):
        assert parse_quantity("½") == (0.5, False)

    def test_quarter(self):
        assert parse_quantity("¼") == (0.25, False)

    def test_three_quarters(self):
        assert parse_quantity("¾") == (0.75, False)

    def test_third(self):
        val, approx = parse_quantity("⅓")
        assert abs(val - 1/3) < 0.001

    def test_two_thirds(self):
        val, approx = parse_quantity("⅔")
        assert abs(val - 2/3) < 0.001

    def test_mixed_number_unicode(self):
        """'1½' should parse as 1.5"""
        assert parse_quantity("1½") == (1.5, False)

    def test_mixed_number_unicode_with_space(self):
        """'1 ½' — space before fraction"""
        assert parse_quantity("1 ½") == (1.5, False)

    def test_integer_plus_unicode_fraction(self):
        assert parse_quantity("3¾") == (3.75, False)


class TestParseQuantityAsciiFractions:
    def test_half_ascii(self):
        assert parse_quantity("1/2") == (0.5, False)

    def test_three_quarters_ascii(self):
        assert parse_quantity("3/4") == (0.75, False)

    def test_mixed_number_ascii(self):
        """'1 1/2' should parse as 1.5"""
        assert parse_quantity("1 1/2") == (1.5, False)

    def test_mixed_number_no_space(self):
        """'11/2' — ambiguous but should parse as mixed number"""
        val, approx = parse_quantity("11/2")
        # Could be 1 + 1/2 = 1.5 or 11/2 = 5.5
        # The regex matches mixed: (1)(1/2) = 1.5
        assert val is not None


class TestParseQuantityApproxUnits:
    def test_cup(self):
        val, approx = parse_quantity("2 cup")
        assert val == 2.0
        assert approx is True

    def test_tablespoon(self):
        val, approx = parse_quantity("3 tbsp")
        assert val == 3.0
        assert approx is True

    def test_pound(self):
        val, approx = parse_quantity("1 lb")
        assert val == 1.0
        assert approx is True

    def test_ounce(self):
        val, approx = parse_quantity("8 oz")
        assert val == 8.0
        assert approx is True

    def test_milliliter(self):
        val, approx = parse_quantity("500 ml")
        assert val == 500.0
        assert approx is True

    def test_count_no_approx(self):
        val, approx = parse_quantity("4 slices")
        assert val == 4.0
        assert approx is False


class TestParseQuantityUnparseable:
    def test_none(self):
        assert parse_quantity(None) == (None, True)

    def test_empty(self):
        assert parse_quantity("") == (None, True)

    def test_to_taste(self):
        assert parse_quantity("to taste") == (None, True)

    def test_optional(self):
        assert parse_quantity("optional") == (None, True)

    def test_dash(self):
        assert parse_quantity("dash") == (None, True)

    def test_pinch(self):
        assert parse_quantity("pinch") == (None, True)

    def test_as_needed(self):
        assert parse_quantity("as needed") == (None, True)

    def test_garbage_string(self):
        val, approx = parse_quantity("asjkdhf")
        assert val is None
        assert approx is True


class TestParseQuantityEdgeCases:
    def test_whitespace_padding(self):
        assert parse_quantity("  4  ") == (4.0, False)

    def test_case_insensitive(self):
        val, approx = parse_quantity("2 CUP")
        assert val == 2.0
        assert approx is True

    def test_unicode_fraction_with_unit(self):
        """'½ cup' should parse as 0.5, approx=True"""
        val, approx = parse_quantity("½ cup")
        assert val == 0.5
        assert approx is True

    def test_mixed_with_unit(self):
        """'1 1/2 lb' should parse as 1.5, approx=True"""
        val, approx = parse_quantity("1 1/2 lb")
        assert val == 1.5
        assert approx is True
