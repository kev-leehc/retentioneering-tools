from __future__ import annotations

import pandas as pd

from retentioneering.tooling.describe.describe import Describe
from tests.tooling.fixtures.describe import test_stream
from tests.tooling.fixtures.describe_corr import basic_corr, session_corr


class TestDescribe:
    def test_describe__basic(self, test_stream, basic_corr):
        de = Describe(test_stream)
        result = de._describe()
        expected_df = basic_corr
        assert pd.testing.assert_frame_equal(result, expected_df) is None

    def test_describe__session(self, test_stream, session_corr):
        de = Describe(test_stream.split_sessions(session_cutoff=(10, "m")))
        result = de._describe()
        expected_df = session_corr
        assert pd.testing.assert_frame_equal(result, expected_df) is None
