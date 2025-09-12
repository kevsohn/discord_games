from setuptools import setup, find_packages

with open('requirements.txt') as f:
    requirements = f.read().splitlines()

setup(
    name="discord_games",  # This is the package name on PyPI or locally
    version="0.1.0",
    packages=find_packages(),
    include_package_data=True,
    install_requires=requirements,
    python_requires=">=3.12",
    author="Kevin Sohn",
    description="A suite of simple games to play with ur mates in ur discord server",
    url="https://github.com/kevsohn/discord_games",
)
