.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
   :target: http://www.gnu.org/licenses/agpl-3.0-standalone.html
   :alt: License: AGPL-3

======================================
Inventory for Water Users Associations
======================================


This module extends the maintenance system to enable advanced infrastructure
inventory capabilities specifically tailored for Water Users Associations
(WUAs), with strong GIS integration and dynamic field management.

Description
===========

The module introduces a robust system for defining, classifying and managing
infrastructure elements through:

Functionality:

* **Custom maintenance categories** with a toggle for inventory visibility.
* **Dynamic fields per category**, supporting a wide variety of data types.
* **GIS-aware field mapping**, allowing structured data synchronization with
external GIS tables.
* **Recursive infrastructure creation**, enabling nested asset creation via
`many2one` dynamic fields.
* **Flexible frontend integration**, exposing all inventory metadata through
JSON routes for modern GIS viewers.

Key Features
============

- **Category Configuration**
  - Categories marked as *available for inventory* are automatically exposed to the viewer.
  - Categories can define a related technical model (`model_id`) to link GIS elements to specific infrastructure records.

- **Dynamic Fields System**
  - Text, number, date, checkbox, binary, selection, and `many2one` types supported.
  - Fields can be marked as required, readonly, and mapped to GIS columns (`gis_path`) for synchronization.
  - `many2one` fields support *inline related record creation* via a `related_category_id`.

- **Equipment Management Enhancements**
  - Equipment can be created dynamically from GIS viewer inputs.
  - Extended HTML field `inventory_extra_data` stores unstructured but trackable extra attributes.

- **GIS Integration**
  - Geometry updates are directly written to GIS tables using dynamic SQL mapping.
  - Each category can define its full mapping for base, intermediate, and GIS layers.
  - If no category mapping exists, the geometry is attached directly to the equipment record.

- **Controller Endpoints**
  - `/inventory_categories`: Returns metadata for all categories available for inventory.
  - `/inventory_init_config`: Returns full configuration including inventory-ready equipments, styles, attachments, and dynamic field values.
  - `/inventory_equipments`: Returns the equipments related to the id's passed in the `equipment_ids` parameter, including their dynamic fields and GIS geometries.

Usage Scenario
==============

This module is designed for use cases where infrastructure data is collaboratively edited
and classified by field technicians and engineers via GIS viewers or web-based inventory
tools. It ensures integrity across Odoo and GIS layers, enabling seamless synchronization
of structured data and geometries.

Credits
=======

* Moval Agroingeniería S.L.

Contributors
------------

* Guillermo Amante <gamante@moval.es>
* Samuel Fernández <sfernandez@moval.es>
* Alberto Hernández <ahernandez@moval.es>
* Eduardo Iniesta <einiesta@moval.es>
* Jesús Martínez <jmartinez@moval.es>
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
