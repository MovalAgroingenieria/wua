.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
   :target: http://www.gnu.org/licenses/agpl-3.0-standalone.html
   :alt: License: AGPL-3

=============================================================
Water Users Association: MDM Sensor to Flow Reading Templates
=============================================================

This module provides transformation templates to convert MDM sensor readings
into irrigation and waterpipe flow readings.

Description
===========

This module includes:

* **Sensor Type**: Flowmeter (Totalizer) with m³ as default unit
* **Transformation Templates**:

  * **MDM Sensor to Flow Reading**: Transforms sensor readings to
    ``wua.flowreading`` for irrigation flow meters (intake-based)
  * **MDM Sensor to Waterpipe Flow Reading**: Transforms sensor readings to
    ``wua.waterpipeflowreading`` for waterpipe flow meters

**Key Features**:

* Automatic selection of closest reading for transformation
* Domain filtering by sensor type (Flowmeter Totalizer)
* Additional filtering:

  * Flow readings: Only sensors with ``intake_id`` defined
  * Waterpipe readings: Only sensors with ``waterpipe_id`` defined

* Negative reading detection with automatic routing to
  ``wua.negative.flowreading``
* Field mappings include: flowmeter_id, reading_time (now), volume, instant_flow
* All created readings are marked as non-initialized and non-validated
* Read-only templates and sensor types to prevent accidental modifications
* Uninstall hook for clean removal of all created data

Credits
=======

* Moval Agroingeniería S.L.

Contributors
------------

* Guillermo Amante <gamante@moval.es>
* Juan José Bautista <jjbautista@moval.es>
* Samuel Fernández <sfernandez@moval.es>
* Pablo García <pgarcia@moval.es>
* Alberto Hernández <ahernandez@moval.es>
* Eduardo Iniesta <einiesta@moval.es>
* Jesús Martínez <jmartinez@moval.es>
* Jose Mendez <jjmendez@moval.es>
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
