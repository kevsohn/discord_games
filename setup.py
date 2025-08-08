from setuptools import setup, find_packages

setup(
    name="discord_games",  # This is the package name on PyPI or locally
    version="0.1.0",
    packages=find_packages(),  # Automatically find all packages
    #install_requires=[
    #    "flask>=2.0"
    #    "discord",
    #],
    author="Kevin Sohn",
    description="A suite of simple games to play with ur mates in ur discord server",
    url="https://github.com/kevsohn/discord_games",
)
