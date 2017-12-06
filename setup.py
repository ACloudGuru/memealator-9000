from setuptools import setup

setup(
    name='memealator_9000',
    version='0.1',
    description="Memealator 9000 makes memes",
    license="GPLv3+",
    author="Robin Norwood",
    author_email="robin@acloud.guru",
    packages=['memeify'],
    package_data={
        'memeify': ['*.txt', '*.otf']
    },
    url="https://github.com/robin-norwood/memealator-9000",
    setup_requires=['lambda_setuptools'],
    lambda_function="memeify.lambda:lambda_handler",
    install_requires=[
        'requests',
        'markovify',
        'Pillow',
        'flickrapi'
    ]
)
