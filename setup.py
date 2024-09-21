from setuptools import setup, find_packages

if __name__ == "__main__":
    setup(
        name="pigeonote",
        version="0.0.1",
        description="Lightweight rendering and multiplayer framework for pygame(-ce).",
        author="Emanuel Lvovsky",
        packages=find_packages(include="pigeonote.*"),
        install_requires=["pygame-ce>=2.5.0"],
    )
