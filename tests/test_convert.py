import pytest
import platform
from subprocess import CalledProcessError
from pathlib import Path
import pyperclip
from unittest.mock import patch
from symphovert.exceptions import SymphonyError

try:
    from symphovert.convert import (
        copypaste,
        save_as,
        find_symphony,
        symphony_convert,
    )
except SymphonyError as error:
    pytest.skip(
        f"Symphony not imported due to {error}", allow_module_level=True
    )


@pytest.fixture()
def reset_clipboard():
    yield
    pyperclip.copy("")


class TestGUIAutomation:
    def test_copypaste(self, reset_clipboard):
        copypaste("hello")
        assert pyperclip.paste() == "hello"

    def test_save_as(self, reset_clipboard):
        save_as("test")
        assert pyperclip.paste() == "test"


class TestSymphony:
    def test_find_symphony(self):
        with patch("platform.system", return_value="Linux"):
            with pytest.raises(SymphonyError):
                find_symphony()
        # Since conversion with Symphony only works on Windows,
        # these tests also only work on Windows.
        if platform.system() == "Windows":
            try:
                result = find_symphony()
            # In case Symphony is not installed
            except SymphonyError as error:
                assert "Could not find IBM Symphony with error:" in str(error)
            else:
                assert result
            # Force subprocess.run() to raise
            with patch(
                "subprocess.run",
                side_effect=CalledProcessError(
                    returncode=1, cmd="Fail", stderr=b"Fail"
                ),
            ):
                with pytest.raises(SymphonyError):
                    find_symphony()

    def test_symphony_convert(self, temp_dir, reset_clipboard):
        # Check if Symphony is installed
        if platform.system() == "Windows":
            try:
                find_symphony()
            # In case Symphony is not installed
            except SymphonyError as error:
                assert "Could not find IBM Symphony with error:" in str(error)
            else:
                with pytest.raises(SymphonyError):
                    Path(temp_dir).joinpath("file.odt").touch()
                    symphony_convert(Path("file"), Path(temp_dir))
                # Patch return value of find_symphony to failing command
                with patch(
                    "convertool.symphony.find_symphony", return_value="fail!"
                ):
                    with pytest.raises(SymphonyError):
                        symphony_convert(Path("file"), Path(temp_dir))
