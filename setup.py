import setuptools

with open("requirements.txt", "r") as f:
    install_requires = f.read().splitlines()

setuptools.setup(name="hcx", packages=["migration"], install_requires=install_requires)
