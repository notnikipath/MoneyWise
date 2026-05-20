from datetime import UTC, datetime

from shared.moneywise_common import auto_categorize, monthly_required_saving, position_return_pct


def test_auto_categorize_detects_keywords() -> None:
    category, auto = auto_categorize("Taxi to airport", "CityTaxi")
    assert category == "transport"
    assert auto is True



def test_monthly_required_saving_positive() -> None:
    deadline = datetime.now(UTC).date().replace(year=datetime.now(UTC).year + 1)
    required = monthly_required_saving(target_amount=240000, current_amount=120000, deadline=deadline)
    assert required > 0



def test_position_return_pct() -> None:
    result = position_return_pct(quantity=10, average_price=100, current_price=110)
    assert result == 10.0
