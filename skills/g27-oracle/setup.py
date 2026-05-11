from setuptools import setup, find_packages

setup(
    name='g27-oracle',
    version='1.0.0',
    description='G27 Oracle Autonomous Trading System',
    packages=find_packages(),
    install_requires=[
        'numpy>=1.20.0',
    ],
    python_requires='>=3.8',
    entry_points={
        'console_scripts': [
            'g27-oracle=g27_autonomous:main',
        ],
    },
)
