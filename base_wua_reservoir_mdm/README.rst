=====================================================
MDM Sensor to Reservoir Reading Templates
=====================================================

This module provides integration between MDM Sensor Management and Water Users Association Reservoir management.

**Features:**

* Links pressure sensors (m.c.a - meters of water column) to reservoirs
* Automatic transformation of pressure sensor readings to reservoir readings
* Scheduled cron job for automated reading imports (inactive by default)
* Transformation template pre-configured for reservoir readings

**Technical Details:**

* **Sensor Type**: Pressure (m.c.a) - measures water column height
* **Target Model**: wua.reservoirreading
* **Selection Mode**: Closest reading to current time
* **No negative reading detection** - not applicable for reservoir water levels

**Field Mappings:**

* reservoir_id → Linked reservoir from sensor configuration
* reading_time → Current datetime
* height → Sensor value (m.c.a)
* volume_entered → Set to 0 (manual entry if needed)

**Domain Filter:**

Only processes sensors that:
- Have type "Pressure (m.c.a)"
- Are linked to a reservoir (reservoir_id is set)

**Cron Job:**

A scheduled action "Transform Reservoir Sensor Readings" is created but **inactive by default**.
Activate it from Settings > Technical > Automation > Scheduled Actions if you want daily automatic transformations.

**Configuration:**

1. Install the module
2. Go to MDM > Configuration > Sensor Types and verify "Pressure (m.c.a)" exists
3. Go to MDM > Configuration > Transform Templates and verify "MDM Sensor to Reservoir Reading" exists
4. Link your pressure sensors to reservoirs via the "Sensors" tab on reservoir forms
5. Optionally activate the cron job for automatic daily transformations

**Usage:**

Manual transformation:
1. Go to MDM > Transform > Transform Readings
2. Select the template "MDM Sensor to Reservoir Reading"
3. Configure parameters (dates, sensors, etc.) as needed
4. Click "Transform" to create reservoir readings

**Dependencies:**

* base_wua_reservoir
* mdm_sensor_management

**Author:** Moval Agroingeniería

**License:** AGPL-3
