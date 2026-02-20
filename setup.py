from setuptools import setup, find_packages

setup(
    name="driving_statistics",
    version="0.1.0",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    include_package_data=True,
    install_requires=[
        "PyQt6",
        "pandas",
        # añade otras dependencias de tu proyecto si las hay
    ],
    entry_points={
        "gui_scripts": [
            "driving_statistics = driving_statistics.main:main"
        ]
    },
)