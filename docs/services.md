# Services
The integration adds the following services to vacuum domain. 

## Vacuum Services
Services for actions that are not available via an entity.

<a href="https://my.home-assistant.io/redirect/developer_services/" target="_blank"><img src="https://my.home-assistant.io/badges/developer_services.svg" alt="Open your Home Assistant instance and show your service developer tools." /></a>

### `dreame_vacuum.vacuum_clean_segment`

Start selected room cleaning with optional customized cleaning parameters. 
> - If you are using integration with map feature, you can acquire segment ids from vacuum entity attributes.
> - Cleaning parameters and cleaning sequence are ignored by the device when `customized_cleaning` or `cleaning_sequence` is enabled.

**Examples:**

- Clean room 3
    ```yaml
    service: dreame_vacuum.vacuum_clean_segment
    data:
      segments: 3
    target:
      entity_id: vacuum.vacuum
    ```
- Clean room 3 and 5
    ```yaml
    service: dreame_vacuum.vacuum_clean_segment
    data:
      segments:
        - 3
        - 5
    target:
      entity_id: vacuum.vacuum
    ```

- Clean room 3 and 5 two times
    ```yaml
    service: dreame_vacuum.vacuum_clean_segment
    data:
      segments:
        - 3
        - 5
      repeats: 2
    target:
      entity_id: vacuum.vacuum
    ```

- Clean room 2 two times and 5 one time
    ```yaml
    service: dreame_vacuum.vacuum_clean_segment
    data:
      segments:
        - 3
        - 5
      repeats: 
        - 2
        - 1
    target:
      entity_id: vacuum.vacuum
    ```

- Clean room 3 and 5 with high fan speed
    ```yaml
    service: dreame_vacuum.vacuum_clean_segment
    data:
      segments:
        - 3
        - 5
      suction_level: "high"
    target:
      entity_id: vacuum.vacuum
    ```

- Clean room 3 with high fan speed and 5 with quiet fan speed
    ```yaml
    service: dreame_vacuum.vacuum_clean_segment
    data:
      segments:
        - 3
        - 5
      suction_level: 
        - "high"
        - "quiet"
    target:
      entity_id: vacuum.vacuum
    ```


### `dreame_vacuum.vacuum_clean_zone`

Start selected zone cleaning with optional customized cleaning parameters.

> You can acquire zone coordinates with <a href="https://github.com/PiotrMachowski/lovelace-xiaomi-vacuum-map-card/blob/master/docs/templates/setup.md#getting-coordinates" target="_blank_">Xiaomi Vacuum Map Card</a>.

**Examples:**

- Clean selected zone
    ```yaml
    service: dreame_vacuum.vacuum_clean_zone
    data:
      zone: 
        - 819
        - -263
        - 4424
        - 2105
    target:
      entity_id: vacuum.vacuum
    ```
- Clean multiple zones
    ```yaml
    service: dreame_vacuum.vacuum_clean_zone
    data:
      zone: 
        - - 819
          - -263
          - 4424
          - 2105
        - - 2001
          - -3050
          - 542
          - 515
    target:
      entity_id: vacuum.vacuum
    ```
- Clean selected zone two times
    ```yaml
    service: dreame_vacuum.vacuum_clean_zone
    data:
      zone: 
        - 819
        - -263
        - 4424
        - 2105
      repeats: 2
    target:
      entity_id: vacuum.vacuum
    ```

