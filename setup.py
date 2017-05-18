from setuptools import setup, find_packages

setup(
	name = 'insights_client',
	version = '3.0',
    author="Richard Brantley <rbrantle@redhat.com>",
    author_email="rbrantle@redhat.com",
    license="GPL",
	packages = find_packages(),
	entry_points={'console_scripts': ['insights-client = insights_client:main']},
	py_modules=['__main__'],
	include_package_data=True
	)