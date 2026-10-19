from engine.blocks.session_levels import detect_session_levels
from engine.tests.helpers import CASH_RTH, CME_ETH, bar, ny


def test_prior_completed_is_yesterdays_cash_high():
    bars = [
        bar(ny(2024, 1, 8, 9, 30), 100, 104, 99, 103),
        bar(ny(2024, 1, 8, 10, 0), 103, 105, 102, 104),
        bar(ny(2024, 1, 8, 15, 59), 104, 104.5, 103, 104),
        bar(ny(2024, 1, 9, 9, 30), 100, 101, 99, 100),
    ]
    points = detect_session_levels(
        bars, CASH_RTH, levels=["high", "low"], which="prior_completed"
    )
    tuesday = points[3]
    assert tuesday.high == 105
    assert tuesday.low == 99
    assert tuesday.session_start == ny(2024, 1, 8, 9, 30)


def test_developing_high_updates_on_each_close():
    bars = [
        bar(ny(2024, 1, 9, 9, 30), 100, 101, 99, 100),
        bar(ny(2024, 1, 9, 10, 30), 100, 106, 99, 105),
    ]
    points = detect_session_levels(
        bars, CASH_RTH, levels=["high"], which="developing"
    )
    assert points[0].high == 101
    assert points[1].high == 106


def test_asof_excludes_bar_that_opens_at_cutoff():
    bars = [
        bar(ny(2024, 1, 8, 9, 45), 100, 110, 99, 108),
        bar(ny(2024, 1, 8, 10, 0), 108, 120, 107, 119),
        bar(ny(2024, 1, 9, 9, 30), 100, 101, 99, 100),
    ]
    points = detect_session_levels(
        bars,
        CASH_RTH,
        levels=["high"],
        which="prior_completed",
        asof="10:00",
    )
    assert points[2].high == 110


def test_missing_session_window_reports_nothing():
    bars = [bar(ny(2024, 1, 9, 17, 0), 100, 101, 99, 100)]
    points = detect_session_levels(
        bars, CASH_RTH, levels=["high"], which="developing"
    )
    assert points[0].high is None
    assert points[0].session_start is None


def test_prior_day_high_is_prior_cme_equity_session():
    bars = [
        bar(ny(2024, 1, 7, 19, 0), 190, 200, 189, 198),
        bar(ny(2024, 1, 8, 16, 0), 198, 199, 197, 198),
        bar(ny(2024, 1, 8, 19, 0), 198, 201, 197, 200),
    ]
    points = detect_session_levels(
        bars, CME_ETH, levels=["high"], which="prior_completed"
    )
    monday_night = points[2]
    assert monday_night.high == 200
    assert monday_night.session_start == ny(2024, 1, 7, 18, 0)


def test_midpoint_is_average_of_high_and_low():
    bars = [
        bar(ny(2024, 1, 8, 9, 30), 100, 110, 90, 100),
        bar(ny(2024, 1, 9, 9, 30), 100, 101, 99, 100),
    ]
    points = detect_session_levels(
        bars, CASH_RTH, levels=["high", "low", "midpoint"], which="prior_completed"
    )
    assert points[1].midpoint == 100.0


def test_cash_session_end_bar_sees_that_session_as_prior():
    bars = [
        bar(ny(2024, 1, 8, 9, 30), 100, 105, 99, 104),
        bar(ny(2024, 1, 8, 16, 0), 104, 104, 104, 104),
    ]
    points = detect_session_levels(
        bars, CASH_RTH, levels=["high"], which="prior_completed"
    )
    assert points[1].high == 105
