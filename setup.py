import subprocess
from setuptools import setup, find_packages, Command
from setuptools.command.install import install
from subprocess import check_call

class InitSubmodules(Command):
    """Custom command to initialize and update git submodules."""
    description = 'Initialize and update submodules'
    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        try:
            subprocess.check_call(['git', 'submodule', 'update', '--init', '--recursive'])
        except subprocess.CalledProcessError as e:
            print(f"Error initializing submodules: {e}")
            exit(1)

class CustomInstallCommand(install):
    """Customized install command to initialize submodules and install all dependencies."""
    def run(self):
        self.run_command('init_submodules') 
        install.run(self) 
        check_call(['pip', 'install', 'bluing', '--no-dependencies'])

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
        'nrfutil',
        'pyserial',
        'psutil',
        'tqdm',
        'scapy',
        'colorama',
        'tabulate',
        'bleak'
    ],
    cmdclass={
        'init_submodules': InitSubmodules,
        'install': CustomInstallCommand,
    },
)
