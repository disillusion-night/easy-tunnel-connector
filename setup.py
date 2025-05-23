from setuptools import setup, find_packages

setup(
    name='my-python-project',
    version='0.1.0',
    author='Your Name',
    author_email='your.email@example.com',
    description='A brief description of your project',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    url='https://github.com/yourusername/my-python-project',
    packages=find_packages(where='src'),
    package_dir={'': 'src'},
    install_requires=[
        # 在这里列出项目的依赖项，例如：
        # 'numpy>=1.18.0',
        # 'requests>=2.20.0',
    ],
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.6',
)