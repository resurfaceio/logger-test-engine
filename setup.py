from setuptools import find_packages, setup


def read_file(name):
    with open(name) as fd:
        return fd.read()


setup(
    name="test-resurface",
    version="0.1.0",
    description=("Resurfaceio integration test "),
    author="Anish Shrestha",
    author_email="hello@anyesh.xyz",
    packages=find_packages(exclude=["tests"]),
    install_requires=read_file("requirements.txt").splitlines(),
    entry_points={
        "console_scripts": ["test-resurface=src.engine:cli"],
    },
    package_data={"": ["config.yaml", "README.md", "API.yaml"]},
    include_package_data=True,
    zip_safe=False,
)