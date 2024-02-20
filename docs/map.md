# Map Support

Completely reverse engineered map data handling, decoding and rendering for live and multiple saved map support with all features provided with the official App.

<img src="https://raw.githubusercontent.com/Tasshack/dreame-vacuum/master/docs/media/live_map.jpg" width="400px">

- High resolution image rendering with layer caching for improving performance.
- All resources with icon position and color index finding algorithms are extracted from the official App for same look and feel.
- All map operations is handled on memory before it is sent to device for low latency updates.
- Fully featured highly optimized integrated map manager for map editing and handling partial maps.
- With dynamic refresh rate determined by map type, device state and last access time.

### High refresh rate with low latency

Partial map (P frame type) decoding for three seconds refresh rate with three seconds delay same as with the official App.

<a href="https://raw.githubusercontent.com/Tasshack/dreame-vacuum/master/docs/media/cleaning.gif" target="_blank"><img src="https://raw.githubusercontent.com/Tasshack/dreame-vacuum/master/docs/media/cleaning.gif" width="500px"></a>

> - P type maps are introduced with second generation robots and new devices only sends P frames to the cloud when running.
> - P maps are only containing the difference between its previous frame therefore handling is much harder than standard I type maps.
> - Valetudo do not parses P frames suggesting that is hard and instead it sends new map requests to refresh the map but requesting I frames from device is strictly restricted to minimum 5 seconds on the official App source code. 
> - Documentation for handling P frames is not available and currently there are no other integration, library or app exists that can handle P maps for Dreame vacuums except the official App.

### Color schemes

Five available color schemes for live and saved maps:
- **Dreame Light**: Colors from the official Dreame App for light themes.
- **Dreame Dark**: Darkened version of the *Dreame Light* map for dark themes.
- **Mijia Light**: Colors from the official Mijia App for light themes.
- **Mijia Dark**: Darkened version of the *Mijia Light* map for dark themes.
- **Grayscale**: Black and white version of the *Dreame Dark* map with inverted icon colors for a clean look.

 > Map color scheme can be changed from integration configuration options.

<a href="https://raw.githubusercontent.com/Tasshack/dreame-vacuum/master/docs/media/map_dreame_light.png" target="_blank"><img src="https://raw.githubusercontent.com/Tasshack/dreame-vacuum/master/docs/media/map_dreame_light.png" width="19%"></a><a href="https://raw.githubusercontent.com/Tasshack/dreame-vacuum/master/docs/media/map_dreame_dark.png" target="_blank"><img src="https://raw.githubusercontent.com/Tasshack/dreame-vacuum/master/docs/media/map_dreame_dark.png" width="19%"></a><a href="https://raw.githubusercontent.com/Tasshack/dreame-vacuum/master/docs/media/map_mijia_light.png" target="_blank"><img src="https://raw.githubusercontent.com/Tasshack/dreame-vacuum/master/docs/media/map_mijia_light.png" width="19%"></a><a href="https://raw.githubusercontent.com/Tasshack/dreame-vacuum/master/docs/media/map_mijia_dark.png" target="_blank"><img src="https://raw.githubusercontent.com/Tasshack/dreame-vacuum/master/docs/media/map_mijia_dark.png" width="19%"></a><a href="https://raw.githubusercontent.com/Tasshack/dreame-vacuum/master/docs/media/map_grayscale.png" target="_blank"><a href="https://raw.githubusercontent.com/Tasshack/dreame-vacuum/master/docs/media/map_grayscale.png" target="_blank"><img src="https://raw.githubusercontent.com/Tasshack/dreame-vacuum/master/docs/media/map_grayscale.png" width="19%"></a>

### Room and customized cleaning icons

Dynamically rendered icons and texts for:
- Room type
- Custom name
- Cleaning order
- suction level
- Water level
- Cleaning Times

