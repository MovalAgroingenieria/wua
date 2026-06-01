.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
   :target: http://www.gnu.org/licenses/agpl-3.0-standalone.html
   :alt: License: AGPL-3

====================================================================
Water Users Association: Interface with Regaber SKYplatform REST API
====================================================================

WUA integration for the Regaber SKYplatform REST API v2.6.  Imports
water meter counter readings from SKYreg and SKYmeter NB-IoT devices into
``wua.reading`` records.

Features
========

* Adds *Regaber SKYplatform* as a telecontrol option for ``wua.waterconnection``
* Stores the SKYplatform ``TreeNodeId`` and device type per waterconnection
* Imports the last counter reading from SKYplatform into ``wua.reading``
* Plugs into the standard ``do_import_reading_of_telecontrol`` hook
* Settings page entry under WUA Irrigation Configuration

Configuration
=============

1. Install ``remotecontrol_regaber`` and configure credentials in the
   Regaber remote control record.
2. Install this module.
3. On each ``wua.waterconnection``:

   * Set *Telecontrol Associated* to **Regaber SKYplatform**.
   * Set *Regaber TreeNode ID* to the ``Id`` from ``GET /TreeNode``.
   * Set *Regaber Device Type* (``skyreg``, ``skyreg_hydrant``, or
     ``skymeter_nbiot``).

4. In *WUA → Configuration → Irrigation Settings*, enable
   *Import from readings (Regaber)*.

Credits
=======

 * Moval Agroingeniería S.L.

Contributors
------------
* Guillermo Amante <gamante@moval.es>
* Samuel Fernández <sfernandez@moval.es>
* Alberto Hernández <ahernandez@moval.es>
* Jesús Martínez <jmartinez@moval.es>
* Miguel Mora <mmora@moval.es>
* Juanu Sandoval <jsandoval@moval.es>
* Salvador Sánchez <ssanchez@moval.es>
* Jorge Vera <jvera@moval.es>

Maintainer
----------

.. image:: https://raw.githubusercontent.com/MovalAgroingenieria/public-assets/master/logos/logo_moval_small.png
   :target: http://moval.es
   :alt: Moval Agroingeniería

This module is maintained by Moval Agroingeniería.
