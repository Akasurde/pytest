import re
import warnings
from unittest import mock

import pytest
from _pytest import deprecated
from _pytest.compat import legacy_path
from _pytest.pytester import Pytester
from pytest import PytestDeprecationWarning


@pytest.mark.parametrize("attribute", pytest.collect.__all__)  # type: ignore
# false positive due to dynamic attribute
def test_pytest_collect_module_deprecated(attribute) -> None:
    with pytest.warns(DeprecationWarning, match=attribute):
        getattr(pytest.collect, attribute)


@pytest.mark.parametrize("plugin", sorted(deprecated.DEPRECATED_EXTERNAL_PLUGINS))
@pytest.mark.filterwarnings("default")
def test_external_plugins_integrated(pytester: Pytester, plugin) -> None:
    pytester.syspathinsert()
    pytester.makepyfile(**{plugin: ""})

    with pytest.warns(pytest.PytestConfigWarning):
        pytester.parseconfig("-p", plugin)


def test_fillfuncargs_is_deprecated() -> None:
    with pytest.warns(
        pytest.PytestDeprecationWarning,
        match=re.escape(
            "pytest._fillfuncargs() is deprecated, use "
            "function._request._fillfixtures() instead if you cannot avoid reaching into internals."
        ),
    ):
        pytest._fillfuncargs(mock.Mock())


def test_fillfixtures_is_deprecated() -> None:
    import _pytest.fixtures

    with pytest.warns(
        pytest.PytestDeprecationWarning,
        match=re.escape(
            "_pytest.fixtures.fillfixtures() is deprecated, use "
            "function._request._fillfixtures() instead if you cannot avoid reaching into internals."
        ),
    ):
        _pytest.fixtures.fillfixtures(mock.Mock())


def test_minus_k_dash_is_deprecated(pytester: Pytester) -> None:
    threepass = pytester.makepyfile(
        test_threepass="""
        def test_one(): assert 1
        def test_two(): assert 1
        def test_three(): assert 1
    """
    )
    result = pytester.runpytest("-k=-test_two", threepass)
    result.stdout.fnmatch_lines(["*The `-k '-expr'` syntax*deprecated*"])


def test_minus_k_colon_is_deprecated(pytester: Pytester) -> None:
    threepass = pytester.makepyfile(
        test_threepass="""
        def test_one(): assert 1
        def test_two(): assert 1
        def test_three(): assert 1
    """
    )
    result = pytester.runpytest("-k", "test_two:", threepass)
    result.stdout.fnmatch_lines(["*The `-k 'expr:'` syntax*deprecated*"])


def test_fscollector_gethookproxy_isinitpath(pytester: Pytester) -> None:
    module = pytester.getmodulecol(
        """
        def test_foo(): pass
        """,
        withinit=True,
    )
    assert isinstance(module, pytest.Module)
    package = module.parent
    assert isinstance(package, pytest.Package)

    with pytest.warns(pytest.PytestDeprecationWarning, match="gethookproxy"):
        package.gethookproxy(pytester.path)

    with pytest.warns(pytest.PytestDeprecationWarning, match="isinitpath"):
        package.isinitpath(pytester.path)

    # The methods on Session are *not* deprecated.
    session = module.session
    with warnings.catch_warnings(record=True) as rec:
        session.gethookproxy(pytester.path)
        session.isinitpath(pytester.path)
    assert len(rec) == 0


def test_strict_option_is_deprecated(pytester: Pytester) -> None:
    """--strict is a deprecated alias to --strict-markers (#7530)."""
    pytester.makepyfile(
        """
        import pytest

        @pytest.mark.unknown
        def test_foo(): pass
        """
    )
    result = pytester.runpytest("--strict")
    result.stdout.fnmatch_lines(
        [
            "'unknown' not found in `markers` configuration option",
            "*PytestDeprecationWarning: The --strict option is deprecated, use --strict-markers instead.",
        ]
    )


def test_yield_fixture_is_deprecated() -> None:
    with pytest.warns(DeprecationWarning, match=r"yield_fixture is deprecated"):

        @pytest.yield_fixture
        def fix():
            assert False


def test_private_is_deprecated() -> None:
    class PrivateInit:
        def __init__(self, foo: int, *, _ispytest: bool = False) -> None:
            deprecated.check_ispytest(_ispytest)

    with pytest.warns(
        pytest.PytestDeprecationWarning, match="private pytest class or function"
    ):
        PrivateInit(10)

    # Doesn't warn.
    PrivateInit(10, _ispytest=True)


def test_raising_unittest_skiptest_during_collection_is_deprecated(
    pytester: Pytester,
) -> None:
    pytester.makepyfile(
        """
        import unittest
        raise unittest.SkipTest()
        """
    )
    result = pytester.runpytest()
    result.stdout.fnmatch_lines(
        [
            "*PytestDeprecationWarning: Raising unittest.SkipTest*",
        ]
    )


def test_hookproxy_warnings_for_fspath(pytestconfig, tmp_path, request):
    path = legacy_path(tmp_path)

    PATH_WARN_MATCH = r".*path: py\.path\.local\) argument is deprecated, please use \(fspath: pathlib\.Path.*"

    with pytest.warns(PytestDeprecationWarning, match=PATH_WARN_MATCH) as r:
        pytestconfig.hook.pytest_ignore_collect(
            config=pytestconfig, path=path, fspath=tmp_path
        )
    (record,) = r
    assert record.filename == __file__
    assert record.lineno == 166

    with pytest.warns(PytestDeprecationWarning, match=PATH_WARN_MATCH) as r:
        request.node.ihook.pytest_ignore_collect(
            config=pytestconfig, path=path, fspath=tmp_path
        )
    (record,) = r
    assert record.filename == __file__
    assert record.lineno == 174
    pytestconfig.hook.pytest_ignore_collect(config=pytestconfig, fspath=tmp_path)
    request.node.ihook.pytest_ignore_collect(config=pytestconfig, fspath=tmp_path)