- Clean first zone two times second zone three times
    ```yaml
    service: dreame_vacuum.vacuum_clean_zone
    data:
      zone: 
        - - 819
          - -263
          - 4424
          - 2105
        - - 2001
          - -3050
          - 542
          - 515
      repeats: 
        - 2
        - 3
    target:
      entity_id: vacuum.vacuum
    ```tity_id: vacuum.vacuum
    ```

### `dreame_vacuum.vacuum_clean_spot`

Start selected spot cleaning with optional customized cleaning parameters.

> Spot cleaning feature is only available for Xiaomi/Mijia branded robots but it works with the Dreame devices too.

> You can acquire point coordinates with <a href="https://github.com/PiotrMachowski/lovelace-xiaomi-vacuum-map-card/blob/master/docs/templates/setup.md#getting-coordinates" target="_blank_">Xiaomi Vacuum Map Card</a>.

**Examples:**

- Clean selected spot
    ```yaml
    service: dreame_vacuum.vacuum_clean_spot
    data:
      points: 
        - 819
        - -263
    target:
      entity_id: vacuum.vacuum
    ```
- Clean multiple spots
    ```yaml
    service: dreame_vacuum.vacuum_clean_spot
    data:
      points: 
        - - 819
          - -263
        - - 2001
          - -3050
    target:
      entity_id: vacuum.vacuum
    ```
- Clean selected spot two times
    ```yaml
    service: dreame_vacuum.vacuum_clean_spot
    data:
      points: 
        - 819
        - -263
      repeats: 2
    target:
      entity_id: vacuum.vacuum
    ```

- Clean first spot two times second spot three times
    ```yaml
    service: dreame_vacuum.vacuum_clean_spot
    data:
      points: 
        - - 819
          - -263
        - - 2001
          - -3050
      repeats: 
        - 2
        - 3
    target:
      entity_id: vacuum.vacuum
    ```

### `dreame_vacuum.vacuum_goto`

TODO

- Go to at [819, -2235] and stop
    ```yaml
    service: dreame_vacuum.vacuum_goto
    data:
      x: 819
      y: -2235
    target:
      entity_id: vacuum.vacuum
    ```

### `dreame_vacuum.vacuum_follow_path`

TODO

### `dreame_vacuum.vacuum_start_shortcut_`

TODO

### `dreame_vacuum.vacuum_remote_control_move_step`

Send remote control command to vacuum. *(For use of a custom lovelace card)*

### `dreame_vacuum.vacuum_install_voice_pack`

Install an official voice pack.

### `dreame_vacuum.vacuum_set_cleaning_sequence`

Set room cleaning sequence on current map. 

> Exact number of room ids must be passed as sequence list

**Example:**

- Set room cleaning sequence on current map to 3, 5, 4, 2, 1
    ```yaml
    service: dreame_vacuum.vacuum_set_cleaning_sequence
    data:
        cleaning_sequence: 
          - 3
          - 5
          - 4
          - 2
          - 1
    target:
        entity_id: vacuum.vacuum
    ```

- Disable custom cleaning sequence on current map
    ```yaml
    service: dreame_vacuum.vacuum_set_cleaning_sequence
    data:
        cleaning_sequence: []
    target:
        entity_id: vacuum.vacuum
    ```

### `dreame_vacuum.vacuum_set_custom_cleaning`

Set customized room cleaning parameters on current map. 

> Settings for all rooms must be passed as list

**Examples:**

- Set room 1 fan speed to quiet, water level to low, cleaning times to 2 and room 5 fan speed to turbo, water level to medium, repeats to 1
    ```yaml
    service: dreame_vacuum.vacuum_set_custom_cleaning
    data:
        segment_id: 
          - 1
          - 5
        suction_level: 
          - 0
          - 3
        water_volume: 
          - 1
          - 2
        repeats: 
          - 2
          - 1
    target:
        entity_id: vacuum.vacuum
    ```

- Set room 3 wetness level to 16
    ```yaml
    service: dreame_vacuum.vacuum_set_custom_cleaning
    data:
        segment_id: 
          - 3
        wetness_level: 
          - 16
    target:
        entity_id: vacuum.vacuum
    ```

### `dreame_vacuum.vacuum_reset_consumable`

Reset a consumable life by type.

> Possible values for consumable
>  - `main_brush`
>  - `side_brush`
>  - `filter`
>  - `tank_filter`
>  - `sensor`
>  - `mop_pad`
>  - `silver_ion`
>  - `detergent`
>  - `squeege`
>  - `dirty_water_channel`
>  - `onboard_dirty_water_tank`
>  - `deodorizer`
>  - `wheel`
>  - `scale_inhibitor`
>  - `fluffing_roller`
>  - `rollermop_filter`
>  - `water_outlet_filter`

**Examples:**

- Reset Main Brush Life
    ```yaml
    service: dreame_vacuum.vacuum_reset_consumable
    data:
        consumable: "main_brush"
    target:
        entity_id: vacuum.vacuum
    ```

- Reset Mop Pad Life
    ```yaml
    service: dreame_vacuum.vacuum_reset_consumable
    data:
        consumable: "mop_pad"
    target:
        entity_id: vacuum.vacuum
    ```

### *`vacuum.send_command`*

Send command service can be used to send raw api requests that are not available with this integration. 

> <a href="https://github.com/al-one/hass-xiaomi-miot#xiaomi-miot-for-homeassistant" target="_blank">More info about commands and parameters.</a>

**Examples:**

- Start auto emptying
    ```yaml
    service: vacuum.send_command
    data:
        entity_id: vacuum.vacuum
        command: action
        params: 
            did: "15.1"
            siid: 15
            aiid: 1
            in: []
    ```

- Enable tight mopping pattern and disable carpet boost
    ```yaml
    service: vacuum.send_command
    data:
        entity_id: vacuum.vacuum
        command: set_properties
        params: 
          - did: "4.29"
            siid: 4
            piid: 29
            value: 1
          - did: "4.12"
            siid: 4
            piid: 12
            value: 0
    ```

## Map Services
Map editing services also uses the vacuum domain because all services are available even without cloud connection.

<a href="https://my.home-assistant.io/redirect/developer_services/" target="_blank"><img src="https://my.home-assistant.io/badges/developer_services.svg" alt="Open your Home Assistant instance and show your service developer tools." /></a>

### `dreame_vacuum.vacuum_request_map`

Request device to upload a new map to the cloud. *(This service is useful when cloud connection is not used and another integration used for handing the map rendering)*

> Device does not responds to this action when:
> - Spot cleaning
> - Fast mapping
> - Relocating
> - After a map edit until it moves

### `dreame_vacuum.vacuum_select_map`

Change currently selected map. (Only possible of multi-floor map is enabled)

> - You can acquire map id from saved map camera entity attributes.

> - Robot will end active job when selected map is changed.

**Example:**

- Set current map as map with id 27
    ```yaml
    service: dreame_vacuum.vacuum_select_map
    data:
        map_id: 27
    target:
        entity_id: vacuum.vacuum
    ```

### `dreame_vacuum.vacuum_delete_map`

Delete a map.

> - You can acquire map id from saved map camera entity attributes.
> - When multi-floor map feature is enabled map indexes may change after deletion. <a href="https://github.com/Tasshack/dreame-vacuum/blob/master/docs/#multi-floor-map-support" target="_blank">(More about multi-floor map support)</a>

**Example:**

- Set delete map with id 48
    ```yaml
    service: dreame_vacuum.vacuum_delete_map
    data:
        map_id: 48
    target:
        entity_id: vacuum.vacuum
    ```

### `dreame_vacuum.vacuum_rename_map`

Rename a map.

> - You can acquire map id from saved map camera entity attributes.
> - Official App does not allow you to enter special characters in map name but this integration does so use this service carefully.

**Example:**

- Rename map with id 14 to "Second Floor"
    ```yaml
    service: dreame_vacuum.vacuum_rename_map
    data:
        map_id: 14
        map_name: "Second Floor"
    target:
        entity_id: vacuum.vacuum
    ```

### `dreame_vacuum.vacuum_restore_map`

Restore a map from previous state that are created and uploaded by the device.
> - It is not guaranteed that map recovery will be successful. Cloud does not store the files forever and recovery files usually be deleted from the cloud after 365 days from the last access.
>  - Cloud connection is required with this service.

**Examples:**

- Restore selected map to second saved recovery map in the recovery map list
    ```yaml
    service: dreame_vacuum.vacuum_restore_map
    data:
        recovery_map_index: 2
    target:
        entity_id: vacuum.vacuum
    ```

- Restore saved map with id 14 to original state
    ```yaml
    service: dreame_vacuum.vacuum_restore_map
    data:
        map_id: 14
        recovery_map_index: 1
    target:
        entity_id: vacuum.vacuum
    ```

### `dreame_vacuum.vacuum_restore_map_from_file`

Restore a map from previously saved recovery map file.
> - This service can be used for offline recovery if you download and place the recovery map file to the /www/ folder of Home Assistant (Vacuum and server must be at the same network).
> - Map Id is required if cloud connection is not enabled.

**Examples:**

- Restore selected map from saved recovery map file
    ```yaml
    service: dreame_vacuum.vacuum_restore_map_from_file
    data:
        file_url: http://192.168.1.10/local/2023-11-04-1724223415-423528451_284320462.1156.mb.tbz2
    target:
        entity_id: vacuum.vacuum
    ```

- Restore saved map with id 14 saved recovery map file
    ```yaml
    service: dreame_vacuum.vacuum_restore_map_from_file
    data:
        map_id: 14
        file_url: https://dreame-cn.oss-cn-shanghai.aliyuncs.com/iot/tmp/000000/ali_dreame/YR649291/648921668/101?Expires=1699189998&OSSAccessKeyId=LTAI5t96WkBXXNzQrX4HtQti&Signature=ttRrjg8p7aC650H3DwI3%2F2ngOOE%3D
    target:
        entity_id: vacuum.vacuum
    ```

### `dreame_vacuum.vacuum_backup_map`

Trigger upload of a saved map as a recovery map to the cloud.
> - Cloud can store only one backup map for every saved map. This service will override the previously backup map if you have one.
> - Vacuums without a camera or a lidar sensor does not have this feature, map backup trigger only works on supported devices.

**Examples:**

- Trigger backup of selected map
    ```yaml
    service: dreame_vacuum.vacuum_backup_map
    target:
        entity_id: vacuum.vacuum
    ```

- Trigger backup of map with id 15
    ```yaml
    service: dreame_vacuum.vacuum_backup_map
    data:
        map_id: 15
    target:
        entity_id: vacuum.vacuum
    ```

### `dreame_vacuum.vacuum_set_restricted_zone`

Set invisible walls, no go and no mopping zones on current map.

> - You can acquire line and zone coordinates with <a href="https://github.com/PiotrMachowski/lovelace-xiaomi-vacuum-map-card/blob/master/docs/templates/setup.md#getting-coordinates" target="_blank_">Xiaomi Vacuum Map Card</a>.
> - All object must be passed at one, you cannot add or remove single wall or no zone. You can acquire current line and zone coordinates from selected map camera entity attributes.

**Examples:**

- Define virtual walls, restricted zones, and/or no mop zones
    ```yaml
    service: dreame_vacuum.vacuum_set_restricted_zone
    data:
        walls: 
            - - 819
              - -263
              - 4424
              - 2105
        zones: 
            - - 819
              - -263
              - 4424
              - 2105
            - - -2001
              - -3050
              - -542
              - 515
        no_mops: []
    target:
        entity_id: vacuum.vacuum
    ```

### `dreame_vacuum.vacuum_save_temporary_map`

Save newly created map. (Device ask you to do when first map is created after factory reset)

### `dreame_vacuum.vacuum_discard_temporary_map`

Discard newly created map.

### `dreame_vacuum.vacuum_replace_temporary_map`

Replace new map with an old one.

> - You can acquire map id from saved map camera entity attributes.
> - When multi-floor map feature is enabled map indexes may change after replacing the map. Replaced new map will always be at last available index event replaced with a lower indexed map. <a href="https://github.com/Tasshack/dreame-vacuum/blob/master/docs/#multi-floor-map-support" target="_blank">(More about multi-floor map support)</a>

**Example:**

- Replace new map with map with id 39
    ```yaml
    service: dreame_vacuum.vacuum_replace_temporary_map
    data:
        map_id: 39
    target:
        entity_id: vacuum.vacuum
    ```

### `dreame_vacuum.vacuum_merge_segments`

Merge two rooms from a map.

> - You can acquire map and segment ids from saved map camera entity attributes.
> - Rooms needs to be neighbors with each other.
> - Deleted segment ids are not used again on new created segments.
> - When multi-floor map feature is enabled selected map will change to edited map.

**Examples:**

- Merge rooms 4 with 6 on the map with 63 (Room 6 will be deleted)
    ```yaml
    service: dreame_vacuum.vacuum_replace_temporary_map
    data:
        map_id: 63
        segments: 
            - 4
            - 6
    target:
        entity_id: vacuum.vacuum
    ```

- Merge rooms 6 with 4 on the map with 63 (Room 4 will be deleted)
    ```yaml
    service: dreame_vacuum.vacuum_replace_temporary_map
    data:
        map_id: 63
        segments: 
            - 6
            - 4
    target:
        entity_id: vacuum.vacuum
    ```

### `dreame_vacuum.vacuum_split_segments`

Split a map room into to different rooms.

> - You can acquire map and segment ids from saved map camera entity attributes.
> - You can acquire line coordinates coordinates with <a href="https://github.com/PiotrMachowski/lovelace-xiaomi-vacuum-map-card/blob/master/docs/templates/setup.md#getting-coordinates" target="_blank_">Xiaomi Vacuum Map Card</a>.
> - Line coordinates must cover selected room area.
> - Deleted segment ids are not used again and new segment always will be at highest next available index.
> - When multi-floor map feature is enabled selected map will change to edited map.

**Example:**

- Split room 4 from line coordinates (A new room will be created and room 4 settings will set to defaults)
    ```yaml
    service: dreame_vacuum.vacuum_replace_temporary_map
    data:
        map_id: 63
        segment: 4
        line: 
            - 819
            - -263
            - 4424
            - 2105
    target:
        entity_id: vacuum.vacuum
    ```

### `dreame_vacuum.vacuum_rename_segment`

Set custom name for a room in current map.

> - You can acquire map and segment ids from saved map camera entity attributes.
> - Official App does not allow you to enter special characters in room name but this integration does so use this service carefully.

**Example:**
- Rename room 3 to "Dining Room"
    ```yaml
    service: dreame_vacuum.vacuum_rename_segment
    data:
        segment_id: 3
        segment_name: "Dining Room"
    target:
        entity_id: vacuum.vacuum
    ```

### `dreame_vacuum.vacuum_rename_shortcut`

TODO

### `dreame_vacuum.vacuum_delete_shortcut`

TODO


### `dreame_vacuum.vacuum_set_obstacle_ignore`

TODO

### `dreame_vacuum.vacuum_set_router_position`

TODO

### `dreame_vacuum.vacuum_set_virtual_threshold`

TODO

### `dreame_vacuum.vacuum_set_carpet_area`

TODO

### `dreame_vacuum.vacuum_set_predefined_points`

TODO


## Other Services
Integration adds <a href="https://www.home-assistant.io/integrations/input_select/#services" target="_blank_">**input_select** services</a> that are missing from the **select** entity to generated select entities for ease of use.

### `dreame_vacuum.select_select_first`

Select first option from options list

### `dreame_vacuum.select_select_last`

Select last option from options list

### `dreame_vacuum.select_select_previous`

Select previous option from options list

### `dreame_vacuum.select_select_next`

Select next option from options list

**<a href="https://github.com/Tasshack/dreame-vacuum/blob/master/room_entities.md#rooms-card" target="_blank">For more info about how these services are used</a>**