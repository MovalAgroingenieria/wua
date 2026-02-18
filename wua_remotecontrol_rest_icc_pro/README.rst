===========================================================
Water Users Association: Interface with ICC PRO REST API
===========================================================

This module provides integration between Moval Regadío (Water Users Association
management system) and ICC PRO remote control system via REST API.

Configuration
=============

1. Install this module and its dependencies
2. Go to Irrigation Configuration and enable remote control
3. Configure ICC PRO settings in the configuration panel
4. Set up irrigation sheds with ICC PRO identifiers
5. Configure water connections with ICC PRO position

Usage
=====

The module extends:

- **Irrigation Sheds**: Adds ICC PRO device identifiers (device_id)
- **Water Connections**: Adds ICC PRO position field for meter identification
- **Readings**: Implements automatic reading import from ICC PRO

The module provides automatic synchronization of water meter readings from
the ICC PRO system to Odoo.

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

.. image:: https://services.moval.es/static/images/logo_moval_small.png
   :target: http://moval.es
   :alt: Moval Agroingeniería

This module is maintained by Moval Agroingeniería.
