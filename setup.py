import os
import subprocess
from setuptools import setup, find_packages, Command
from setuptools.command.install import install

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

class InstallSubmoduleDependencies(Command):
    """Custom command to install dependencies for the Python 2.7 submodule."""
    description = 'Install dependencies for the Python 2.7 submodule'
    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        venv2_activate_path = 'venv2/bin/activate'
        
        if not os.path.exists(venv2_activate_path):
            print("Python 2.7 virtual environment (venv2) not found!")
            exit(1)
        
        try:
            subprocess.check_call([
                'bash', '-c',
                f'source {venv2_activate_path} && pip install -r modules/sweyntooth/requirements.txt'
            ])
        except subprocess.CalledProcessError as e:
            print(f"Error installing submodule dependencies: {e}")
            exit(1)

class CustomInstallCommand(install):
    """Customized install command to initialize submodules and install all dependencies."""
    def run(self):
        self.run_command('init_submodules') 
        #self.run_command('install_submodule_dependencies') 
        install.run(self) 

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
        'bluepy'
    ],
    cmdclass={
        'init_submodules': InitSubmodules,
        #'install_submodule_dependencies': InstallSubmoduleDependencies,
        'install': CustomInstallCommand,
    },
)
