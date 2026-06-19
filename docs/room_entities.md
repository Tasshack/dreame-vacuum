# Room entities for customized cleaning
<img src="https://raw.githubusercontent.com/Tasshack/dreame-vacuum/master/docs/media/room_1_entities.png" width="450px">

Integration exposes and manages room entities for customized cleaning settings that are introduced on firmware version 1156. If *customized cleaning* feature is enabled, robot uses these settings on *cleaning* and *custom segment cleaning* jobs and cannot be overridden by start action parameters.

Room settings stored on current map data and only selected map custom cleaning settings can be accessed via the cloud api. Therefore integration shares same room entities with other saved maps and dynamically updates their entity names and icons respectively when selected map is changed. 

<img src="https://raw.githubusercontent.com/Tasshack/dreame-vacuum/master/docs/media/rooms_map_1.png" width="350px"><img src="https://raw.githubusercontent.com/Tasshack/dreame-vacuum/master/docs/media/rooms_map_2.png" width="350px">

Integration exposes rooms from all saved maps and updates their availability state according to the currently selected map.

<img src="https://raw.githubusercontent.com/Tasshack/dreame-vacuum/master/docs/media/room_3_map_1.png" width="350px"><img src="https://raw.githubusercontent.com/Tasshack/dreame-vacuum/master/docs/media/room_3_map_2.png" width="350px">

## Rooms card

With help of two custom cards you can generate a single card to manage all room settings with correct names and icons.

TODO

<a href="https://my.home-assistant.io/redirect/developer_template/" target="_blank"><img src="https://my.home-assistant.io/badges/developer_template.svg" alt="Open your Home Assistant instance and show your template developer tools." /></a>

