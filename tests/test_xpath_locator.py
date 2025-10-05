from xnat_selenium.xpath import XpathLocator, XpathUnion


def test_join_sublocator_handles_relative_paths():
    base = XpathLocator("//div[@id='archive']")
    assert base.join_sublocator("./div[3]").expression == "//div[@id='archive']/div[3]"
    assert base.join_sublocator("/div[3]").expression == "//div[@id='archive']/div[3]"


def test_nth_instance_wraps_expression():
    assert XpathLocator("//div/div/div").nth_instance(3).expression == "(//div/div/div)[3]"


def test_parent_helpers():
    locator = XpathLocator("//div/div")
    assert locator.parent().expression == "//div/div/.."
    assert locator.grandparent().expression == "//div/div/../.."


def test_union_helpers():
    union = XpathUnion(
        [XpathLocator("//div"), XpathLocator("//div/span"), XpathLocator("//span/div")]
    )
    assert union.expression == "(//div | //div/span | //span/div)"


def test_union_sublocators():
    base = XpathLocator("//div")
    result = base.union_sublocators(
        [XpathLocator("./div/span"), XpathLocator("./table/tbody")]
    )
    assert result.expression == "(//div/div/span | //div/table/tbody)"

