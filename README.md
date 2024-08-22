sPOD - The shifted  proper orthogonal decomposition
===================================================
This is a python tool for decomposing and model reduction for multiple transport
phenomena.
It is written in python3.

![sPOD-example](https://github.com/MOR-transport/sPOD/blob/sPOD-main/sPOD_vortex-shedding.gif)

Installation with Conda
------------------------
#. For a easy installation of the sPOD library use conda with the following command:

.. code-block:: bash

    conda env create -f sPOD-env.yml

This will create an environment called sPOD in which you can run all the examples.
For activating the environment use:

.. code-block:: bash

    conda activate sPOD

before executing the examples in the example folder.

Requirements
-------------

#. In order to run `sPOD` package, the following libraries are required:
 * Numpy
 * Matplotlib
 * Scikit-learn
 * SciPy

#. The documentation generator relies on Sphinx.
   The latter generator an be installed, for instance, using pip with the
   following command

.. code-block:: bash

    python3 -m pip install sphinx pydata-sphinx-theme

 
Usage of Library
-----------------
Clone the repository and use it in your python code

.. code-block:: python

    import sPOD_tools

or use instead

.. code-block:: python

    from sPOD_tools import sPOD

Documentation
-------------
The documentation can be generated by running the `Makefile` in the folder
`doc/`.

#. For example, the following command generates the documentation in HTML format

.. code-block:: bash

    make html


#. To read the documentation, open the file `build/html.index.html` in your
   favourite browser.
    
Examples
--------
For simple examples, you can check out the python scripts in the `example/`
folder. To download the wildlandfire and two cylinders test case from [![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.13355796.svg)](https://doi.org/10.5281/zenodo.13355796) just use the command:

.. code-block:: bash

    make download

After you can run the individual examples by executing them using python or using the command:

.. code-block:: bash

    make

to run all the examples in the folder. The *synthetic_examples_1D.py* implements the basic functionality and a good introduction start understanding the implementation.

**BE AWARE THAT THIS CODE IS STILL UNDER DEVELOPMENT. FUTURE DEVS WILL INCREASE PERFORMANCE AND USABILITY**
