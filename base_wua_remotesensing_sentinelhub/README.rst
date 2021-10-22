.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
   :target: http://www.gnu.org/licenses/agpl-3.0-standalone.html
   :alt: License: AGPL-3

===================================================================
Remote Sensing for Water Users Associations (based on Sentinel-Hub)
===================================================================

Base module for other modules that implement a communication with Sentinel-Hub
to get vegetation indices.

Description
===========

This module is the common base for other modules that obtain vegetation indices
based on remote-sensing data of the Sentinel satellites (European Space
Agency). The data is global and available every 5 days, with a resolution
of 10 meters.

The module is not installed directly. You need to install the particular
modules, such as wua_remotesensing_sentinelhub_ndvi.

Some indices are:

* NDVI
* Moisture
* Etc

Functionality:

* Obtain the historical data from each parcel.
* Graphic report based on series.
* Obtain the index orthoimage and the equivalent raster image, for each parcel and each date.

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
