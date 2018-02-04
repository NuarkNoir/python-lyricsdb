from cx_Freeze import setup, Executable

setup(
    name = "LyricsDB",
    version = "0.1",
    description = "LyricsDB Grabber",
    executables = [Executable("loader.py")]
)
