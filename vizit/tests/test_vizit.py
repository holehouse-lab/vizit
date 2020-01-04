"""
Unit and regression test for the vizit package.
"""

# Import package, test suite, and other packages as needed
import vizit
import pytest
import sys

def test_vizit_imported():
    """Sample test, will always pass so long as import statement worked"""
    assert "vizit" in sys.modules
