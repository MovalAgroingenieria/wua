.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
   :target: http://www.gnu.org/licenses/agpl-3.0-standalone.html
   :alt: License: AGPL-3

======================================
Irrigation Recommendations for any WUA
======================================

In a water users association, calculation of irrigation recommendations for each active crop unit. This calculation is based on agroclimatic data (ET0, Pe) and on a Kc coefficient that depends on the crop and the NDVI vegetation index.

Description
===========

This module collects daily from the Spanish SiAR station network the values of ET0 (reference evapotranspiration) and Pe (effective precipitation). It also collects, every five days from the Sentinel satellites, the average NDVI index value for each plot.

Based on the NDVI index and the crop type of each crop unit in the plot, a Kc value is obtained. Then, using ET0, Pe, Kc, and an adjustable coefficient (close to 1), the gross irrigation requirements of the crop unit are calculated.

Credits
=======

* Moval Agroingeniería S.L.

Contributors
------------

* Guillermo Amante <gamante@moval.es>
* César Andrés <candres@moval.es>
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