<a href="https://raw.githubusercontent.com/Tasshack/dreame-vacuum/master/docs/media/map_icons.gif" target="_blank"><img src="https://raw.githubusercontent.com/Tasshack/dreame-vacuum/master/docs/media/map_icons.gif" width="500px"></a>


### Dynamic object rendering for job types

Custom rendering rules extracted from the official App for specific type of job and robot state.

<a href="https://raw.githubusercontent.com/Tasshack/dreame-vacuum/master/docs/media/room_cleaning.gif" target="_blank"><img src="https://raw.githubusercontent.com/Tasshack/dreame-vacuum/master/docs/media/room_cleaning.gif" width="400px"></a><a href="https://raw.githubusercontent.com/Tasshack/dreame-vacuum/master/docs/media/zone_cleaning.gif" target="_blank"><img src="https://raw.githubusercontent.com/Tasshack/dreame-vacuum/master/docs/media/zone_cleaning.gif" width="400px"></a>

**<a href="https://github.com/Tasshack/dreame-vacuum/blob/master/README.md#with-xiaomi-vacuum-map-card" target="_blank">For more info about Xiaomi Vacuum map card</a>**

### Fast mapping and spot cleaning

Live mapping support with *new map* handling, parsing and rendering.

<a href="https://raw.githubusercontent.com/Tasshack/dreame-vacuum/master/docs/media/fast_mapping.gif" target="_blank"><img src="https://raw.githubusercontent.com/Tasshack/dreame-vacuum/master/docs/media/fast_mapping.gif" width="400px"></a><a href="https://raw.githubusercontent.com/Tasshack/dreame-vacuum/master/docs/media/spot_cleaning.gif" target="_blank"><img src="https://raw.githubusercontent.com/Tasshack/dreame-vacuum/master/docs/media/spot_cleaning.gif" width="400px"></a>

> When robot is fast mapping or spot cleaning it creates a new map on its memory and does not responds to local map_request api actions. Newly created map does not have an object name yet so it can only be accessed via cloud map_data property. New map data requires different decoding and rendering rules because of that there are currently no other available map decoder library for this types of maps.

### Robot state

Vacuum icon overlays for displaying device state same as on the official App.

| <div style="width:70px">Sleeping</div> | <div style="width:70px">Idle</div> | <div style="width:70px">Active</div> | <div style="width:70px">Charging</div> | <div style="width:70px">Error</div> | 
|:--------:|:--------:|:--------:|:--------:|:--------:| 
| <img src="https://raw.githubusercontent.com/Tasshack/dreame-vacuum/master/docs/media/robot_sleeping.png" width="50px"> | <img src="https://raw.githubusercontent.com/Tasshack/dreame-vacuum/master/docs/media/robot_idle.png" width="50px"> | <img src="https://raw.githubusercontent.com/Tasshack/dreame-vacuum/master/docs/media/robot_active.png" width="50px"> | <img src="https://raw.githubusercontent.com/Tasshack/dreame-vacuum/master/docs/media/robot_charging.png" width="50px"> | <img src="https://raw.githubusercontent.com/Tasshack/dreame-vacuum/master/docs/media/robot_error.png" width="50px"> |

> Warnings are clearable via notifications or `clear_warning` service for restoring robot state on map.

### Multi-floor map support

Up to three saved maps with auto generated camera and select entities for multiple floor map management.

> Saved maps uses `[original map id][version]` as their `map_id` format (e.g. `46`). Because of that map ids are constantly changing and cannot be used on entity ids. Instead, map camera entities uses indexing system. Map indexes created from map id ordered saved map list and used for naming maps without custom names. Therefore when  `map_2` removed from the list, `map_3` will be deleted instead and `map_3` will become `map_2` (exactly how handled on the official App). If Multi-floor map is disabled when multiple saved maps exists `map_1` always become the selected map instead of other maps being deleted.

<a href="https://raw.githubusercontent.com/Tasshack/dreame-vacuum/master/docs/media/multi_map.gif" target="_blank"><img src="https://raw.githubusercontent.com/Tasshack/dreame-vacuum/master/docs/media/multi_map.gif" width="500px"></a>

