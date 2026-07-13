import importlib.util
import json
import pathlib
import sys
import types
import unittest


class _Input:
    def __init__(self, **_kwargs):
        pass


stub = types.ModuleType("cog")
stub.BaseRunner = object
stub.Input = _Input
stub.Path = pathlib.Path
sys.modules.setdefault("cog", stub)
spec = importlib.util.spec_from_file_location("predict", pathlib.Path(__file__).parents[1] / "predict.py")
predict = importlib.util.module_from_spec(spec)
spec.loader.exec_module(predict)


class PredictContractTest(unittest.TestCase):
    def test_two_stem_mp3_command_is_bounded(self):
        args = predict.demucs_args("song.wav", "/tmp/out", "two", "mp3", "htdemucs")
        self.assertIn("--two-stems", args)
        self.assertIn("--mp3-bitrate", args)
        self.assertEqual(args[-1], "song.wav")

    def test_four_stem_wav_omits_conversion_flags(self):
        args = predict.demucs_args("song.wav", "/tmp/out", "four", "wav", "htdemucs")
        self.assertNotIn("--two-stems", args)
        self.assertNotIn("--mp3", args)

    def test_invalid_options_are_rejected(self):
        with self.assertRaises(ValueError):
            predict.demucs_args("song.wav", "/tmp/out", "all", "wav", "htdemucs")

    def test_schema_declares_downloadable_file(self):
        schema = json.loads((pathlib.Path(__file__).parents[1] / "appnz.schema.json").read_text())
        self.assertEqual(schema["outputKind"], "file")


if __name__ == "__main__":
    unittest.main()
