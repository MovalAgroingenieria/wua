========================================
WUA: SCADA Mula Waterconnection Readings
========================================

This module integrates WUA waterconnection readings with the
``remotecontrol_scada_mula`` SQL remote control.

It adds support to import the closest monthly counter reading from
SCADA Mula ``consumos_MM`` tables into WUA watermeter readings.

Overview
========

- Depends on ``remotecontrol_scada_mula`` and ``base_wua_remotecontrol_rest``.
- Adds a new telecontrol association on water connections: ``scada_mula``.
- Matches each water connection against SCADA rows using:

  - ``sector``
  - ``arqueta``
  - ``parcela``

- Uses ``contadorFinal`` as imported reading volume.
- Uses hydrological year database naming:

  - ``<database_prefix>_<year1>_<year2_short>``
  - Example: ``mula_2025_26``

- Reads monthly table for current execution month:

  - ``consumos_01``, ``consumos_02``, ..., ``consumos_12``

- Selects the closest day to execution day:

  - Prefer nearest previous/equal day
  - Otherwise nearest next day

Configuration
=============

1. Install module ``wua_remotecontrol_scada_mula``.
2. Configure remote control ``SCADA Mula`` in module
   ``remotecontrol_scada_mula`` with valid ``connection_params``.
3. On each target ``wua.waterconnection``:

   - Set ``telecontrol_associated`` to ``scada_mula``
   - Fill mapping fields:

     - ``scada_mula_sector``
     - ``scada_mula_arqueta``
     - ``scada_mula_parcela``

4. Ensure import flag is enabled:

   - ``import_from_readings_scada_mula`` = True

Technical Notes
===============

- The action execution context from ``base_remotecontrol`` is used.
- SQL access is performed through injected helpers:

  - ``sql_connect``
  - ``sql_execute``
  - ``sql_fetchone``
  - ``sql_close``

- No direct connector import is required in this module action code.

Default Flags
=============

The module defines these default flags in ``ir.values``:

- ``import_from_readings_scada_mula``: True
- ``import_from_waterconnection_scada_mula``: False
- ``import_from_irrigationshed_scada_mula``: False
- ``import_from_hydraulicsector_scada_mula``: False

Known Assumptions
=================

This module expects SCADA monthly tables to expose at least these columns:

- ``dia``
- ``contadorFinal``
- ``sector``
- ``arqueta``
- ``parcela``

Optional fallback column:

- ``toma``

Bug Tracker
===========

Bugs are tracked on GitHub Issues for the Moval WUA platform repositories.

When reporting an issue, please include:

- module name: ``wua_remotecontrol_scada_mula``
- database name and environment
- exact remotecontrol action/procedure executed
- full traceback and relevant ``mail.message`` logs

Credits
=======

* Moval Agroingeniería

Contributors
------------
* Guillermo Amante <gamante@moval.es>
* Juan José Bautista <jjbautista@moval.es>
* Samuel Fernández <sfernandez@moval.es>
* Pablo García <pgarcia@moval.es>
* Alberto Hernández <ahernandez@moval.es>
* Eduardo Iniesta <einiesta@moval.es>
* Jesús Martínez <jmartinez@moval.es>
* José Javier Méndez <jjmendez@moval.es>
* Miguel Mora <mmora@moval.es>
* Miguel Ángel Rodríguez <marodriguez@moval.es>
* Juanu Sandoval <jsandoval@moval.es>
* Salvador Sánchez <ssanchez@moval.es>
* Jorge Vera <jvera@moval.es>

Maintainer
----------

.. image:: https://raw.githubusercontent.com/MovalAgroingenieria/public-assets/master/logos/logo_moval_small.png
   :target: http://moval.es
   :alt: Moval Agroingeniería

This module is maintained by Moval Agroingeniería.
