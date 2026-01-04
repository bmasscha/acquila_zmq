from setuptools import setup, find_packages

setup(
    name="acquila_zmq",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        "pyzmq",
    ],
    author="Acquila Team",
    description="A ZMQ-based communication library for Acquila components.",
    keywords="zmq, communication, acquila",
    python_requires=">=3.7",
)
