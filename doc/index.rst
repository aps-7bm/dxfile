======
DXfile
======

Scientific Data Exchange :cite:`DeCarlo:14b` is a set of guidelines for storing
scientific data and metadata in a Hierarchical Data Format 5 :cite:`HDF:01` file. 

HDF5 :cite:`HDF:01` has many important characteristics for scientific data 
storage. It offers platform-independent binary data storage with optional
compression, hierarchical data ordering, and support for MPI-based
parallel computing. Data are stored with alphanumeric tags, so that one
can examine a HDF5 file’s contents with no knowledge of how the file
writing program was coded. Tools for this examination include the
HDF5-supplied command-line utility :cite:`HDF:02` to examine the contents 
of any HDF5 file, or the freely-available Java program :cite:`HDF:03`
to interactively examine the file.

At synchrotron facilities using the EPICS :cite:`EPICS:01` software for area 
detectors :cite:`AD:01` with the NDFileHDF5 plugin :cite:`AD:02`, is possible 
to save Data Exchange files by properly configure the detector and the HDF 
schema attribute files .  
 
This reference guide describes the basic design principles of Data
Exchange, examples of their application, a core reference for guidelines
common to most uses, and coding examples.


Features
--------
* The definition of the scientific data exchange.
* A python interface for writing scientific data exchange files.
* XML attribute files for writers with the EPICS Area Detector HDF plug-in.
 
Highlights
----------
* Based on Hierarchical Data Format 5 (HDF5).
* Focuses on technique rather than instrument descriptions.
* Provenance tracking for understanding analysis steps and results.
* Ease of readability.
   
Contribute
----------

* Documentation: https://github.com/data-exchange/dxfile/tree/master/doc
* Issue Tracker: https://github.com/data-exchange/dxfile/issues
* Source Code: https://github.com/data-exchange/dxfile

Contents
--------

.. toctree::
   :maxdepth: 1
   
   source/introduction
   source/reference
   source/xraytomo
   source/xrayfluo
   source/xraypcs
   source/install
   source/api
   source/demo
   source/credits
   source/appendix


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
