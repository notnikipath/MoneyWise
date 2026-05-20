from shared.moneywise_common import categorization_accuracy, report_load_seconds, transactions_per_second


def test_categorization_accuracy() -> None:
    value = categorization_accuracy(["groceries", "transport"], ["groceries", "housing"])
    assert value == 50.0



def test_report_load_seconds_in_range() -> None:
    value = report_load_seconds(cache_hit_ratio=0.8, row_count=14000)
    assert 0 < value < 4



def test_transactions_per_second() -> None:
    assert transactions_per_second(86_400) == 1.0
