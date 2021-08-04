from setuptools import setup


def requirements():
  with open("requirements.txt") as f:
    return f.read().splitlines()


setup(
  name="Police-Supply-Demand",
  packages=["crims"],
  scripts=[
    "netlogo_adapter.py"
  ],
  include_package_data=True,
  zip_safe=False,
  install_requires=requirements(),
)
