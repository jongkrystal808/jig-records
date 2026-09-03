from __future__ import annotations

import os
import unittest
from unittest.mock import patch

import main


class MainLauncherTests(unittest.TestCase):
    def test_reload_can_be_disabled_explicitly(self) -> None:
        with patch.dict(os.environ, {"UVICORN_RELOAD": "0"}, clear=False):
            self.assertFalse(main.should_reload_server())

    def test_reload_rejects_invalid_value(self) -> None:
        with patch.dict(os.environ, {"UVICORN_RELOAD": "sometimes"}, clear=False):
            with self.assertRaisesRegex(RuntimeError, "UVICORN_RELOAD"):
                main.should_reload_server()

    def test_reload_forces_single_worker(self) -> None:
        with patch.dict(os.environ, {"UVICORN_WORKERS": "4"}, clear=False):
            self.assertEqual(main.uvicorn_worker_count(reload_enabled=True), 1)
            self.assertEqual(main.uvicorn_worker_count(reload_enabled=False), 4)

    def test_worker_count_must_be_positive_integer(self) -> None:
        for value in ("0", "invalid"):
            with self.subTest(value=value):
                with patch.dict(os.environ, {"UVICORN_WORKERS": value}, clear=False):
                    with self.assertRaisesRegex(RuntimeError, "UVICORN_WORKERS"):
                        main.uvicorn_worker_count(reload_enabled=False)


if __name__ == "__main__":
    unittest.main()
