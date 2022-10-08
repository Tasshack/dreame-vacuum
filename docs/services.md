# Services
The integration adds the following services to vacuum domain. 

## Vacuum Services
Services for actions that are not available via an entity

#### `dreame_vacuum.vacuum_clean_segment`

Start selected room cleaning with optional customized cleaning parameters.

#### `dreame_vacuum.vacuum_clean_zone`

Start selected zone cleaning with optional customized cleaning parameters.

#### `dreame_vacuum.vacuum_set_dnd`

Set do not disturb settings. *(This service exists because the lack of **date_time** entity on Home Assistant)*

#### `dreame_vacuum.vacuum_remote_control_move_step`

Send remote control command to vacuum. *(For use of a custom lovelace card)*

#### `dreame_vacuum.vacuum_install_voice_pack`

Install an official voice pack.

#### `dreame_vacuum.vacuum_set_cleaning_order`

Set room cleaning sequence on current map. 

#### `dreame_vacuum.vacuum_set_custom_cleaning`

Set customized room cleaning parameters on current map. 

## Map Services
Map editing services also uses the vacuum domain because all services are available even without cloud connection.

#### `dreame_vacuum.vacuum_request_map`

Request device to upload a new map to the cloud. *(This service is useful when cloud connection is not used and another integration used for handing the map rendering)*

Device does not responds to this action when:
- Spot cleaning
- Fast mapping
- Relocating
- After a map edit until it moves

#### `dreame_vacuum.vacuum_select_map`

Change currently selected map. (Only possible of multi-floor map is enabled)

#### `dreame_vacuum.vacuum_delete_map`

Delete a map.

#### `dreame_vacuum.vacuum_rename_map`

Rename a map.

#### `dreame_vacuum.vacuum_restore_map`

Restore a map from previous state that are created and uploaded by the device.

#### `dreame_vacuum.vacuum_set_restricted_zone`

Set invisible walls, no go and no mopping zones on a map.

#### `dreame_vacuum.vacuum_save_temporary_map`

Save newly created map. (Device ask you to do when first map is created after factory reset)

#### `dreame_vacuum.vacuum_discard_temporary_map`

Discard newly created map.

#### `dreame_vacuum.vacuum_replace_temporary_map`

Replace new map with an old one.

#### `dreame_vacuum.vacuum_merge_segments`

Merge two segments from current map.

#### `dreame_vacuum.vacuum_split_segments`

Split a map segment into to different segments.

#### `dreame_vacuum.vacuum_rename_segment`

Set custom name for a segment.

## Other Services
Integration adds **input_select** services that are missing from the **select** entity to generated select entities for ease of use.

#### `dreame_vacuum.select_select_first`

Select first option from options list

#### `dreame_vacuum.select_select_last`

Select last option from options list

#### `dreame_vacuum.select_select_previous`

Select previous option from options list

#### `dreame_vacuum.select_select_next`

Select next option from options list