[![Version](https://img.shields.io/github/manifest-json/v/Tasshack/dreame-vacuum/dev?filename=custom_components%2Fdreame_vacuum%2Fmanifest.json&color=slateblue&label=Version&style=for-the-badge)](https://github.com/Tasshack/dreame-vacuum/releases)
![Downloads](https://img.shields.io/github/downloads/Tasshack/dreame-vacuum/total?label=Downloads&style=for-the-badge)
![Stars](https://img.shields.io/github/stars/Tasshack/dreame-vacuum?label=Stars&color=darkgoldenrod&style=for-the-badge)
[![HACS](https://img.shields.io/badge/HACS-Default-orange.svg?logo=HomeAssistantCommunityStore&logoColor=white&style=for-the-badge)](https://github.com/hacs/integration)
[![Community Forum](https://img.shields.io/static/v1.svg?label=Community&message=Forum&color=41bdf5&logo=HomeAssistant&logoColor=white&style=for-the-badge)](https://community.home-assistant.io/t/custom-component-dreame-vacuum/473026)
[![Ko-Fi](https://img.shields.io/static/v1.svg?label=%20&message=Ko-Fi&color=F16061&logo=ko-fi&logoColor=white&style=for-the-badge)](https://www.ko-fi.com/Tasshack)
[![PayPal.Me](https://img.shields.io/static/v1.svg?label=%20&message=PayPal.Me&logo=paypal&color=blue&style=for-the-badge)](https://paypal.me/Tasshackk)

![Logo](https://raw.githubusercontent.com/Tasshack/dreame-vacuum/dev/docs/media/logo.png)

# Dreame vacuum integration for Home Assistant

Complete app replacement with Home Assistant for Dreame robot vacuums.

<img src="https://raw.githubusercontent.com/Tasshack/dreame-vacuum/master/docs/media/map.png" width="48%"><img src="https://raw.githubusercontent.com/Tasshack/dreame-vacuum/master/docs/media/map_app.png" width="48%">

<img src="https://raw.githubusercontent.com/Tasshack/dreame-vacuum/master/docs/media/settings.png" width="48%"><img src="https://raw.githubusercontent.com/Tasshack/dreame-vacuum/master/docs/media/settings_app.png" width="48%">

## Features

- [Supported devices](https://github.com/Tasshack/dreame-vacuum/blob/dev/docs/supported_devices.md)
- [Auto generated device entities](https://github.com/Tasshack/dreame-vacuum/blob/dev/docs/entities.md)
- [Live and multi floor map support](https://github.com/Tasshack/dreame-vacuum/blob/dev/docs/map.md)
- [Map obstacle photos](https://github.com/Tasshack/dreame-vacuum/blob/dev/docs/map.md#obstacle-photos)
- [Cleaning and cruising history maps](https://github.com/Tasshack/dreame-vacuum/blob/dev/docs/map.md#cleaning-and-cruising-history-maps)
- [Cloud and local map backup/recovery](https://github.com/Tasshack/dreame-vacuum/blob/dev/docs/map.md#backup-and-recovery)
- [Saved WiFi coverage maps](https://github.com/Tasshack/dreame-vacuum/blob/dev/docs/map.md#wifi-map)
- [Customized room cleaning entities](https://github.com/Tasshack/dreame-vacuum/blob/dev/docs/room_entities.md)
- [Services for device and map with examples](https://github.com/Tasshack/dreame-vacuum/blob/dev/docs/services.md)
- [Persistent notifications and error reporting](https://github.com/Tasshack/dreame-vacuum/blob/dev/docs/notifications.md)
- [Events for automations](https://github.com/Tasshack/dreame-vacuum/blob/dev/docs/events.md)
- Dreamehome account support
- Movahome account support


## Installation

#### Manually

```bash
wget -O - https://raw.githubusercontent.com/Tasshack/dreame-vacuum/dev/install | bash -
```


#### Via [HACS](https://hacs.xyz/)
<a href="https://my.home-assistant.io/redirect/hacs_repository/?owner=Tasshack&repository=dreame-vacuum&category=integration" target="_blank"><img src="https://my.home-assistant.io/badges/hacs_repository.svg" alt="Open your Home Assistant instance and open a repository inside the Home Assistant Community Store." /></a>


## Configuration

<a href="https://my.home-assistant.io/redirect/config_flow_start/?domain=dreame_vacuum" target="_blank"><img src="https://my.home-assistant.io/badges/config_flow_start.svg" alt="Open your Home Assistant instance and start setting up a new integration." /></a>
- Select configuration type:

     - **Mi Home Account**: TODO
     - **Dreamehome Account**: TODO
     - **Local**: TODO

- Enter required credentials according to the selected configuration type. 
  > Please make sure that the devices are at same subnet for `Mi Home account` and `Local` configuration types. <a href="https://python-miio.readthedocs.io/en/latest/troubleshooting.html#discover-devices-across-subnets" target="_blank">python-miio article about this issue.</a>
- Set your device name and integration settings:

    TODO

    <a href="https://github.com/Tasshack/dreame-vacuum/blob/dev/docs/notifications.md" target="_blank">About notifications feature</a><br><a href="https://github.com/Tasshack/dreame-vacuum/blob/dev/docs/map.md#color-schemes" target="_blank">About map color schemes</a>
- Navigate to device page for disabling or enabling entities that you want to use.

    <a href="https://github.com/Tasshack/dreame-vacuum/blob/dev/docs/entities.md" target="_blank">About entities</a>


## How To Use
Integration is compatible with all available Lovelace vacuum cards but if you want to use zone cleaning feature you can prefer the Xiaomi Vacuum Card.

#### With Dreame Vacuum Card

*Work in progress... <a href="https://github.com/Tasshack/dreame-vacuum/issues/466" target="_blank">#466</a>*


#### With [Xiaomi Vacuum Map Card](https://github.com/PiotrMachowski/lovelace-xiaomi-vacuum-map-card)
 > Template for room and zone cleaning.
<a href="https://my.home-assistant.io/redirect/developer_template/" target="_blank"><img src="https://my.home-assistant.io/badges/developer_template.svg" alt="Open your Home Assistant instance and show your template developer tools." /></a>
```yaml
{# ----------------- PROVIDE YOUR OWN ENTITY IDS HERE ----------------- #}
{% set camera_entity = "camera." %}
{% set vacuum_entity = "vacuum." %}
{# ------------------- DO NOT CHANGE ANYTHING BELOW ------------------- #}
{% set attributes = states[camera_entity].attributes %}

type: custom:xiaomi-vacuum-map-card
vacuum_platform: default
entity: {{ vacuum_entity }}
map_source:
  camera: {{ camera_entity }}
calibration_source:
  camera: true
map_modes:
  - template: vacuum_clean_zone
    max_selections: 10
    repeats_type: EXTERNAL
    max_repeats: 3
    service_call_schema:
      service: dreame_vacuum.vacuum_clean_zone
      service_data:
        entity_id: '[[entity_id]]'
        zone: '[[selection]]'
        repeats: '[[repeats]]'
  - template: vacuum_clean_segment
    repeats_type: EXTERNAL
    max_repeats: 3
    service_call_schema:
      service: dreame_vacuum.vacuum_clean_segment
      service_data:
        entity_id: '[[entity_id]]'
        segments: '[[selection]]'
        repeats: '[[repeats]]'
    predefined_selections:
{%- for room_id in attributes.rooms | default([]) %}
{%- set room = attributes.rooms[room_id] %}
      - id: {{room_id}}
        outline:
          - - {{room["x0"]}}
            - {{room["y0"]}}
          - - {{room["x0"]}}
            - {{room["y1"]}}
          - - {{room["x1"]}}
            - {{room["y1"]}}
          - - {{room["x1"]}}
            - {{room["y0"]}}
{%- endfor %}
  - name: Clean Spot
    icon: mdi:map-marker-plus
    max_repeats: 3
    selection_type: MANUAL_POINT
    repeats_type: EXTERNAL
    service_call_schema:
      service: dreame_vacuum.vacuum_clean_spot
      service_data:
        entity_id: '[[entity_id]]'
        points: '[[selection]]'
        repeats: '[[repeats]]'
```

#### With [Vacuum Card](https://github.com/denysdovhan/vacuum-card)

```yaml
type: custom:vacuum-card
entity: # Your vacuum entity
map: # Map Entity
map_refresh: 1
stats:
  default:
    - attribute: filter_left
      unit: '%'
      subtitle: Filter
    - attribute: side_brush_left
      unit: '%'
      subtitle: Side brush
    - attribute: main_brush_left
      unit: '%'
      subtitle: Main brush
    - attribute: sensor_dirty_left
      unit: '%'
      subtitle: Sensors
  cleaning:
    - attribute: cleaned_area
      unit: m2
      subtitle: Cleaned area
    - attribute: cleaning_time
      unit: min
      subtitle: Cleaning time
shortcuts:
  - name: Clean Room 1
    service: dreame_vacuum.vacuum_clean_segment
    service_data:
      entity_id: # Your vacuum entity
      segments: 1
    icon: mdi:sofa
  - name: Clean Room 2
    service: dreame_vacuum.vacuum_clean_segment
    service_data:
      entity_id: # Your vacuum entity
      segments: 2
    icon: mdi:bed-empty
  - name: Clean Room 3
    service: dreame_vacuum.vacuum_clean_segment
    service_data:
      entity_id: # Your vacuum entity
      segments: 3
    icon: mdi:silverware-fork-knife
```

#### With <a href="https://github.com/Hypfer/lovelace-valetudo-map-card" target="_blank">Valetudo Map Card</a>
 > Enable **Map Data** camera entity. 
<a href="https://my.home-assistant.io/redirect/entities/" target="_blank"><img src="https://my.home-assistant.io/badges/entities.svg" alt="Open your Home Assistant instance and show your entities." /></a>

```yaml
type: custom:valetudo-map-card
vacuum: # Your vacuum name not the entity id
rotate: 0 # Map rotation entity does not work on valetudo map card
dock_icon: mdi:lightning-bolt-circle
dock_color: rgb(105 178 141)
vacuum_color: rgb(110, 110, 110)
wall_color: rgb(159, 159, 159)
floor_color: rgb(221, 221, 221)
no_go_area_color: rgb(177, 0, 0)
no_mop_area_color: rgb(170, 47, 255)
virtual_wall_color: rgb(199, 0, 0)
virtual_wall_width: 1.5
currently_cleaned_zone_color: rgb(221, 221, 221)
path_color: rgb(255, 255, 255)
path_width: 1.5
segment_opacity: 1
segment_colors:
  - rgb(171, 199, 248)
  - rgb(249, 224, 125)
  - rgb(184, 227, 255)
  - rgb(184, 217, 141)
```

#### With <a href="https://github.com/benct/lovelace-xiaomi-vacuum-card" target="_blank">Xiaomi Vacuum Card</a> and Picture Entity Card
```yaml
type: picture-entity
entity: # Your vacuum entity
camera_image: # Your camera entity
show_state: false
show_name: false
camera_view: live
tap_action:
  action: none
hold_action:
  action: none
```

```yaml
type: custom:xiaomi-vacuum-card
entity: # Your vacuum entity
vendor: xiaomi
attributes:
  main_brush_life:
    label: 'Main Brush: '
    key: main_brush_left
    unit: '%'
    icon: mdi:car-turbocharger
  side_brush_life:
    label: 'Side Brush: '
    key: side_brush_left
    unit: '%'
    icon: mdi:pinwheel-outline
  filter_life:
    label: 'Filter: '
    key: filter_left
    unit: '%'
    icon: mdi:air-filter
  sensor_life:
    label: 'Sensor: '
    key: sensor_dirty_left
    unit: '%'
    icon: mdi:radar
  main_brush: false
  side_brush: false
  filter: false
  sensor: false

```

## To Do

- Integrated custom lovelace map card
- Shortcut editing
- Schedule editing
- Furniture editing
- DnD editing
- Live camera streaming
- Backend translations


## Contributing
To submit your changes please fork `dev` branch of this repository and open a pull request. 

## Thanks To

 - [xiaomi_vacuum](https://github.com/pooyashahidi/xiaomi_vacuum) by [@pooyashahidi](https://github.com/pooyashahidi)
 - [Xiaomi MIoT for Home Assistant](https://github.com/ha0y/xiaomi_miot_raw) by [@ha0y](https://github.com/ha0y)
 - [Xiaomi Cloud Map Extractor](https://github.com/PiotrMachowski/Home-Assistant-custom-components-Xiaomi-Cloud-Map-Extractor) by [@PiotrMachowski](https://github.com/PiotrMachowski)
 - Dreame cloud authentication by [@kuudori](https://github.com/kuudori)
 - Mova cloud help by [@r1si](https://github.com/r1si)


## Do not forget to support the project!

<a href="https://ko-fi.com/tasshack"><img width="300" src="https://raw.githubusercontent.com/Tasshack/dreame-vacuum/refs/heads/dev/.github/icons/kofi.png"/></a>

<a href="https://paypal.me/tasshackK"><img width="300" src="https://raw.githubusercontent.com/Tasshack/dreame-vacuum/refs/heads/dev/.github/icons/paypal.png"></a>

<a href="https://github.com/sponsors/Tasshack"><img width="300" src="https://raw.githubusercontent.com/Tasshack/dreame-vacuum/refs/heads/dev/.github/icons/github.png"></a>
