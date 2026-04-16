.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
   :target: http://www.gnu.org/licenses/agpl-3.0-standalone.html
   :alt: License: AGPL-3

================================================
Water Users Association Irrigation (Spherag API)
================================================

Interface of Moval Water Management with the Spherag
remote monitoring system, based on a REST API

Description
===========

Interface of Moval Water Management with the Spherag remote monitoring system,
based on a REST API, and with the functional schema of the
base_wua_remotecontrol_rest module.

Spherag is a cloud-based remote monitoring and control system for
irrigation installations, providing real-time meter readings and
device management through an Atlas platform.

This module enables automatic synchronization of:

* Census data (irrigation sheds, water connections, water meters) from
  Spherag discovery JSON exports
* Reading data from configured water meters through the Spherag monitoring API
* Two-phase integration: discovery phase for infrastructure creation, and
  synchronized reading import phase

Configuration
=============

After module installation, configure the following in
Irrigation Management > Configuration:

1. Enable Remote Control (base_wua_remotecontrol_rest)
2. Set Spherag Application URL (for launching native monitoring dashboard)
3. Set Default Hydraulic Sector for automatic irrigation shed creation
4. Enable import flags as needed:
   - Import from readings (default: enabled)
   - Import from waterconnection
   - Import from irrigationshed (default: enabled)
   - Import from hydraulic sector (default: enabled)

Usage
=====

**Census Import (Discovery)**

1. Export Spherag discovery JSON from Spherag platform
2. Go to Remote Control > Import Data > Water Connection
3. Select Spherag and upload the JSON discovery file
4. Module creates irrigation sheds and water connections automatically,
   mapping to default hydraulic sector

**Reading Synchronization**

1. Configure water connections with Spherag element IDs (via census import)
2. Enable "Import from readings" flag
3. Call import_readings_spherag() wizard or use automation
4. Module fetches last readings for configured water meters only (optimized queries)
5. Creates wua.reading records with remote control origin "Spherag"

**Negative Readings**

Negative or divergent readings can be marked with origin "Spherag" for tracking
and later adjustment.

Credits
=======

* Moval Agroingeniería S.L.

Contributors
------------

* Alberto Hernández <ahernandez@moval.es>
* Eduardo Iniesta <einiesta@moval.es>
* Miguel Mora <mmora@moval.es>
* Juanu Sandoval <jsandoval@moval.es>
* Salvador Sánchez <ssanchez@moval.es>
* Jorge Vera <jvera@moval.es>

Maintainer
----------

.. image:: https://services.moval.es/static/images/logo_moval_small.png
   :target: http://moval.es
   :alt: Moval Agroingeniería

This module is maintained by Moval Agroingeniería.
