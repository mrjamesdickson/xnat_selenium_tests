from xnat_selenium.browser import BrowserSupport, ChromeSupport, FirefoxSupport


def setup_function():
    BrowserSupport.clear_cache()


def test_browser_caching_variants():
    BrowserSupport.cache_browser("Chrome")
    assert BrowserSupport.cached_browser_support is ChromeSupport
    BrowserSupport.clear_cache()

    BrowserSupport.cache_browser("FF")
    assert BrowserSupport.cached_browser_support is FirefoxSupport
    BrowserSupport.clear_cache()

    BrowserSupport.cache_browser("Google Chrome")
    assert BrowserSupport.cached_browser_support is ChromeSupport


def test_unknown_browser_reports_available_options():
    try:
        BrowserSupport.cache_browser("MicrosoftEdge")
    except RuntimeError as error:
        message = str(error)
        assert "Unknown browser: MicrosoftEdge" in message
        assert "Chrome" in message
        assert "MozillaFirefox" in message
    else:  # pragma: no cover - defensive
        raise AssertionError("Expected RuntimeError to be raised for unknown browser")

