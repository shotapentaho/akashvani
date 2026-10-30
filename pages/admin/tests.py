"""Test-suite runner for the password-protected admin panel."""

import io
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

import streamlit as st


def _run_test_suite():
    """Run the repository unittest suite and return its result and output."""
    project_root = Path(__file__).resolve().parents[2]
    tests_dir = project_root / "tests"
    suite = unittest.defaultTestLoader.discover(str(tests_dir))
    result = unittest.TestResult()
    output = io.StringIO()
    with redirect_stdout(output), redirect_stderr(output):
        suite.run(result)
    return result, output.getvalue()


def show_tests():
    """Display and optionally run the repository test suite."""
    st.header("🧪 Test Suite")
    st.markdown("Run the automated Python tests and review the latest result.")

    if st.button("▶️ Run all tests", type="primary"):
        with st.spinner("Running test suite..."):
            result, output = _run_test_suite()
        st.session_state["admin_test_result"] = {
            "run": result,
            "output": output,
        }

    test_result = st.session_state.get("admin_test_result")
    if not test_result:
        st.info("Run the test suite to capture the latest result.")
        return

    result = test_result["run"]
    total = result.testsRun
    failures = len(result.failures)
    errors = len(result.errors)
    passed = total - failures - errors

    if result.wasSuccessful():
        st.success(f"✅ All {passed} tests pass.")
    else:
        st.error(
            f"❌ {passed} passed, {failures} failed, and {errors} errored "
            f"out of {total} tests."
        )

    if test_result["output"]:
        with st.expander("Test output"):
            st.code(test_result["output"], language="text")
