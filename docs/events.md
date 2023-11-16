# Events
Integration tracks certain device properties and notifies HA on specific events similar to the notification feature but events always will be fired even notifications are disabled from integration options.

### Cleanup started or finished
Fires when cleanup job is completed or canceled/ended.

#### `dreame_vacuum_task_status`
- `entity_id`: Vacuum entity
- `cleaning_mode`: Selected cleaning mode
- `status`: Status
- `water_tank`: Water tank is installed
- `mop_pad`: Mop pads are installed
- `completed`: Task is completed or started
- `cleaned_area`: Cleaned area. (Only present when task is completed)
- `cleaning_time`: Cleaned area. (Only present when task is completed)
- `active_segments`: Selected rooms for the segment cleaning task. (Only present if map feature is enabled)
- `active_areas`: Selected areas for the zone cleaning task. (Only present if map feature is enabled)
- `active_points`: Selected points for the spot cleaning task. (Only present if map feature is enabled)

### Consumable is depleted
Fires when consumable life is ended.

#### `dreame_vacuum_consumable`
- `entity_id`: Vacuum entity
- `consumable`: Consumable type
  - `main_brush`: Main brush must be replaced
  - `side_brush`: Side brush must be replaced
  - `filter`: Filter must be replaced
  - `sensor`: Sensors must be cleaned
  - `mop_pad`: Mop pads must be replaced
  - `silver_ion`: Silver-ion must be replaced
  - `detergent`: Detergent must be replaced

### Information
Fires when certain job cannot be executed due to the user settings.

#### `dreame_vacuum_information`
- `entity_id`: Vacuum entity
- `information`: Information type
  - `dust_collection`: Dust collection not performed due to the DnD settings
  - `cleaning_paused`: Cleaning paused due to low battery

### Warning
Fires when there is a dismissible warning code on the device.

#### `dreame_vacuum_warning`
- `entity_id`: Vacuum entity
- `warning`: Warning description
- `code`: Fault code of the warning

### Error
Fires when there is a fault code on the device.

#### `dreame_vacuum_error`
- `entity_id`: Vacuum entity
- `error`: Error description
- `code`: Fault code of the error

### Low Water
Fires when there is low water warning.

#### `dreame_vacuum_low_water`
- `entity_id`: Vacuum entity
- `low_water`: Low water warning description
- `code`: Fault code of the low water warning

### Drainage Status
Fires when water tank drainage is completed or failed.

#### `dreame_vacuum_drainage_status`
- `entity_id`: Vacuum entity
- `drainage_status`: Drainage is successful or not

### 2FA Login Required
Fires when there two factor authentication is required to login.

#### `dreame_vacuum_2fa_login`
- `entity_id`: Vacuum entity
- `url`: 2FA login URL