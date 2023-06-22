from setuptools import setup, find_packages

p_version = "0.0.1"

with open("README.md") as f:
    long_description = f.read()


setup(
    name="postgre-test-container",
    version=p_version,
    author="Ivan Malmstine",
    author_email="ivan@malmstine.com",
    packages=find_packages(),
    url="https://github.com/malmstine/postgre-test-container",
    license="MIT",
    description="Temporary test docker container",
    long_description=long_description,
    long_description_content_type="text/markdown",
    keywords=[
        "docker",
        "postgreSQL",
        "postgre",
        "test",
        "test container"
    ]
)
