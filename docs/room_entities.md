# Room entities for customized cleaning
<img src="https://raw.githubusercontent.com/Tasshack/dreame-vacuum/master/docs/media/room_1_entities.png" width="450px">

Integration exposes and manages room entities for customized cleaning settings that are introduced on firmware version 1156. If *customized cleaning* feature is enabled, robot uses these settings on *cleaning* and *custom segment cleaning* jobs and cannot be overridden by start action parameters.

Room settings stored on current map data and only selected map custom cleaning settings can be accessed via the cloud api. Therefore integration shares same room entities with other saved maps and dynamically updates their entity names and icons respectively when selected map is changed. 

<img src="https://raw.githubusercontent.com/Tasshack/dreame-vacuum/master/docs/media/rooms_map_1.png" width="350px"><img src="https://raw.githubusercontent.com/Tasshack/dreame-vacuum/master/docs/media/rooms_map_2.png" width="350px">

Integration exposes rooms from all saved maps and updates their availability state according to the currently selected map.

<img src="https://raw.githubusercontent.com/Tasshack/dreame-vacuum/master/docs/media/room_3_map_1.png" width="350px"><img src="https://raw.githubusercontent.com/Tasshack/dreame-vacuum/master/docs/media/room_3_map_2.png" width="350px">

With help of two custom cards you can generate a single card to manage all room settings with correct names and icons.

<a href="https://raw.githubusercontent.com/Tasshack/dreame-vacuum/master/docs/media/rooms.gif" target="_blank"><img src="https://raw.githubusercontent.com/Tasshack/dreame-vacuum/master/docs/media/rooms.gif" width="350px"><a href="https://raw.githubusercontent.com/Tasshack/dreame-vacuum/master/docs/media/custom_cleaning.gif" target="_blank"><img src="https://raw.githubusercontent.com/Tasshack/dreame-vacuum/master/docs/media/custom_cleaning.gif" width="350px"></a>

> <a href="https://github.com/iantrich/config-template-card" target="_blank">config-template-card</a> and <a href="https://github.com/benct/lovelace-multiple-entity-row" target="_blank">multiple-entity-row</a> custom cards are required with this template.

<a href="https://my.home-assistant.io/redirect/developer_template/" target="_blank"><img src="https://my.home-assistant.io/badges/developer_template.svg" alt="Open your Home Assistant instance and show your template developer tools." /></a>

```yaml
{# ----------------- PROVIDE YOUR OWN ENTITY IDS HERE ----------------- #}
{% set vacuum_entity = "vacuum." %}
{% set max_room_id = 8 %}
{# ------------------- DO NOT CHANGE ANYTHING BELOW ------------------- #}
{% set vacuum_name = states[vacuum_entity].entity_id.replace('vacuum.', '') %}
type: entities
entities:
{# Alternatively room ids can be acquired from vacuum or camera entities #}
{% for room in range(1, max_room_id) %}
{% set entity_id = "select." + vacuum_name + "_room_" + room|string %}
  - type: conditional
    conditions:
      - entity: {{ entity_id }}_name
        state_not: unavailable
    row:
      type: custom:config-template-card
      variables:
        - states['{{ entity_id }}_name']
        - states['{{ entity_id }}_fan_speed'].entity_id
        - states['{{ entity_id }}_water_level'].entity_id
        - states['{{ entity_id }}_repeats'].entity_id
        - states['{{ entity_id }}_order'].entity_id
      entities:
        - ${vars[0].entity_id}
        - ${vars[1]}
        - ${vars[2]}
        - ${vars[3]}
        - ${vars[4]}
      card:
        type: custom:multiple-entity-row
        entity: ${vars[0].entity_id}
        show_state: false
        name: ${vars[0].state}
        entities:
          - entity: ${vars[1]}
            name: Fan
            hide_if: unavailable
            tap_action:
              action: call-service
              service: dreame_vacuum.select_select_next
              service_data:
                entity_id: ${vars[1]}
            styles:
              width: 55px
          - entity: ${vars[2]}
            name: Water
            hide_if: unavailable
            tap_action:
              action: call-service
              service: dreame_vacuum.select_select_next
              service_data:
                entity_id: ${vars[2]}
            styles:
              width: 55px
          - entity: ${vars[3]}
            name: Repeats
            hide_if: unavailable
            tap_action:
              action: call-service
              service: dreame_vacuum.select_select_next
              service_data:
                entity_id: ${vars[3]}
            styles:
              width: 30px
          - entity: ${vars[4]}
            name: Order
            hide_if: unavailable
            styles:
              width: 35px
{%- endfor %}
```

#### <a href="https://github.com/Tasshack/dreame-vacuum/blob/master/docs/entities.md#select-entities-for-rooms">For more information about room entities.</a>