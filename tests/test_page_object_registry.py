from xnat_selenium.page_registry import (
    PageObjectRegistry,
    XnatPageComponent,
    Xnat_1_6dev,
    Xnat_1_7_2,
    Xnat_1_7_3,
    Xnat_1_7_4,
    Xnat_1_7_5,
    Xnat_1_7_5_2,
    Xnat_1_7_7,
)


PageObjectRegistry.clear()


@PageObjectRegistry.register
class DummyPageComponent(XnatPageComponent):
    handled_versions = (Xnat_1_7_7, Xnat_1_7_5_2)


@PageObjectRegistry.register
class DummyPageComponent1_7_5(DummyPageComponent):
    handled_versions = (Xnat_1_7_5, Xnat_1_7_4)


@PageObjectRegistry.register
class DummyPageComponent1_7_3(DummyPageComponent1_7_5):
    handled_versions = (Xnat_1_7_3, Xnat_1_7_2)


@PageObjectRegistry.register
class DummyPageComponent1_6(DummyPageComponent1_7_3):
    handled_versions = (Xnat_1_6dev,)


def test_page_object_lookup_prefers_most_specific_version():
    assert (
        PageObjectRegistry.get_page_object(DummyPageComponent, Xnat_1_7_7)
        is DummyPageComponent
    )
    assert (
        PageObjectRegistry.get_page_object(DummyPageComponent, Xnat_1_7_5_2)
        is DummyPageComponent
    )
    assert (
        PageObjectRegistry.get_page_object(DummyPageComponent, Xnat_1_7_5)
        is DummyPageComponent1_7_5
    )
    assert (
        PageObjectRegistry.get_page_object(DummyPageComponent, Xnat_1_7_4)
        is DummyPageComponent1_7_5
    )
    assert (
        PageObjectRegistry.get_page_object(DummyPageComponent, Xnat_1_7_3)
        is DummyPageComponent1_7_3
    )
    assert (
        PageObjectRegistry.get_page_object(DummyPageComponent, Xnat_1_7_2)
        is DummyPageComponent1_7_3
    )
    assert (
        PageObjectRegistry.get_page_object(DummyPageComponent, Xnat_1_6dev)
        is DummyPageComponent1_6
    )

