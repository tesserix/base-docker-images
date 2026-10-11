import pytest

from select_images import select_images


def test_scoped_adk_build_only_adds_its_runtime_dependency():
    assert select_images("python-adk-3.14") == (["python-runtime-3.14"], ["python-adk-3.14"])


def test_explicit_scope_deduplicates_and_trims_input():
    assert select_images("python-adk-3.14, python-runtime-3.14,python-adk-3.14") == (
        ["python-runtime-3.14"], ["python-adk-3.14"]
    )


def test_all_keeps_the_scheduled_complete_rebuild():
    base, derived = select_images("all")
    assert len(base) == 11
    assert derived == ["python-adk-3.13", "python-adk-3.14"]


def test_base_only_selection_does_not_build_adk():
    assert select_images("python-runtime-3.14") == (["python-runtime-3.14"], [])


@pytest.mark.parametrize("selection", ["", "python-adk-3.15", "all,python-adk-3.14"])
def test_invalid_selection_fails_before_builds(selection):
    with pytest.raises(ValueError):
        select_images(selection)
