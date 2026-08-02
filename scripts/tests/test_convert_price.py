from convert_price import format_price
from convert_price import process_file as convert_price_process_file

from .helpers import make_json_file


class TestFormatPrice:
    def test_zero(self):
        assert format_price(0) == "0 cent"

    def test_cents_only(self):
        assert format_price(25) == "25 cent"

    def test_dollars_only(self):
        assert format_price(1000) == "10 USD"

    def test_mixed(self):
        assert format_price(125) == "1 USD 25 cent"

    def test_kusd(self):
        assert format_price(222000) == "2 kUSD 220 USD"

    def test_exact_kusd(self):
        assert format_price(500000) == "5 kUSD"

    def test_dollars_and_cents(self):
        assert format_price(305) == "3 USD 5 cent"


class TestRegexReplacement:
    def test_replaces_price_in_file(self, tmp_path):
        p = make_json_file(tmp_path, {"id": "item1", "price": 150, "name": "test"})
        result = convert_price_process_file(p, p, backup=False)
        assert result.processed == 1
        content = p.read_text()
        assert '"price": "1 USD 50 cent"' in content

    def test_replaces_price_postapoc(self, tmp_path):
        p = make_json_file(tmp_path, {"id": "item1", "price_postapoc": 200})
        result = convert_price_process_file(p, p, backup=False)
        assert result.processed == 1
        content = p.read_text()
        assert '"price_postapoc": "2 USD"' in content

    def test_no_match_skips(self, tmp_path):
        p = make_json_file(tmp_path, {"name": "test"})
        result = convert_price_process_file(p, p, backup=False)
        assert result.processed == 0
        assert result.skipped == 1
        assert result.has_errors is False
