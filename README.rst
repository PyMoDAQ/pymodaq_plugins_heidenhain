pymodaq_plugins_heidenhain
##########################

.. image:: https://img.shields.io/pypi/v/pymodaq_plugins_heidenhain.svg
   :target: https://pypi.org/project/pymodaq_plugins_heidenhain/
   :alt: Latest Version

.. image:: https://readthedocs.org/projects/pymodaq/badge/?version=latest
   :target: https://pymodaq.readthedocs.io/en/stable/?badge=latest
   :alt: Documentation Status

.. image:: https://github.com/jerlfan/pymodaq_plugins_heidenhain/actions/workflows/tests.yml/badge.svg
    :target: https://github.com/jerlfan/pymodaq_plugins_heidenhain/actions/workflows/tests.yml

PyMoDAQ plugins for HEIDENHAIN encoders read through the IK 220 PC counter card, such as the LC 483 absolute linear
encoder (EnDat interface). This branch targets **PyMoDAQ 5.3.x** (Python 3.10 to 3.13).

Authors
=======

* Jérémie Margueritat (jeremie.margueritat@univ-lyon1.fr)

Instruments
===========

Below is the list of instruments included in this plugin

Viewer0D
++++++++

* **IK220**: absolute position of an EnDat encoder connected to a HEIDENHAIN IK 220 card

Installation instructions
=========================

* PyMoDAQ 5.3.x on Windows 64 bits.
* HEIDENHAIN IK 220 driver and DLL (``IK220Dll64.dll``), package 739275-05 for Windows 10 64 bits. Compatibility
  with Windows 11 has not been checked yet.
* Not tested on hardware yet.

Development
===========

* Install your plugin in editable mode: ``pip install -e .``
* Check it, without any hardware: ``check_plugin`` (and ``pytest tests``)
* If you use an AI coding assistant, point it to ``AGENTS.md``: it describes the patterns to follow for instrument
  plugins, Dashboard extensions and standalone apps.