### Map entities

Automatically generated saved and live map entities for map editing and automations.

<img src="https://raw.githubusercontent.com/Tasshack/dreame-vacuum/master/docs/media/map_entities.png" width="500px">

**<a href="https://github.com/Tasshack/dreame-vacuum/blob/master/docs/entities.md#select" target="_blank">For more info about map entities</a>**

### Dynamic room entities for selected map

Automatically generated room entities for room and customized cleaning settings.

<a href="https://raw.githubusercontent.com/Tasshack/dreame-vacuum/master/docs/media/rooms.gif" target="_blank"><img src="https://raw.githubusercontent.com/Tasshack/dreame-vacuum/master/docs/media/rooms.gif" width="500px"></a>

**<a href="https://github.com/Tasshack/dreame-vacuum/blob/master/room_entities.md" target="_blank">For more info about room entities</a>**

### Map and room editing services

Services for available map operations provided with the official App.

<a href="https://raw.githubusercontent.com/Tasshack/dreame-vacuum/master/docs/media/merge_segments.gif" target="_blank"><img src="https://raw.githubusercontent.com/Tasshack/dreame-vacuum/master/docs/media/merge_segments.gif" width="400px"></a><a href="https://raw.githubusercontent.com/Tasshack/dreame-vacuum/master/docs/media/split_segments.gif" target="_blank"><img src="https://raw.githubusercontent.com/Tasshack/dreame-vacuum/master/docs/media/split_segments.gif" width="400px"></a>

**<a href="https://github.com/Tasshack/dreame-vacuum/blob/master/docs/services.md#map-services" target="_blank">For more info about map services</a>**

### Valetudo map card support

Reverse engineered Valetudo map data generation with optimization features.

> Valetudo map card uses its own color index algorithm, does not render room icons or names and ignores the map rotation setting from map data. But it can generate images much more quickly since map image rendering actually happens on browser.

<img src="https://raw.githubusercontent.com/Tasshack/dreame-vacuum/master/docs/media/valetudo_map.png" width="500px">

**<a href="https://github.com/Tasshack/dreame-vacuum/blob/master/README.md#with-valetudo-map-card" target="_blank">For more info about valetudo map card</a>**

### Map Icon Set

Selectable room, vacuum and charger icon types:

- **Dreame**: Icons from the official Dreame App.
- **Dreame Old**: Icons from the old version of the official Dreame App for VSLAM robots.
- **Mijia**: Icons from the official Mijia App.
- **Material**: Icons from the Material Design.

### Map Objects

Configurable map object rendering options: 

> Map object can be selected from integration configuration options.
- **Room Colors**: Render rooms with colors
- **Room Icons**: Render room icons instead of names
- **Room Names**: Render custom and default room names
- **Room Order**: Render cleaning sequence number of the room
- **Room Suction Level**: Render customized cleaning suction level of the room
- **Room Water Volume**: Render customized cleaning water volume of the room
- **Room Cleaning Times**: Render customized cleaning times of the room
- **Room Cleaning Mode**: Render customized cleaning cleaning mode of the room *(Only on supported devices)*
- **Path**: Render path
- **No Go Zones**: Render no go zones
- **No Mop Zones**: Render no mop zones
- **Virtual Walls**: Render virtual walls
- **Active Areas**: Render active areas
- **Active Points**: Render active points
- **Charger Icon**: Render charger icon
- **Robot Icon**: Render robot icon
- **Cleaning Direction**: Render cleaning direction *(Not supported yet)*
- **AI Obstacle**: Render obstacle icon
- **Carpet Area**: Render carpet areas *(Not supported yet)*

### Map recovery

*Map recovery support is coming soon.*

### Cleaning history map

*Cleaning history map rendering support is coming soon.*

### <a href="https://github.com/Tasshack/dreame-vacuum/blob/master/README.md#how-to-use" target="_blank">How to use</a>