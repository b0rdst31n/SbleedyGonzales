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

            pybluez_path = os.path.join('helpers', 'pybluez')
            if os.path.isdir(pybluez_path):
                os.chdir(pybluez_path)
                subprocess.check_call(['python', 'setup.py', 'install'])
            else:
                print(f"Error: {pybluez_path} directory not found.")
                exit(1)
        except subprocess.CalledProcessError as e:
            print(f"Error during submodule initialization or installation: {e}")
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
        'bleak',
        'pwntools'
    ],
    cmdclass={
        'init_submodules': InitSubmodules,
        'install': CustomInstallCommand,
    },
)
