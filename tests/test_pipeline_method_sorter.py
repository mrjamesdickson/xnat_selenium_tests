from xnat_selenium.pipeline import PipelineMethodSorter, UnitTestFilter


def test_pipeline_sorting_matches_reference_behaviour():
    sorter = PipelineMethodSorter()
    launch100 = UnitTestFilter.get_instance("testLaunch100")
    launch55 = UnitTestFilter.get_instance("testLaunch55")
    launch50 = UnitTestFilter.get_instance("testLaunch50")
    launch40 = UnitTestFilter.get_instance("testLaunch40")
    launch30 = UnitTestFilter.get_instance("testLaunch30")
    launch20 = UnitTestFilter.get_instance("testLaunch20")
    launch5 = UnitTestFilter.get_instance("testLaunch5")
    check55 = UnitTestFilter.get_instance("testCheck55")
    check50 = UnitTestFilter.get_instance("testCheck50")
    check40 = UnitTestFilter.get_instance("testCheck40")
    check30 = UnitTestFilter.get_instance("testCheck30")

    ordered = sorter.order_by_job_shop_solution(
        UnitTestFilter.get_dummy_tests(1), 3
    )

    expected_prefix = [
        [launch100, launch55, launch50, launch30, launch40, launch20, launch5],
        [launch100, launch50, launch55, launch30, launch40, launch20, launch5],
    ]
    assert ordered[:7] in expected_prefix
    assert ordered[7:11] == [check50, check55, check30, check40]


def test_missing_check_test_raises_error():
    sorter = PipelineMethodSorter()
    try:
        sorter.order_by_job_shop_solution(UnitTestFilter.get_dummy_tests(2), 3)
    except RuntimeError as error:
        assert (
            str(error)
            == "Could not find corresponding pipeline check test for launch test testLaunch5."
        )
    else:  # pragma: no cover - defensive
        raise AssertionError("Expected RuntimeError to be raised when check test missing")

