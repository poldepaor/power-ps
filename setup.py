
import setuptools
with open("README.md", "r") as fh:
    long_description = fh.read()
setuptools.setup(
     name='power-ps',  
     version='0.1',
     scripts=['process_stats.py'] ,
     author="Paul Power",
     author_email="powerpaul91@gmail.com",
     description="A process monitoring tool with graph generation",
     long_description=long_description,
   long_description_content_type="text/markdown",
     url="https://github.com/poldepaor/power-ps",
     packages=setuptools.find_packages(),
     classifiers=[
         "Programming Language :: Python :: 3",
         "License :: OSI Approved :: MIT License",
         "Operating System :: OS Independent",
     ],
 )
