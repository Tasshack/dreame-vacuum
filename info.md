[![version](https://img.shields.io/github/manifest-json/v/Tasshack/dreame-vacuum?filename=custom_components%2Fdreame_vacuum%2Fmanifest.json&color=green)](https://github.com/Tasshack/dreame-vacuum/releases/latest)
[![HACS](https://img.shields.io/badge/HACS-Default-orange.svg?logo=HomeAssistantCommunityStore&logoColor=white)](https://github.com/hacs/integration)
[![Community Forum](https://img.shields.io/static/v1.svg?label=Community&message=Forum&color=41bdf5&logo=HomeAssistant&logoColor=white)](https://community.home-assistant.io/t/custom-component-dreame-vacuum/473026)
[![But me a coffee](https://img.shields.io/static/v1.svg?label=%20&message=Buy%20me%20a%20coffee&color=6f4e37&logo=buy%20me%20a%20coffee&logoColor=white)](https://www.buymeacoffee.com/Tasshack)
[![PayPal.Me](https://img.shields.io/static/v1.svg?label=%20&message=PayPal.Me&logo=paypal)](https://paypal.me/Tasshackk)

![dreame Logo](https://cdn.shopify.com/s/files/1/0302/5276/1220/files/rsz_logo_-01_400x_2ecfe8c0-2756-4bd1-a3f4-593b1f73e335_284x.jpg "dreame Logo")

# Dreame vacuum integration for Home Assistant

Complete app replacement for Dreame second generation lidar robot vacuums and a Valetudo alternative for integrating your device to Home Assistant.

<p align="center">
    <img src="https://raw.githubusercontent.com/Tasshack/dreame-vacuum/master/docs/media/map.png" width="20%"><img src="https://raw.githubusercontent.com/Tasshack/dreame-vacuum/master/docs/media/map_app.png" width="20%"><img width=8%><img src="https://raw.githubusercontent.com/Tasshack/dreame-vacuum/master/docs/media/settings.png" width="20%"><img src="https://raw.githubusercontent.com/Tasshack/dreame-vacuum/master/docs/media/settings_app.png" width="20%">
</p>

## Features
All features completely reverse engineered from the official Mi Home app RN plugin for Z10 Pro with firmware version 1156.

- [Auto generated device entities](https://github.com/Tasshack/dreame-vacuum/blob/master/docs/entities.md)
- [Live and multi floor map support](https://github.com/Tasshack/dreame-vacuum/blob/master/docs/map.md)
- [Customized room cleaning entities](https://github.com/Tasshack/dreame-vacuum/blob/master/docs/room_entities.md)
- [Services for device and map with examples](https://github.com/Tasshack/dreame-vacuum/blob/master/docs/services.md)
- [Persistent notifications and error reporting](https://github.com/Tasshack/dreame-vacuum/blob/master/docs/notifications.md)
- [Events for automations](https://github.com/Tasshack/dreame-vacuum/blob/master/docs/events.md)
- [Valetudo map card support](#with-valetudo-map-card)
- Onboard scheduling support *(Coming soon)*

## Supported Devices
- **Dreame**
  - `dreame.vacuum.p2009` *(D9)*
  - `dreame.vacuum.p2259` *(D9 Max)*
  - `dreame.vacuum.p2187` *(D9 Pro)*
  - `dreame.vacuum.r2205` *(D10 Plus)*
  - `dreame.vacuum.p2029` *(L10 Pro)*
  - `dreame.vacuum.p2028a` *(L10 Plus)*
  - `dreame.vacuum.r2228o` *(L10s Ultra)*
  - `dreame.vacuum.r2215o` *(L10s Pro)*
  - `dreame.vacuum.r2216o` *(L10s Pro)*
  - `dreame.vacuum.p2028` *(Z10 Pro)*
  - `dreame.vacuum.p2027` *(W10)*
  - `dreame.vacuum.r2104` *(W10 Pro)*
  - `dreame.vacuum.r2251o` *(W10s)*
  - `dreame.vacuum.r2232a` *(W10s Pro)*
  - `dreame.vacuum.r2228` *(S10)*
  - `dreame.vacuum.r2211o` *(S10+)*
  - `dreame.vacuum.r2233` *(S10 Pro)*
  - `dreame.vacuum.r2247` *(S10 Pro Plus)*
  - `dreame.vacuum.r2246` *(S10 Plus)*
  - `dreame.vacuum.r2215` *(X10)*
  - `dreame.vacuum.r2235` *(X10 Ultra)*
- **Mijia**
  - `dreame.vacuum.p2036` *(Trouver LDS Finder)*
  - `dreame.vacuum.p2150o` *(Vacuum-Mop)*
  - `dreame.vacuum.p2150a` *(Vacuum-Mop 2 Ultra)*
  - `dreame.vacuum.p2150b` *(Vacuum-Mop 2 Ultra Set)*
  - `dreame.vacuum.p2114o` *(Self-Cleaning Robot Vacuum-Mop)* 
  - `dreame.vacuum.p2149o` *(Self-Cleaning Robot Vacuum-Mop Pro)*
  - `dreame.vacuum.r2254` *(1S)*
  - `dreame.vacuum.r2209` *(X10)*
  - `dreame.vacuum.p2114a` *(X10+)*
- **MOVA** 
  - `dreame.vacuum.p2157` *(L600)*

## Configuration
- Use this button: <a href="https://my.home-assistant.io/redirect/config_flow_start/?domain=dreame_vacuum" target="_blank"><img src="https://my.home-assistant.io/badges/config_flow_start.svg" alt="Open your Home Assistant instance and start setting up a new integration." /></a> or:
  - Add the **Dreame Vacuum** integration in Settings -> Devices & Services -> Add Integration
  - Select **Dreame Vacuum** from the list
  - Confirm form submission
- Select configuration type:

    <img src="https://raw.githubusercontent.com/Tasshack/dreame-vacuum/master/docs/media/config_flow.png" width="550px">

    <a href="https://github.com/Tasshack/dreame-vacuum/blob/master/docs/map.md" target="_blank">About map feature</a>

- Enter required credentials according to the selected configuration type. 
  > Please make sure that the devices are at same subnet for both configuration types. <a href="https://python-miio.readthedocs.io/en/latest/troubleshooting.html#discover-devices-across-subnets" target="_blank">python-miio article about this issue.</a>
- Set your device name and integration settings:

    <img src="https://raw.githubusercontent.com/Tasshack/dreame-vacuum/master/docs/media/config_flow_settings.png" width="350px">

    <a href="https://github.com/Tasshack/dreame-vacuum/blob/master/docs/notifications.md" target="_blank">About notifications feature</a><br><a href="https://github.com/Tasshack/dreame-vacuum/blob/master/docs/map.md#color-schemes" target="_blank">About map color schemes</a>
- Navigate to device page for disabling or enabling entities that you want to use.

    <a href="https://github.com/Tasshack/dreame-vacuum/blob/master/docs/entities.md" target="_blank">About entities</a>
 
## How to Use

Integration is compatible with all available Lovelace vacuum cards but if you want to use zone cleaning feature you can prefer the Xiaomi Vacuum Card.

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
      unit: m²
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

#### With Dreame Vacuum Card

*Coming Soon*

### Blueprints

- ##### [Disabling obstacle avoidance on selected room](https://github.com/Tasshack/dreame-vacuum/blob/master/blueprints/automation/disable_obstacle_avoidance_on_selected_room.yaml) 
    Line laser based 3D obstacle avoidance is great but it is affected from reflective surfaces can be found on kitchen or corridors. This integration exposes robots current room as entity so it can be used on automations.

    <a href="https://my.home-assistant.io/redirect/blueprint_import/?blueprint_url=https%3A%2F%2Fgithub.com%2FTasshack%2Fdreame-vacuum%2Fblob%2Fmaster%2Fblueprints%2Fautomation%2Fdisable_obstacle_avoidance_on_selected_room.yaml" target="_blank"><img src="https://my.home-assistant.io/badges/blueprint_import.svg" alt="Open your Home Assistant instance and show the blueprint import dialog with a specific blueprint pre-filled." /></a>

## Thanks To

 - [xiaomi_vacuum](https://github.com/pooyashahidi/xiaomi_vacuum) by [@pooyashahidi](https://github.com/pooyashahidi)
 - [Xiaomi MIoT for Home Assistant](https://github.com/ha0y/xiaomi_miot_raw) by [@ha0y](https://github.com/ha0y)
 - [Xiaomi Cloud Map Extractor](https://github.com/PiotrMachowski/Home-Assistant-custom-components-Xiaomi-Cloud-Map-Extractor) by [@PiotrMachowski](https://github.com/PiotrMachowski)
 - [Valetudo](https://github.com/Hypfer/Valetudo) by [@Hypfer](https://github.com/Hypfer)


<a href="https://www.buymeacoffee.com/tasshack" target="_blank"><img src="https://bmc-cdn.nyc3.digitaloceanspaces.com/BMC-button-images/custom_images/orange_img.png" alt="Buy Me A Coffee" style="height: auto !important;width: auto !important;" ></a>
<a href="https://paypal.me/tasshackK" target="_blank"><img src="https://www.paypalobjects.com/webstatic/mktg/logo/pp_cc_mark_37x23.jpg" border="0" alt="PayPal Logo" style="height: auto !important;width: auto !important;"></a>