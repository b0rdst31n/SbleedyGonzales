from setuptools import setup, find_packages

setup(
    name='SbleedyGonzales',
    version='0.1',
    packages=find_packages(),
    entry_points={
        'console_scripts': [
            'sbleedy = sbleedyCLI.sbleedy:main',
        ],
    },
    install_requires=[
        'pyyaml',
        'rich',
        'setuptools',
        'pyserial',
        'psutil',
        'tqdm',
        'scapy'
    ],
)
