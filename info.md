[![version](https://img.shields.io/github/manifest-json/v/Tasshack/dreame-vacuum?filename=custom_components%2Fdreame_vacuum%2Fmanifest.json&color=slateblue)](https://github.com/Tasshack/dreame-vacuum/releases/latest)
![GitHub all releases](https://img.shields.io/github/downloads/Tasshack/dreame-vacuum/total)
![GitHub issues](https://img.shields.io/github/issues/Tasshack/dreame-vacuum)
[![HACS](https://img.shields.io/badge/HACS-Default-orange.svg?logo=HomeAssistantCommunityStore&logoColor=white)](https://github.com/hacs/integration)
[![Community Forum](https://img.shields.io/static/v1.svg?label=Community&message=Forum&color=41bdf5&logo=HomeAssistant&logoColor=white)](https://community.home-assistant.io/t/custom-component-dreame-vacuum/473026)
[![Ko-Fi](https://img.shields.io/static/v1.svg?label=%20&message=Ko-Fi&color=F16061&logo=ko-fi&logoColor=white)](https://www.ko-fi.com/Tasshack)
[![PayPal.Me](https://img.shields.io/static/v1.svg?label=%20&message=PayPal.Me&logo=paypal)](https://paypal.me/Tasshackk)

![Logo](https://raw.githubusercontent.com/Tasshack/dreame-vacuum/dev/docs/media/logo.png)

# Dreame vacuum integration for Home Assistant

Complete app replacement with Home Assistant for Dreame robot vacuums.

<p align="center">
    <img src="https://raw.githubusercontent.com/Tasshack/dreame-vacuum/master/docs/media/map.png" width="20%"><img src="https://raw.githubusercontent.com/Tasshack/dreame-vacuum/master/docs/media/map_app.png" width="20%"><img width=8%><img src="https://raw.githubusercontent.com/Tasshack/dreame-vacuum/master/docs/media/settings.png" width="20%"><img src="https://raw.githubusercontent.com/Tasshack/dreame-vacuum/master/docs/media/settings_app.png" width="20%">
</p>

## Features

- [Auto generated device entities](https://github.com/Tasshack/dreame-vacuum/blob/master/docs/entities.md)
- [Live and multi floor map support](https://github.com/Tasshack/dreame-vacuum/blob/master/docs/map.md)
- [Customized room cleaning entities](https://github.com/Tasshack/dreame-vacuum/blob/master/docs/room_entities.md)
- [Services for device and map with examples](https://github.com/Tasshack/dreame-vacuum/blob/master/docs/services.md)
- [Persistent notifications and error reporting](https://github.com/Tasshack/dreame-vacuum/blob/master/docs/notifications.md)
- [Events for automations](https://github.com/Tasshack/dreame-vacuum/blob/master/docs/events.md)
- [Valetudo map card support](#with-valetudo-map-card)

## Supported Devices
- **Dreame**
  - `dreame.vacuum.p2008` *(F9)*
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
  - `dreame.vacuum.p2041` *(1T)*
  - `dreame.vacuum.p2140a` *(2C)*
  - `dreame.vacuum.p2140` *(2C)*
  - `dreame.vacuum.p2140q` *(Mi Robot Vacuum-Mop 2)*
  - `dreame.vacuum.p2140p` *(Mi Robot Vacuum-Mop 2)*
  - `dreame.vacuum.p2140o` *(Mi Robot Vacuum-Mop 2)*
  - `dreame.vacuum.p2148o` *(Mi Robot Vacuum Mop Ultra Slim)*
  - `dreame.vacuum.p2041o` *(Mi Robot Vacuum-Mop 2 Pro+)*
- **MOVA** 
  - `dreame.vacuum.p2157` *(L600)*
  - `dreame.vacuum.p2156o` *(MOVA Z500)*

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

```yaml
type: custom:xiaomi-vacuum-map-card
entity: # Your vacuum entity
map_source:
  camera: # Map Entity
calibration_source:
  camera: true
vacuum_platform: Tasshack/dreame-vacuum
```

> Open card editor, click "Generate rooms config" button, check (adjust if needed) your config using yaml editor and save changes.
<img src="https://user-images.githubusercontent.com/6118709/189792603-c5ad2089-7405-4d1b-850d-77af8f170618.png">

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

## Thanks To

 - [xiaomi_vacuum](https://github.com/pooyashahidi/xiaomi_vacuum) by [@pooyashahidi](https://github.com/pooyashahidi)
 - [Xiaomi MIoT for Home Assistant](https://github.com/ha0y/xiaomi_miot_raw) by [@ha0y](https://github.com/ha0y)
 - [Xiaomi Cloud Map Extractor](https://github.com/PiotrMachowski/Home-Assistant-custom-components-Xiaomi-Cloud-Map-Extractor) by [@PiotrMachowski](https://github.com/PiotrMachowski)
 - [Valetudo](https://github.com/Hypfer/Valetudo) by [@Hypfer](https://github.com/Hypfer)


<a href='https://ko-fi.com/tasshack' target='_blank'><img height='36' style='border:0px;height:36px;' src='https://storage.ko-fi.com/cdn/kofi3.png?v=3' border='0' alt='Buy Me a Coffee at ko-fi.com' /></a>
<a href="https://paypal.me/tasshackK" target="_blank"><img src="https://www.paypalobjects.com/webstatic/mktg/logo/pp_cc_mark_37x23.jpg" border="0" alt="PayPal Logo" style="height: auto !important;width: auto !important;"></a>