```yaml
{# ----------------- PROVIDE YOUR OWN ENTITY ID HERE ----------------- #}
{% set vacuum_entity = "vacuum." %}
{# ------------------- DO NOT CHANGE ANYTHING BELOW ------------------- #}
{%- set vacuum_name = states[vacuum_entity].entity_id.replace('vacuum.', '') %} 
{%- set mop_pad = ('mop_pad_humidity' in states[vacuum_entity].attributes)|bool %}
{% set rooms = namespace(list=[]) %}
{%- if 'rooms' in states[vacuum_entity].attributes %}
{%- for map in states[vacuum_entity].attributes.rooms.values() %}  
    {%- for room in map %}      
    {%- if room.id not in rooms.list %}
        {%- set rooms.list = rooms.list + [room.id] %}
    {%- endif %}
    {%- endfor %}
{%- endfor %}
{%- endif %}
{%- set rooms.list = rooms.list|sort() %}

type: entities
title: Rooms
show_header_toggle: false
entities:
{%- for room in rooms.list %}
{%- set custom_cleaning_mode = states['select.' + vacuum_name + '_room_' + room|string + '_cleaning_mode'] != None %}
{%- set room_exists = "states['" + vacuum_entity + "'].attributes.cleaning_sequence && states['" + vacuum_entity + "'].attributes.cleaning_sequence.length > " + (loop.index - 1)|string  %} 
{%- set room_id = "(" + room_exists + " ? (states['" + vacuum_entity + "'].attributes.cleaning_sequence[" + (loop.index - 1)|string + "]) : " + room|string + ")" %}
{%- set current_room = "(vars[5].state == 'unavailable' && states['select." + vacuum_name + "_cleaning_mode'].state == 'unavailable' && states['" + vacuum_entity + "'].attributes.current_segment == vars[0])" %}
  - type: custom:config-template-card
    variables:
      - >- 
        {{ room_id }}
      - states['select.{{ vacuum_name }}_room_' + vars[0] + '_name'] 
      - states['select.{{ vacuum_name }}_room_' + vars[0] + '_suction_level']
      {%- if mop_pad %}
      - states['select.{{ vacuum_name }}_room_' + vars[0] + '_mop_pad_humidity']
      {%- else %}
      - states['select.{{ vacuum_name }}_room_' + vars[0] + '_water_volume']
      {%- endif %}
      - states['select.{{ vacuum_name }}_room_' + vars[0] + '_cleaning_times']
      - states['select.{{ vacuum_name }}_room_' + vars[0] + '_order']
      - >- 
        states['{{ vacuum_entity }}']
      - >-
        (vars[6].attributes.rooms && vars[6].attributes.selected_map ? vars[6].attributes.rooms[vars[6].attributes.selected_map].filter(function (e) { return states['select.{{ vacuum_name }}_room_' + e.id + '_order'] && states['select.{{ vacuum_name }}_room_' + e.id + '_order'].state != 'not_set' }).length : 0)
      - >-
        ({{ current_room }} ? 'var(--state-icon-active-color)' : 'var(--primary-text-color)')
      - >-
        (vars[6].attributes.cleaning_sequence ? 'inherit' : 'none')
      - >-
        (vars[5] && vars[5].state != 'unavailable' ? 'inherit' : 'none')
      - >-
        (vars[6].attributes.customized_cleaning && (!vars[6].attributes.active_segments || states['{{ vacuum_entity }}'].attributes.active_segments.includes(vars[0])) ? 'inherit' : 'none')        
      - >-
        (vars[5] && vars[5].state != 'not_set' ? 'inherit' : 'hidden')
      {%- if custom_cleaning_mode %}
      - states['select.{{ vacuum_name }}_room_' + vars[0] + '_cleaning_mode']
      {%- endif %}
    entities:
      - ${vars[1].entity_id}
      - ${vars[2].entity_id}
      - ${vars[3].entity_id}
      - ${vars[4].entity_id}
      - ${vars[5].entity_id}
      - ${vars[6].entity_id}
      {%- if custom_cleaning_mode %}
      - ${vars[13].entity_id}
      {%- endif %}
    card:
      type: conditional
      conditions:
        - entity: ${vars[1].entity_id}
          state_not: unavailable
      card:            
        type: custom:multiple-entity-row
        entity: ${vars[1].entity_id}
        show_state: false
        name: ${vars[1].state}
        entities:
        {%- if custom_cleaning_mode %}
          - icon: ${vars[13].attributes.icon}
            entity: ${vars[13].entity_id}
            name: ' '
            tap_action: 
              action: call-service
              service: dreame_vacuum.select_select_next
              service_data:
                entity_id: ${vars[13].entity_id}
            double_tap_action:
              action: call-service
              service: dreame_vacuum.select_select_previous
              service_data:
                entity_id: ${vars[13].entity_id}
            hold_action:
              action: more-info
            styles:
              display: ${vars[11]}
              pointer-events: >-
                ${vars[13].state != 'unavailable' ? 'inherit' : 'none'}
              width: 28px
              '--paper-item-icon-color': ${vars[8]}
        {%- endif %}
          - icon: ${vars[2].attributes.icon}
            entity: ${vars[2].entity_id}
            name: ' '
            tap_action: 
              action: call-service
              service: dreame_vacuum.select_select_next
              service_data:
                entity_id: ${vars[2].entity_id}
            double_tap_action:
              action: call-service
              service: dreame_vacuum.select_select_previous
              service_data:
                entity_id: ${vars[2].entity_id}
            hold_action:
              action: more-info
            styles:
              display: ${vars[11]}
              pointer-events: >-
                ${vars[2].state != 'unavailable' ? 'inherit' : 'none'}
              width: 28px
              '--paper-item-icon-color': ${vars[8]}
          - icon: ${vars[3].attributes.icon}
            entity: ${vars[3].entity_id}
            name: ' '
            tap_action:
              action: call-service
              service: dreame_vacuum.select_select_next
              service_data:
                entity_id: ${vars[3].entity_id}
            double_tap_action:
              action: call-service
              service: dreame_vacuum.select_select_previous
              service_data:
                entity_id: ${vars[3].entity_id}
            styles:
              display: ${vars[11]}
              pointer-events: >-
                ${vars[3].state != 'unavailable' ? 'inherit' : 'none'}
              width: 28px
              '--paper-item-icon-color': ${vars[8]}
          - icon: ${vars[4].attributes.icon}
            entity: ${vars[4].entity_id}
            name: ' '
            tap_action:
              action: call-service
              service: dreame_vacuum.select_select_next
              service_data:
                entity_id: ${vars[4].entity_id}
            double_tap_action:
              action: call-service
              service: dreame_vacuum.select_select_previous
              service_data:
                entity_id: ${vars[4].entity_id}
            hold_action:
              action: more-info
            styles:
              display: ${vars[11]}
              pointer-events: >-
                ${vars[4].state != 'unavailable' ? 'inherit' : 'none'}
              width: 28px
              '--paper-item-icon-color': ${vars[8]}
          - icon: mdi:chevron-down
            entity: ${vars[5].entity_id}
            name: ' '
            tap_action:
              action: call-service
              service: dreame_vacuum.select_select_next
              service_data:
                entity_id: ${vars[5].entity_id}
                cycle: false
            hold_action:
              action: more-info
            styles:
              display: ${vars[9]}
              visibility: ${vars[12]}
              margin-right: 0
              margin-left: 8px
              '--paper-item-icon-color': >-
                ${(vars[7] > {{ loop.index }} ? 'var(--primary-color)' : 'var(--state-unavailable-color)')}
              pointer-events: >-
                ${(vars[7] > {{ loop.index }} ? vars[10] : 'none')}
          - icon: mdi:chevron-up
            entity: ${vars[5].entity_id}
            name: ' '
            tap_action:
              action: call-service
              service: dreame_vacuum.select_select_previous
              service_data:
                entity_id: ${vars[5].entity_id}
                cycle: false
            hold_action:
              action: more-info
            styles:
              display: ${vars[9]}
              visibility: ${vars[12]}
              '--paper-item-icon-color': {{ 'var(--primary-color)' if loop.index > 1 else 'var(--state-unavailable-color)' }}
              pointer-events: {{ "${vars[10]}" if loop.index > 1 else 'none' }}
  {%- endfor %}
  - type: divider
  - entity: switch.{{vacuum_name}}_customized_cleaning
    name: Customized Cleaning    
{%- if states['switch.' + vacuum_name + '_cleaning_sequence'] is not none %}
  - entity: switch.{{vacuum_name}}_cleaning_sequence
    name: Cleaning Sequence
{%- endif %}
```

#### <a href="https://github.com/Tasshack/dreame-vacuum/blob/master/docs/entities.md#select-entities-for-rooms">For more information about room entities</a>
