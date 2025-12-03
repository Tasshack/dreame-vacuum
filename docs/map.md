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
- Cleaning mode
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

TODO ADD IMAGES

- **Dreame**: Icons from the official Dreame App.
- **Dreame Old**: Icons from the old version of the official Dreame App for VSLAM robots.
- **Mijia**: Icons from the official Mijia App.
- **Material**: Icons from the Material Design.

### Hidden Map Objects

Configurable map object rendering options: 

> Hidden Map objects can be selected from integration configuration options.
- **Room Colors**: Disable rooms with colors
- **Room Icons**: Disable room icons
- **Room Names**: Disable custom and default room names
- **Room Name Background**: Disable room name or icon background in room color
- **Room Order**: Disable cleaning sequence number of the room
- **Room Suction Level**: Disable customized cleaning suction level of the room
- **Room Water Volume**: Disable customized cleaning water volume of the room
- **Room Cleaning Times**: Disable customized cleaning times of the room
- **Room Cleaning Mode**: Disable customized cleaning cleaning mode of the room *(Only on supported devices)*
- **Path**: Disable paths
- **No Go Zones**: Disable no go zones
- **No Mop Zones**: Disable no mop zones
- **Virtual Walls**: Disable virtual walls
- **Pathways**: Disable pathways *(Only on supported devices)*
- **Passable Thresholds**: Disable Passable Thresholds *(Only on supported devices)*
- **Impassable Thresholds**: Disable Passable Thresholds *(Only on supported devices)*
- **Active Areas**: Disable active areas
- **Active Points**: Disable active points
- **Charger Icon**: Disable charger icon
- **Robot Icon**: Disable robot icon
- **Cleaning Direction**: Disable cleaning direction
- **AI Obstacle**: Disable obstacle icons *(Only on supported devices)*
- **Pet**: Disable pet icons *(Only on supported devices)*
- **Carpet Area**: Disable carpets *(Only on supported devices)*
- **Floor Material**: Disable floor material of the rooms *(Only on supported devices)*
- **Furnitures**: Disable 2D/3D furnitures *(Only on supported devices)*
- **Low-Lying Areas**: Disable Low-Lying areas *(Only on supported devices)*
- **Curtains**: Disable Curtains *(Only on supported devices)*
- **Ramps**: Disable Ramps *(Only on supported devices)*
- **Cruise Point**: Disable cruise points *(Only on supported devices)*

### Cleaning and Cruising History Maps

Cleaning and cruising history maps can be displayed via `Current Map` entity camera proxy.

`/api/camera_history_map_proxy/{entity_id}?token={access_token}&index={history_index}&cruising={is_cruising_history}&info={info_text}&dirty={dirty_map}`

- **entity_id**: Id of the current map entity (`camera.{vacuum_name}_map`)
- **access_token**: Camera entity access token (Can be acquired from `camera.{vacuum_name}_map` entity attributes)
- **history_index (optional, default = 1)**: Index of the history entry from 1 to 25 (Can be acquired from `sensor.{vacuum_name}_cleaning_history` entity attributes)
- **is_cruising_history (optional, default = 0)**: Can be set to 1 for getting the cruising history instead of the cleaning history (Only on devices with the cruising capability)
- **info_text (optional, default = 1)**: Can be set to 0 for rendering the map image transparent and without the top header text
- **dirty_map (optional, default = 0)**: Can be set to 1 for rendering the dirty map image of CleanGenius and second cleaning feature

> Returns `404` if the requested history map does not exists.

**Example:**

`http://local.homeassistant/api/camera_history_map_proxy/camera.vacuum_map?token=5df93cfcf8ecc23fa17b233ca938cc52f41e2b17a46ca291865be3f9ba64d89b&index=5`

#### Cleaning History Card

```yaml
type: custom:button-card
entity: camera. # Current map camera entity
label: Cleaning History # Optional
title: Cleaning History # Optional
icon: mdi:clipboard-text-clock
tap_action:
  action: none
entity_picture: >
  [[[ return function(t){const e=t._config;if(t.shadowRoot.querySelector("hui-error-card")&&!t._u)return t._u=!0,t.style.opacity=0,void setTimeout((function(){t.style.opacity=1,t.update()}),0);if(!t.__shouldUpdate){t._u=!1;const i=/v=([^&]*)/,o=/index=([^&]*)/;t.__shouldUpdate=t.shouldUpdate,t.shouldUpdate=function(t){const e=this;let o=e.__shouldUpdate(t);if(t&&t.has("_config"))return e.shouldUpdate=e.__shouldUpdate,e.__shouldUpdate=null,e._s=null,!0;const a=e._config,n=e._hass.states[a.entity],l=t.get("_hass"),s=l?l.states[a.entity]:null;if(o=l&&s!=n,!o)return!1;e._l&&(e._l.stateObj=n);let r=e.__items(e._hass);const c=e.__items(l)[0].join(",")!==r[0].join(",");if(e._i&&n&&!c){if(!c&&e._i&&n&&e._a){const t=n.attributes.access_token;if(t!=e._a&&(e._config.hold_action.url_path=e._i[1].replace(e._a,t),e._a=t,this._config.custom_fields))return!0}return e.hass=e._hass,!1}let d=0;const u=e._s;if(n){const t=n.attributes.access_token;if(!c&&t!=e._a){let i=n.attributes[a.picture_list+"_picture"];if(i)if("string"==typeof i||i instanceof String)i=i.replace(e._a,t);else for(let o=0;o<r[0].length;o++)i[r[0][o]]=i[r[0][o]].replace(e._a,t)}if(e._a=t,d=u&&""===u.value?0:parseInt(u.value),d<0||d>=r[0].length)d=0;else if(d>0&&r[0].length>0&&(d=0,e._i&&(d=r[0].indexOf(e._i[0]),-1===d))){d=0;let t=e._i[1].match(i)[1];for(let e=0;e<r[1].length;e++)if(t==r[1][e].match(i)[1]){d=e;break}}}return u.label=!(!a.label||!n)&&a.label,e.__populate(d,r[0],u),u.dispatchEvent(new Event("change")),o},t.__items=function(t){if(t){const e=t.states[this._config.entity];if(e&&e.attributes){const t=e.attributes[this._config.picture_list+"_picture"];if(t){if("string"==typeof t||t instanceof String)return[[""],[t]];{const e=Object.values(t);if(e.length)return[Object.keys(t),e]}}}}return[[],[]]},t.__populate=function(t,e,i){const o={"(Completed)":"✔️","(Interrupted)":"❌","(Manually Ignored)":"⛔","(Automatically Ignored)":"⭕","(Edited)":"📝","(Original)":"✅","(Backup)":"💾"},a=new RegExp(Object.keys(o).join("|").replaceAll(")","\\)").replaceAll("(","\\("),"g"),n=function(t){return t&&t.length?t.replace(a,(t=>o[t])):""};(t<0||t>=e.length)&&(t=0);let l="";for(let s=0;s<e.length;s++)l+='<mwc-list-item value="'+s+'"'+(t==s?" selected activated":"")+">"+n(e[s])+"</mwc-list-item>";i.innerHTML=l,i.value=t+"",i.selectedText=n(e[t])};const a="picture-selector",n=t.shadowRoot.querySelector("ha-card#"+a);n&&n.remove();const l=document.createElement("ha-card");let s;l.id=a,l.style.cssText="cursor:default;display:block;padding:12px 16px 16px;overflow:visible;border-bottom-left-radius:0;border-bottom-right-radius:0;border-bottom:none;",t.shadowRoot.children.length?t.shadowRoot.insertBefore(l,t.shadowRoot.children[0]):t.shadowRoot.appendChild(l),e.title&&e.title.length&&(" "!==e.title&&(s=document.createElement("h1"),s.className="card-header",s.style.padding="0 0 4px 0",s.innerHTML='<div class="name">'+e.title+"</div>",l.appendChild(s)),e.styles.grid||(e.styles.grid=[]),e.styles.grid=e.styles.grid.concat([{cursor:"default"},{display:"block"},{margin:"0 16px 16px"},{overflow:"hidden"},{"border-radius":"var(--ha-card-border-radius,12px)"},{"border-width":"var(--ha-card-border-width,1px)"},{"border-style":"solid"},{"border-color":"var(--ha-card-border-color,var(--divider-color,#e0e0e0))"},{background:"var(--input-disabled-fill-color);"}]));const r=t._hass.states[e.entity];t._a=r?r.attributes.access_token:"";const c=t.__items(t._hass),d=document.createElement("ha-select");if(d.style.cssText="width:auto;display:block;",e.icon&&e.icon.length){d.style.cssText+="margin:4px 0 0 40px;";const i=document.createElement("state-badge");i.stateObj=r,i.overrideIcon=e.icon,i.style.cssText="float:left;margin-top:12px;",l.appendChild(i),t._l=i}d.label=!(!e.label||!r)&&e.label,d.value="0",d.naturalMenuWidth=!0,1==c[0].length&&0==c[0][0].length&&(s?(d.style.display="none",t._l&&(t._l.style.display="none"),s.style.padding="0"):l.style.display="none"),t.__populate(0,c[0],d),l.appendChild(d),t._s=d;const u=function(e){const i=function(i){if(!i)return;const o=function(t){const e=t.target.parentElement.querySelectorAll("ha-circular-progress").forEach((t=>t.remove()));e&&e.remove(),t.target.style.cursor=""};i.onload=function(t){i.style.height="",t.target.style.opacity=1,o(t),t.target.onload=null},i.onerror=function(e){t._i=!1,o(e),t.update()},i.style.opacity=0,i.style.cursor="wait",e&&0==i.naturalHeight&&i.width&&(i.style.height=i.width+"px");const a=document.createElement("ha-circular-progress");a.active=!0,a.size="large",a.style.position="absolute",i.parentElement.appendChild(a)},o=t.shadowRoot.querySelector("#icon");o&&"IMG"==o.tagName?i(o):setTimeout((function(){const e=t.shadowRoot.querySelector("#icon");e&&0==e.naturalHeight&&e.width&&(e.style.height=e.width+"px"),i(e)}),0)};d.addEventListener('closed',function(e){e.stopPropagation()});if(d.onchange=function(e){if(""!=e.target.value){const a=t.__items(t._hass);if(0===a[1].length)return void(t._i=!1);const n=parseInt(e.target.value);if(n>=0&&n<a[1].length&&(!t._i||t._i[0]!=a[0][n]&&t._i[1]!=a[1][n])){if(t._i){if(t._i[0]=a[0][n],t._i[1].match(i)[1]===a[1][n].match(i)[1])return;t._i[1]=a[1][n]}else t._i=[a[0][n],a[1][n]];t._config.hold_action.url_path=t._i[1];const e=t._i[1].match(o);t._x=e&&e.length>1?e[1]:"",u(),t.update()}}},t._i=!1,t._config.hold_action={action:"url"},c[0].length){t._config.hold_action.url_path=c[1][0];const e=c[1][0].match(o);t._x=e&&e.length>1?e[1]:"";const i=t.shadowRoot.querySelector("#icon");i&&"IMG"==i.tagName?t._i=[c[0][0],c[1][0]]:(t.style.opacity=0,setTimeout((function(){t._i=[c[0][0],c[1][0]],u(!0),t.update(),t.style.opacity=1}),0))}}return t._i?t._i[1]+(e.extra_params&&e.extra_params.length?"&"+e.extra_params:""):void 0}(this) ]]]
picture_list: cleaning_history
size: 100%
show_name: false
show_entity_picture: true
styles:
  icon:
    - transition: opacity 180ms ease-in-out 0s
  card:
    - --mdc-ripple-color: rgba(0,0,0,0)
    - padding: 0
    - border-top-left-radius: 0
    - border-top-right-radius: 0
    - border-top: none
```

#### Cruising History Card

```yaml
type: custom:button-card
entity: camera. # Current map camera entity
label: Cruising History # Optional
title: Cruising History # Optional
icon: mdi:camera-marker
tap_action:
  action: none
entity_picture: >
  [[[ return function(t){const e=t._config;if(t.shadowRoot.querySelector("hui-error-card")&&!t._u)return t._u=!0,t.style.opacity=0,void setTimeout((function(){t.style.opacity=1,t.update()}),0);if(!t.__shouldUpdate){t._u=!1;const i=/v=([^&]*)/,o=/index=([^&]*)/;t.__shouldUpdate=t.shouldUpdate,t.shouldUpdate=function(t){const e=this;let o=e.__shouldUpdate(t);if(t&&t.has("_config"))return e.shouldUpdate=e.__shouldUpdate,e.__shouldUpdate=null,e._s=null,!0;const a=e._config,n=e._hass.states[a.entity],l=t.get("_hass"),s=l?l.states[a.entity]:null;if(o=l&&s!=n,!o)return!1;e._l&&(e._l.stateObj=n);let r=e.__items(e._hass);const c=e.__items(l)[0].join(",")!==r[0].join(",");if(e._i&&n&&!c){if(!c&&e._i&&n&&e._a){const t=n.attributes.access_token;if(t!=e._a&&(e._config.hold_action.url_path=e._i[1].replace(e._a,t),e._a=t,this._config.custom_fields))return!0}return e.hass=e._hass,!1}let d=0;const u=e._s;if(n){const t=n.attributes.access_token;if(!c&&t!=e._a){let i=n.attributes[a.picture_list+"_picture"];if(i)if("string"==typeof i||i instanceof String)i=i.replace(e._a,t);else for(let o=0;o<r[0].length;o++)i[r[0][o]]=i[r[0][o]].replace(e._a,t)}if(e._a=t,d=u&&""===u.value?0:parseInt(u.value),d<0||d>=r[0].length)d=0;else if(d>0&&r[0].length>0&&(d=0,e._i&&(d=r[0].indexOf(e._i[0]),-1===d))){d=0;let t=e._i[1].match(i)[1];for(let e=0;e<r[1].length;e++)if(t==r[1][e].match(i)[1]){d=e;break}}}return u.label=!(!a.label||!n)&&a.label,e.__populate(d,r[0],u),u.dispatchEvent(new Event("change")),o},t.__items=function(t){if(t){const e=t.states[this._config.entity];if(e&&e.attributes){const t=e.attributes[this._config.picture_list+"_picture"];if(t){if("string"==typeof t||t instanceof String)return[[""],[t]];{const e=Object.values(t);if(e.length)return[Object.keys(t),e]}}}}return[[],[]]},t.__populate=function(t,e,i){const o={"(Completed)":"✔️","(Interrupted)":"❌","(Manually Ignored)":"⛔","(Automatically Ignored)":"⭕","(Edited)":"📝","(Original)":"✅","(Backup)":"💾"},a=new RegExp(Object.keys(o).join("|").replaceAll(")","\\)").replaceAll("(","\\("),"g"),n=function(t){return t&&t.length?t.replace(a,(t=>o[t])):""};(t<0||t>=e.length)&&(t=0);let l="";for(let s=0;s<e.length;s++)l+='<mwc-list-item value="'+s+'"'+(t==s?" selected activated":"")+">"+n(e[s])+"</mwc-list-item>";i.innerHTML=l,i.value=t+"",i.selectedText=n(e[t])};const a="picture-selector",n=t.shadowRoot.querySelector("ha-card#"+a);n&&n.remove();const l=document.createElement("ha-card");let s;l.id=a,l.style.cssText="cursor:default;display:block;padding:12px 16px 16px;overflow:visible;border-bottom-left-radius:0;border-bottom-right-radius:0;border-bottom:none;",t.shadowRoot.children.length?t.shadowRoot.insertBefore(l,t.shadowRoot.children[0]):t.shadowRoot.appendChild(l),e.title&&e.title.length&&(" "!==e.title&&(s=document.createElement("h1"),s.className="card-header",s.style.padding="0 0 4px 0",s.innerHTML='<div class="name">'+e.title+"</div>",l.appendChild(s)),e.styles.grid||(e.styles.grid=[]),e.styles.grid=e.styles.grid.concat([{cursor:"default"},{display:"block"},{margin:"0 16px 16px"},{overflow:"hidden"},{"border-radius":"var(--ha-card-border-radius,12px)"},{"border-width":"var(--ha-card-border-width,1px)"},{"border-style":"solid"},{"border-color":"var(--ha-card-border-color,var(--divider-color,#e0e0e0))"},{background:"var(--input-disabled-fill-color);"}]));const r=t._hass.states[e.entity];t._a=r?r.attributes.access_token:"";const c=t.__items(t._hass),d=document.createElement("ha-select");if(d.style.cssText="width:auto;display:block;",e.icon&&e.icon.length){d.style.cssText+="margin:4px 0 0 40px;";const i=document.createElement("state-badge");i.stateObj=r,i.overrideIcon=e.icon,i.style.cssText="float:left;margin-top:12px;",l.appendChild(i),t._l=i}d.label=!(!e.label||!r)&&e.label,d.value="0",d.naturalMenuWidth=!0,1==c[0].length&&0==c[0][0].length&&(s?(d.style.display="none",t._l&&(t._l.style.display="none"),s.style.padding="0"):l.style.display="none"),t.__populate(0,c[0],d),l.appendChild(d),t._s=d;const u=function(e){const i=function(i){if(!i)return;const o=function(t){const e=t.target.parentElement.querySelectorAll("ha-circular-progress").forEach((t=>t.remove()));e&&e.remove(),t.target.style.cursor=""};i.onload=function(t){i.style.height="",t.target.style.opacity=1,o(t),t.target.onload=null},i.onerror=function(e){t._i=!1,o(e),t.update()},i.style.opacity=0,i.style.cursor="wait",e&&0==i.naturalHeight&&i.width&&(i.style.height=i.width+"px");const a=document.createElement("ha-circular-progress");a.active=!0,a.size="large",a.style.position="absolute",i.parentElement.appendChild(a)},o=t.shadowRoot.querySelector("#icon");o&&"IMG"==o.tagName?i(o):setTimeout((function(){const e=t.shadowRoot.querySelector("#icon");e&&0==e.naturalHeight&&e.width&&(e.style.height=e.width+"px"),i(e)}),0)};d.addEventListener('closed',function(e){e.stopPropagation()});if(d.onchange=function(e){if(""!=e.target.value){const a=t.__items(t._hass);if(0===a[1].length)return void(t._i=!1);const n=parseInt(e.target.value);if(n>=0&&n<a[1].length&&(!t._i||t._i[0]!=a[0][n]&&t._i[1]!=a[1][n])){if(t._i){if(t._i[0]=a[0][n],t._i[1].match(i)[1]===a[1][n].match(i)[1])return;t._i[1]=a[1][n]}else t._i=[a[0][n],a[1][n]];t._config.hold_action.url_path=t._i[1];const e=t._i[1].match(o);t._x=e&&e.length>1?e[1]:"",u(),t.update()}}},t._i=!1,t._config.hold_action={action:"url"},c[0].length){t._config.hold_action.url_path=c[1][0];const e=c[1][0].match(o);t._x=e&&e.length>1?e[1]:"";const i=t.shadowRoot.querySelector("#icon");i&&"IMG"==i.tagName?t._i=[c[0][0],c[1][0]]:(t.style.opacity=0,setTimeout((function(){t._i=[c[0][0],c[1][0]],u(!0),t.update(),t.style.opacity=1}),0))}}return t._i?t._i[1]+(e.extra_params&&e.extra_params.length?"&"+e.extra_params:""):void 0}(this) ]]]
picture_list: cruising_history
size: 100%
show_name: false
show_entity_picture: true
styles:
  icon:
    - transition: opacity 180ms ease-in-out 0s
  card:
    - --mdc-ripple-color: rgba(0,0,0,0)
    - padding: 0
    - border-top-left-radius: 0
    - border-top-right-radius: 0
    - border-top: none
```

### Obstacle Photos

Map obstacle photos be displayed via `Current Map` entity camera proxy.

`/api/camera_map_obstacle_proxy/{entity_id}?token={access_token}&index={obstacle_index}&crop={is_cropped}&file={download_file}`

- **entity_id**: Id of the current map entity (`camera.{vacuum_name}_map`)
- **access_token**: Camera entity access token (Can be acquired from `camera.{vacuum_name}_map` entity attributes)
- **obstacle_index (optional, default = 1)**: Index of the obstacle (Can be acquired from `camera.{vacuum_name}_map` entity attributes)
- **is_cropped (optional, default = 1)**: App renders the obstacle photos as cropped to prevent displaying the borders on some devices. This parameter can be set to 0 for rendering the original obstacle image.
- **download_file (optional, default = 0)**: Can be set to 1 for downloading the obstacle picture

> Returns `404` if the requested obstacle does not exists.

**Example:**

`http://local.homeassistant/api/camera_map_obstacle_proxy/camera.vacuum_map?token=5df93cfcf8ecc23fa17b233ca938cc52f41e2b17a46ca291865be3f9ba64d89b&index=2&crop=1`

#### Obstacles Card

```yaml
type: custom:button-card
entity: camera. # Current map camera entity
label: Obstacles # Optional
title: null # Optional
icon: mdi:traffic-cone
entity_picture: >
  [[[ return function(t){const e=t._config;if(t.shadowRoot.querySelector("hui-error-card")&&!t._u)return t._u=!0,t.style.opacity=0,void setTimeout((function(){t.style.opacity=1,t.update()}),0);if(!t.__shouldUpdate){t._u=!1;const i=/v=([^&]*)/,o=/index=([^&]*)/;t.__shouldUpdate=t.shouldUpdate,t.shouldUpdate=function(t){const e=this;let o=e.__shouldUpdate(t);if(t&&t.has("_config"))return e.shouldUpdate=e.__shouldUpdate,e.__shouldUpdate=null,e._s=null,!0;const a=e._config,n=e._hass.states[a.entity],l=t.get("_hass"),s=l?l.states[a.entity]:null;if(o=l&&s!=n,!o)return!1;e._l&&(e._l.stateObj=n);let r=e.__items(e._hass);const c=e.__items(l)[0].join(",")!==r[0].join(",");if(e._i&&n&&!c){if(!c&&e._i&&n&&e._a){const t=n.attributes.access_token;if(t!=e._a&&(e._config.hold_action.url_path=e._i[1].replace(e._a,t),e._a=t,this._config.custom_fields))return!0}return e.hass=e._hass,!1}let d=0;const u=e._s;if(n){const t=n.attributes.access_token;if(!c&&t!=e._a){let i=n.attributes[a.picture_list+"_picture"];if(i)if("string"==typeof i||i instanceof String)i=i.replace(e._a,t);else for(let o=0;o<r[0].length;o++)i[r[0][o]]=i[r[0][o]].replace(e._a,t)}if(e._a=t,d=u&&""===u.value?0:parseInt(u.value),d<0||d>=r[0].length)d=0;else if(d>0&&r[0].length>0&&(d=0,e._i&&(d=r[0].indexOf(e._i[0]),-1===d))){d=0;let t=e._i[1].match(i)[1];for(let e=0;e<r[1].length;e++)if(t==r[1][e].match(i)[1]){d=e;break}}}return u.label=!(!a.label||!n)&&a.label,e.__populate(d,r[0],u),u.dispatchEvent(new Event("change")),o},t.__items=function(t){if(t){const e=t.states[this._config.entity];if(e&&e.attributes){const t=e.attributes[this._config.picture_list+"_picture"];if(t){if("string"==typeof t||t instanceof String)return[[""],[t]];{const e=Object.values(t);if(e.length)return[Object.keys(t),e]}}}}return[[],[]]},t.__populate=function(t,e,i){const o={"(Completed)":"✔️","(Interrupted)":"❌","(Manually Ignored)":"⛔","(Automatically Ignored)":"⭕","(Edited)":"📝","(Original)":"✅","(Backup)":"💾"},a=new RegExp(Object.keys(o).join("|").replaceAll(")","\\)").replaceAll("(","\\("),"g"),n=function(t){return t&&t.length?t.replace(a,(t=>o[t])):""};(t<0||t>=e.length)&&(t=0);let l="";for(let s=0;s<e.length;s++)l+='<mwc-list-item value="'+s+'"'+(t==s?" selected activated":"")+">"+n(e[s])+"</mwc-list-item>";i.innerHTML=l,i.value=t+"",i.selectedText=n(e[t])};const a="picture-selector",n=t.shadowRoot.querySelector("ha-card#"+a);n&&n.remove();const l=document.createElement("ha-card");let s;l.id=a,l.style.cssText="cursor:default;display:block;padding:12px 16px 16px;overflow:visible;border-bottom-left-radius:0;border-bottom-right-radius:0;border-bottom:none;",t.shadowRoot.children.length?t.shadowRoot.insertBefore(l,t.shadowRoot.children[0]):t.shadowRoot.appendChild(l),e.title&&e.title.length&&(" "!==e.title&&(s=document.createElement("h1"),s.className="card-header",s.style.padding="0 0 4px 0",s.innerHTML='<div class="name">'+e.title+"</div>",l.appendChild(s)),e.styles.grid||(e.styles.grid=[]),e.styles.grid=e.styles.grid.concat([{cursor:"default"},{display:"block"},{margin:"0 16px 16px"},{overflow:"hidden"},{"border-radius":"var(--ha-card-border-radius,12px)"},{"border-width":"var(--ha-card-border-width,1px)"},{"border-style":"solid"},{"border-color":"var(--ha-card-border-color,var(--divider-color,#e0e0e0))"},{background:"var(--input-disabled-fill-color);"}]));const r=t._hass.states[e.entity];t._a=r?r.attributes.access_token:"";const c=t.__items(t._hass),d=document.createElement("ha-select");if(d.style.cssText="width:auto;display:block;",e.icon&&e.icon.length){d.style.cssText+="margin:4px 0 0 40px;";const i=document.createElement("state-badge");i.stateObj=r,i.overrideIcon=e.icon,i.style.cssText="float:left;margin-top:12px;",l.appendChild(i),t._l=i}d.label=!(!e.label||!r)&&e.label,d.value="0",d.naturalMenuWidth=!0,1==c[0].length&&0==c[0][0].length&&(s?(d.style.display="none",t._l&&(t._l.style.display="none"),s.style.padding="0"):l.style.display="none"),t.__populate(0,c[0],d),l.appendChild(d),t._s=d;const u=function(e){const i=function(i){if(!i)return;const o=function(t){const e=t.target.parentElement.querySelectorAll("ha-circular-progress").forEach((t=>t.remove()));e&&e.remove(),t.target.style.cursor=""};i.onload=function(t){i.style.height="",t.target.style.opacity=1,o(t),t.target.onload=null},i.onerror=function(e){t._i=!1,o(e),t.update()},i.style.opacity=0,i.style.cursor="wait",e&&0==i.naturalHeight&&i.width&&(i.style.height=i.width+"px");const a=document.createElement("ha-circular-progress");a.active=!0,a.size="large",a.style.position="absolute",i.parentElement.appendChild(a)},o=t.shadowRoot.querySelector("#icon");o&&"IMG"==o.tagName?i(o):setTimeout((function(){const e=t.shadowRoot.querySelector("#icon");e&&0==e.naturalHeight&&e.width&&(e.style.height=e.width+"px"),i(e)}),0)};d.addEventListener('closed',function(e){e.stopPropagation()});if(d.onchange=function(e){if(""!=e.target.value){const a=t.__items(t._hass);if(0===a[1].length)return void(t._i=!1);const n=parseInt(e.target.value);if(n>=0&&n<a[1].length&&(!t._i||t._i[0]!=a[0][n]&&t._i[1]!=a[1][n])){if(t._i){if(t._i[0]=a[0][n],t._i[1].match(i)[1]===a[1][n].match(i)[1])return;t._i[1]=a[1][n]}else t._i=[a[0][n],a[1][n]];t._config.hold_action.url_path=t._i[1];const e=t._i[1].match(o);t._x=e&&e.length>1?e[1]:"",u(),t.update()}}},t._i=!1,t._config.hold_action={action:"url"},c[0].length){t._config.hold_action.url_path=c[1][0];const e=c[1][0].match(o);t._x=e&&e.length>1?e[1]:"";const i=t.shadowRoot.querySelector("#icon");i&&"IMG"==i.tagName?t._i=[c[0][0],c[1][0]]:(t.style.opacity=0,setTimeout((function(){t._i=[c[0][0],c[1][0]],u(!0),t.update(),t.style.opacity=1}),0))}}return t._i?t._i[1]+(e.extra_params&&e.extra_params.length?"&"+e.extra_params:""):void 0}(this) ]]]
picture_list: obstacle
size: 100%
show_entity_picture: true
show_name: false
custom_fields:
  buttons:
    card:
      type: custom:button-card
      name: >
        [[[ return (!this.__c || this.__c(this.__o()) ? 'Cancel Ignore' : 'Ignore Obstacle'); ]]]
      icon: >
        [[[ return (!this.__c || this.__c(this.__o()) ? 'mdi:eye' : 'mdi:eye-off'); ]]]
      confirmation: >
        [[[ return this.__c && !this.__c(this.__o()); ]]]
      size: 24px
      tap_action:
        action: call-service
        service: dreame_vacuum.vacuum_set_obstacle_ignore
        data: >
          [[[ return function(t){t.__o||(t.__o=function(){const n=t._hass.states[t._config.entity];return n&&n.attributes.obstacles&&n.attributes.obstacles[t._i?t._x:""]},t.__c=function(t){return t&&t.ignore_status&&"Not Ignored"!==t.ignore_status},t.__d=function(t){return t&&t.ignore_status&&t.ignore_status.indexOf("Automatically")>=0});const n=t.__o();if(n)return{entity_id:t._config.entity.replace("camera.","vacuum.").substring(0,t._config.entity.lastIndexOf("_map")),x:n.x,y:n.y,obstacle_ignored:!t.__c(n)}}(this); ]]]
      styles:
        grid:
          - display: contents
        img_cell:
          - display: contents
        name:
          - color: >
              [[[ return (!this.__d || this.__d(this.__o()) ? 'var(--state-icon-unavailable-color)' : 'var(--primary-text-color)'); ]]]
        icon:
          - color: >
              [[[ return (!this.__d || this.__d(this.__o()) ? 'var(--state-icon-unavailable-color)' : 'var(--primary-text-color)'); ]]]
          - margin: 0 6px 0 0
        card:
          - background-color: >
              [[[ return (!this.__d || this.__d(this.__o()) ? 'var(--state-unavailable-color)' : 'var(--primary-color)'); ]]]
          - pointer-events: >
              [[[ return (!this.__d || this.__d(this.__o()) ? 'none' : 'auto'); ]]]
          - border-radius: 100px
          - max-width: 200px
          - max-height: 48px
          - padding: 8px 24px
styles:
  custom_fields:
    buttons:
      - cursor: >
          [[[ return (!this.__d || this.__d(this.__o()) ? 'not-allowed' : 'default'); ]]]
      - margin: 16px
      - display: >
          [[[ const o = this.__o(); return (o && o.ignore_status ? 'inline-block': 'none'); ]]]
      - width: auto
  grid:
    - display: block
  icon:
    - transition: opacity 180ms ease-in-out 0s
  card:
    - '--mdc-ripple-color': rgba(0,0,0,0)
    - padding: 0
    - border-top-left-radius: 0
    - border-top-right-radius: 0
    - border-top: none
```


#### Obstacle Photos from History Maps

Map obstacle photos for history maps be displayed via `Current Map` entity camera proxy. 

`/api/camera_map_obstacle_history_proxy/{entity_id}?token={access_token}&history_index={history_index}&cruising={is_cruising_history}&index={obstacle_index}&crop={is_cropped}&file={download_file}`

- **entity_id**: Id of the current map entity (`camera.{vacuum_name}_map`)
- **access_token**: Camera entity access token (Can be acquired from `camera.{vacuum_name}_map` entity attributes)
- **history_index (optional, default = 1)**: Index of the history entry from 1 to 25 (Can be acquired from `sensor.{vacuum_name}_cleaning_history` entity attributes)
- **is_cruising_history (optional, default = 0)**: Can be set to 1 for getting the cruising history instead of the cleaning history (Only on devices with the cruising capability)
- **obstacle_index (optional, default = 1)**: Index of the obstacle (Can be acquired from `camera.{vacuum_name}_map` entity attributes)
- **is_cropped (optional, default = 1)**: App renders the obstacle photos as cropped to prevent displaying the borders on some devices. This parameter can be set to 0 for rendering the original obstacle image.
- **download_file (optional, default = 0)**: Can be set to 1 for downloading the obstacle picture

> Returns `404` if the requested history map or obstacle does not exists.

**Example:**

`http://local.homeassistant/api/camera_map_obstacle_history_proxy/camera.vacuum_map?token=5df93cfcf8ecc23fa17b233ca938cc52f41e2b17a46ca291865be3f9ba64d89b&history_index=2&index=3`

### Backup and Recovery

Recovery maps can be displayed and downloaded via related `Saved or Current Map` entity camera proxy.
> - Cloud storage does not store the map recovery files forever. Even if recovery map can be rendered, map cannot be restored to that state because cloud may not have the file anymore. This usually happens if the map has been created more than a year ago.
> - Downloading a recovery map file for later use of restoring the map is an exclusive feature for this integration and cannot be done via the App.

`/api/camera_recovery_map_proxy/{entity_id}?token={access_token}&index={recovery_map_index}&file={download_file}&info={info_text}`

- **entity_id**: Id of the current map entity (`camera.{vacuum_name}_map(_{map_index})`)
- **access_token**: Camera entity access token (Can be acquired from `camera.{vacuum_name}_map_{map_index}` entity attributes)
- **obstacle_index (optional, default = 1)**: Index of the recovery map entry (Can be acquired from `camera.{vacuum_name}_map_{map_index}` entity attributes)
- **download_file (optional, default = 0)**: Can be set to 1 for downloading the recovery map file for restoring the map later (Please not that recovery files are matched with the map ids cannot be used for recovering the maps after a hard reset)
- **info_text (optional, default = 1)**: Can be set to 0 for rendering the map image transparent and without the top header text

> Returns `404` if the requested recovery map does not exists.

**Example for displaying the recovery map:**

`http://local.homeassistant/api/camera_recovery_map_proxy/camera.vacuum_map_1?token=5df93cfcf8ecc23fa17b233ca938cc52f41e2b17a46ca291865be3f9ba64d89b&index=2`

**Example for downloading the recovery map file:**

`http://local.homeassistant/api/camera_recovery_map_proxy/camera.vacuum_map_1?token=5df93cfcf8ecc23fa17b233ca938cc52f41e2b17a46ca291865be3f9ba64d89b&index=2&file=1`

<a href="https://github.com/Tasshack/dreame-vacuum/blob/dev/docs/services.md#dreame_vacuumvacuum_restore_map" target="_blank">**How to restore the map**</a>

<a href="https://github.com/Tasshack/dreame-vacuum/blob/dev/docs/services.md#dreame_vacuumvacuum_backup_map" target="_blank">**How to trigger backup to the cloud (Only on supported devices)**</a>

#### Map Recovery Card

```yaml
type: custom:button-card
entity: camera. # Current or saved map camera entity
label: Recovery Maps # Optional
title: Restore Map # Optional 
extra_params: info=0 # For transparent map
icon: mdi:file-restore
entity_picture: >
  [[[ return function(t){const e=t._config;if(t.shadowRoot.querySelector("hui-error-card")&&!t._u)return t._u=!0,t.style.opacity=0,void setTimeout((function(){t.style.opacity=1,t.update()}),0);if(!t.__shouldUpdate){t._u=!1;const i=/v=([^&]*)/,o=/index=([^&]*)/;t.__shouldUpdate=t.shouldUpdate,t.shouldUpdate=function(t){const e=this;let o=e.__shouldUpdate(t);if(t&&t.has("_config"))return e.shouldUpdate=e.__shouldUpdate,e.__shouldUpdate=null,e._s=null,!0;const a=e._config,n=e._hass.states[a.entity],l=t.get("_hass"),s=l?l.states[a.entity]:null;if(o=l&&s!=n,!o)return!1;e._l&&(e._l.stateObj=n);let r=e.__items(e._hass);const c=e.__items(l)[0].join(",")!==r[0].join(",");if(e._i&&n&&!c){if(!c&&e._i&&n&&e._a){const t=n.attributes.access_token;if(t!=e._a&&(e._config.hold_action.url_path=e._i[1].replace(e._a,t),e._a=t,this._config.custom_fields))return!0}return e.hass=e._hass,!1}let d=0;const u=e._s;if(n){const t=n.attributes.access_token;if(!c&&t!=e._a){let i=n.attributes[a.picture_list+"_picture"];if(i)if("string"==typeof i||i instanceof String)i=i.replace(e._a,t);else for(let o=0;o<r[0].length;o++)i[r[0][o]]=i[r[0][o]].replace(e._a,t)}if(e._a=t,d=u&&""===u.value?0:parseInt(u.value),d<0||d>=r[0].length)d=0;else if(d>0&&r[0].length>0&&(d=0,e._i&&(d=r[0].indexOf(e._i[0]),-1===d))){d=0;let t=e._i[1].match(i)[1];for(let e=0;e<r[1].length;e++)if(t==r[1][e].match(i)[1]){d=e;break}}}return u.label=!(!a.label||!n)&&a.label,e.__populate(d,r[0],u),u.dispatchEvent(new Event("change")),o},t.__items=function(t){if(t){const e=t.states[this._config.entity];if(e&&e.attributes){const t=e.attributes[this._config.picture_list+"_picture"];if(t){if("string"==typeof t||t instanceof String)return[[""],[t]];{const e=Object.values(t);if(e.length)return[Object.keys(t),e]}}}}return[[],[]]},t.__populate=function(t,e,i){const o={"(Completed)":"✔️","(Interrupted)":"❌","(Manually Ignored)":"⛔","(Automatically Ignored)":"⭕","(Edited)":"📝","(Original)":"✅","(Backup)":"💾"},a=new RegExp(Object.keys(o).join("|").replaceAll(")","\\)").replaceAll("(","\\("),"g"),n=function(t){return t&&t.length?t.replace(a,(t=>o[t])):""};(t<0||t>=e.length)&&(t=0);let l="";for(let s=0;s<e.length;s++)l+='<mwc-list-item value="'+s+'"'+(t==s?" selected activated":"")+">"+n(e[s])+"</mwc-list-item>";i.innerHTML=l,i.value=t+"",i.selectedText=n(e[t])};const a="picture-selector",n=t.shadowRoot.querySelector("ha-card#"+a);n&&n.remove();const l=document.createElement("ha-card");let s;l.id=a,l.style.cssText="cursor:default;display:block;padding:12px 16px 16px;overflow:visible;border-bottom-left-radius:0;border-bottom-right-radius:0;border-bottom:none;",t.shadowRoot.children.length?t.shadowRoot.insertBefore(l,t.shadowRoot.children[0]):t.shadowRoot.appendChild(l),e.title&&e.title.length&&(" "!==e.title&&(s=document.createElement("h1"),s.className="card-header",s.style.padding="0 0 4px 0",s.innerHTML='<div class="name">'+e.title+"</div>",l.appendChild(s)),e.styles.grid||(e.styles.grid=[]),e.styles.grid=e.styles.grid.concat([{cursor:"default"},{display:"block"},{margin:"0 16px 16px"},{overflow:"hidden"},{"border-radius":"var(--ha-card-border-radius,12px)"},{"border-width":"var(--ha-card-border-width,1px)"},{"border-style":"solid"},{"border-color":"var(--ha-card-border-color,var(--divider-color,#e0e0e0))"},{background:"var(--input-disabled-fill-color);"}]));const r=t._hass.states[e.entity];t._a=r?r.attributes.access_token:"";const c=t.__items(t._hass),d=document.createElement("ha-select");if(d.style.cssText="width:auto;display:block;",e.icon&&e.icon.length){d.style.cssText+="margin:4px 0 0 40px;";const i=document.createElement("state-badge");i.stateObj=r,i.overrideIcon=e.icon,i.style.cssText="float:left;margin-top:12px;",l.appendChild(i),t._l=i}d.label=!(!e.label||!r)&&e.label,d.value="0",d.naturalMenuWidth=!0,1==c[0].length&&0==c[0][0].length&&(s?(d.style.display="none",t._l&&(t._l.style.display="none"),s.style.padding="0"):l.style.display="none"),t.__populate(0,c[0],d),l.appendChild(d),t._s=d;const u=function(e){const i=function(i){if(!i)return;const o=function(t){const e=t.target.parentElement.querySelectorAll("ha-circular-progress").forEach((t=>t.remove()));e&&e.remove(),t.target.style.cursor=""};i.onload=function(t){i.style.height="",t.target.style.opacity=1,o(t),t.target.onload=null},i.onerror=function(e){t._i=!1,o(e),t.update()},i.style.opacity=0,i.style.cursor="wait",e&&0==i.naturalHeight&&i.width&&(i.style.height=i.width+"px");const a=document.createElement("ha-circular-progress");a.active=!0,a.size="large",a.style.position="absolute",i.parentElement.appendChild(a)},o=t.shadowRoot.querySelector("#icon");o&&"IMG"==o.tagName?i(o):setTimeout((function(){const e=t.shadowRoot.querySelector("#icon");e&&0==e.naturalHeight&&e.width&&(e.style.height=e.width+"px"),i(e)}),0)};d.addEventListener('closed',function(e){e.stopPropagation()});if(d.onchange=function(e){if(""!=e.target.value){const a=t.__items(t._hass);if(0===a[1].length)return void(t._i=!1);const n=parseInt(e.target.value);if(n>=0&&n<a[1].length&&(!t._i||t._i[0]!=a[0][n]&&t._i[1]!=a[1][n])){if(t._i){if(t._i[0]=a[0][n],t._i[1].match(i)[1]===a[1][n].match(i)[1])return;t._i[1]=a[1][n]}else t._i=[a[0][n],a[1][n]];t._config.hold_action.url_path=t._i[1];const e=t._i[1].match(o);t._x=e&&e.length>1?e[1]:"",u(),t.update()}}},t._i=!1,t._config.hold_action={action:"url"},c[0].length){t._config.hold_action.url_path=c[1][0];const e=c[1][0].match(o);t._x=e&&e.length>1?e[1]:"";const i=t.shadowRoot.querySelector("#icon");i&&"IMG"==i.tagName?t._i=[c[0][0],c[1][0]]:(t.style.opacity=0,setTimeout((function(){t._i=[c[0][0],c[1][0]],u(!0),t.update(),t.style.opacity=1}),0))}}return t._i?t._i[1]+(e.extra_params&&e.extra_params.length?"&"+e.extra_params:""):void 0}(this) ]]]
picture_list: recovery_map
size: 100%
show_entity_picture: true
show_name: false
custom_fields:
  buttons:
    card:
      type: horizontal-stack
      cards:
        - type: custom:button-card
          name: Restore
          icon: mdi:restore
          size: 24px
          tap_action:
            action: call-service
            service: dreame_vacuum.vacuum_restore_map
            data: 
              entity_id: |
                [[[ return (this._config.entity ? this._config.entity.replace('camera.','vacuum.').substring(0, this._config.entity.lastIndexOf('_map')) : ''); ]]]
              recovery_map_index: |
                [[[ return this._x ? parseInt(this._x) : 99 ]]]
          confirmation: true
          styles:
            grid:
              - display: contents
            img_cell:
              - display: contents
            icon:
              - margin: 0 6px 0 0
              - color: var(--primary-text-color)
            card:
              - border-radius: 100px
              - background-color: var(--primary-color)
        - type: custom:button-card
          name: Download
          icon: mdi:download
          size: 24px
          tap_action:
            action: url
            url_path: |
              [[[ return (this._x ? this._config.hold_action.url_path + '&file=1' : ''); ]]]
          styles:
            grid:
              - display: contents
            img_cell:
              - display: contents
            icon:
              - margin: 0 6px 0 0
              - color: var(--primary-text-color)
            card:
              - border-radius: 100px
              - background-color: var(--primary-color)
styles:
  custom_fields:
    buttons:
      - '--horizontal-stack-card-margin': 0 8px
      - padding: 0 16px 16px
      - display: >
          [[[ return (this._i ? 'block': 'none');]]]
  grid:
    - display: block
  icon:
    - transition: opacity 180ms ease-in-out 0s
  card:
    - '--mdc-ripple-color': rgba(0,0,0,0)
    - padding: 0
    - border-top-left-radius: 0
    - border-top-right-radius: 0
    - border-top: none
```

### WiFi Map

Saved WiFi maps can be displayed using <a href="https://github.com/Tasshack/dreame-vacuum/blob/dev/docs/entities.md#camera" target="_blank">`Saved WiFi Map` camera entities</a> (disabled by default) or alternatively via related `Saved or Current Map` entity camera proxy.

> WiFi maps for all saved maps may not be available on the device.

`/api/camera_wifi_map_proxy/{entity_id}?token={access_token}&info={info_text}`

- **entity_id**: Id of the current map entity (`camera.{vacuum_name}_map(_{map_index})`)
- **access_token**: Camera entity access token (Can be acquired from `camera.{vacuum_name}_map_{map_index}` entity attributes)
- **info_text (optional, default = 1)**: Can be set to 0 for rendering the map image transparent and without the top header text

> Returns `404` if requested saved map does not contain any wifi map data.

**Example:**

`http://local.homeassistant/api/camera_wifi_map_proxy/camera.vacuum_map_1?token=5df93cfcf8ecc23fa17b233ca938cc52f41e2b17a46ca291865be3f9ba64d89b`


#### WiFi Map Card

```yaml
type: custom:button-card
entity: camera. # Current or saved map camera entity
icon: mdi:wifi-marker
tap_action:
  action: none
entity_picture: >
  [[[ return function(t){const e=t._config;if(t.shadowRoot.querySelector("hui-error-card")&&!t._u)return t._u=!0,t.style.opacity=0,void setTimeout((function(){t.style.opacity=1,t.update()}),0);if(!t.__shouldUpdate){t._u=!1;const i=/v=([^&]*)/,o=/index=([^&]*)/;t.__shouldUpdate=t.shouldUpdate,t.shouldUpdate=function(t){const e=this;let o=e.__shouldUpdate(t);if(t&&t.has("_config"))return e.shouldUpdate=e.__shouldUpdate,e.__shouldUpdate=null,e._s=null,!0;const a=e._config,n=e._hass.states[a.entity],l=t.get("_hass"),s=l?l.states[a.entity]:null;if(o=l&&s!=n,!o)return!1;e._l&&(e._l.stateObj=n);let r=e.__items(e._hass);const c=e.__items(l)[0].join(",")!==r[0].join(",");if(e._i&&n&&!c){if(!c&&e._i&&n&&e._a){const t=n.attributes.access_token;if(t!=e._a&&(e._config.hold_action.url_path=e._i[1].replace(e._a,t),e._a=t,this._config.custom_fields))return!0}return e.hass=e._hass,!1}let d=0;const u=e._s;if(n){const t=n.attributes.access_token;if(!c&&t!=e._a){let i=n.attributes[a.picture_list+"_picture"];if(i)if("string"==typeof i||i instanceof String)i=i.replace(e._a,t);else for(let o=0;o<r[0].length;o++)i[r[0][o]]=i[r[0][o]].replace(e._a,t)}if(e._a=t,d=u&&""===u.value?0:parseInt(u.value),d<0||d>=r[0].length)d=0;else if(d>0&&r[0].length>0&&(d=0,e._i&&(d=r[0].indexOf(e._i[0]),-1===d))){d=0;let t=e._i[1].match(i)[1];for(let e=0;e<r[1].length;e++)if(t==r[1][e].match(i)[1]){d=e;break}}}return u.label=!(!a.label||!n)&&a.label,e.__populate(d,r[0],u),u.dispatchEvent(new Event("change")),o},t.__items=function(t){if(t){const e=t.states[this._config.entity];if(e&&e.attributes){const t=e.attributes[this._config.picture_list+"_picture"];if(t){if("string"==typeof t||t instanceof String)return[[""],[t]];{const e=Object.values(t);if(e.length)return[Object.keys(t),e]}}}}return[[],[]]},t.__populate=function(t,e,i){const o={"(Completed)":"✔️","(Interrupted)":"❌","(Manually Ignored)":"⛔","(Automatically Ignored)":"⭕","(Edited)":"📝","(Original)":"✅","(Backup)":"💾"},a=new RegExp(Object.keys(o).join("|").replaceAll(")","\\)").replaceAll("(","\\("),"g"),n=function(t){return t&&t.length?t.replace(a,(t=>o[t])):""};(t<0||t>=e.length)&&(t=0);let l="";for(let s=0;s<e.length;s++)l+='<mwc-list-item value="'+s+'"'+(t==s?" selected activated":"")+">"+n(e[s])+"</mwc-list-item>";i.innerHTML=l,i.value=t+"",i.selectedText=n(e[t])};const a="picture-selector",n=t.shadowRoot.querySelector("ha-card#"+a);n&&n.remove();const l=document.createElement("ha-card");let s;l.id=a,l.style.cssText="cursor:default;display:block;padding:12px 16px 16px;overflow:visible;border-bottom-left-radius:0;border-bottom-right-radius:0;border-bottom:none;",t.shadowRoot.children.length?t.shadowRoot.insertBefore(l,t.shadowRoot.children[0]):t.shadowRoot.appendChild(l),e.title&&e.title.length&&(" "!==e.title&&(s=document.createElement("h1"),s.className="card-header",s.style.padding="0 0 4px 0",s.innerHTML='<div class="name">'+e.title+"</div>",l.appendChild(s)),e.styles.grid||(e.styles.grid=[]),e.styles.grid=e.styles.grid.concat([{cursor:"default"},{display:"block"},{margin:"0 16px 16px"},{overflow:"hidden"},{"border-radius":"var(--ha-card-border-radius,12px)"},{"border-width":"var(--ha-card-border-width,1px)"},{"border-style":"solid"},{"border-color":"var(--ha-card-border-color,var(--divider-color,#e0e0e0))"},{background:"var(--input-disabled-fill-color);"}]));const r=t._hass.states[e.entity];t._a=r?r.attributes.access_token:"";const c=t.__items(t._hass),d=document.createElement("ha-select");if(d.style.cssText="width:auto;display:block;",e.icon&&e.icon.length){d.style.cssText+="margin:4px 0 0 40px;";const i=document.createElement("state-badge");i.stateObj=r,i.overrideIcon=e.icon,i.style.cssText="float:left;margin-top:12px;",l.appendChild(i),t._l=i}d.label=!(!e.label||!r)&&e.label,d.value="0",d.naturalMenuWidth=!0,1==c[0].length&&0==c[0][0].length&&(s?(d.style.display="none",t._l&&(t._l.style.display="none"),s.style.padding="0"):l.style.display="none"),t.__populate(0,c[0],d),l.appendChild(d),t._s=d;const u=function(e){const i=function(i){if(!i)return;const o=function(t){const e=t.target.parentElement.querySelectorAll("ha-circular-progress").forEach((t=>t.remove()));e&&e.remove(),t.target.style.cursor=""};i.onload=function(t){i.style.height="",t.target.style.opacity=1,o(t),t.target.onload=null},i.onerror=function(e){t._i=!1,o(e),t.update()},i.style.opacity=0,i.style.cursor="wait",e&&0==i.naturalHeight&&i.width&&(i.style.height=i.width+"px");const a=document.createElement("ha-circular-progress");a.active=!0,a.size="large",a.style.position="absolute",i.parentElement.appendChild(a)},o=t.shadowRoot.querySelector("#icon");o&&"IMG"==o.tagName?i(o):setTimeout((function(){const e=t.shadowRoot.querySelector("#icon");e&&0==e.naturalHeight&&e.width&&(e.style.height=e.width+"px"),i(e)}),0)};d.addEventListener('closed',function(e){e.stopPropagation()});if(d.onchange=function(e){if(""!=e.target.value){const a=t.__items(t._hass);if(0===a[1].length)return void(t._i=!1);const n=parseInt(e.target.value);if(n>=0&&n<a[1].length&&(!t._i||t._i[0]!=a[0][n]&&t._i[1]!=a[1][n])){if(t._i){if(t._i[0]=a[0][n],t._i[1].match(i)[1]===a[1][n].match(i)[1])return;t._i[1]=a[1][n]}else t._i=[a[0][n],a[1][n]];t._config.hold_action.url_path=t._i[1];const e=t._i[1].match(o);t._x=e&&e.length>1?e[1]:"",u(),t.update()}}},t._i=!1,t._config.hold_action={action:"url"},c[0].length){t._config.hold_action.url_path=c[1][0];const e=c[1][0].match(o);t._x=e&&e.length>1?e[1]:"";const i=t.shadowRoot.querySelector("#icon");i&&"IMG"==i.tagName?t._i=[c[0][0],c[1][0]]:(t.style.opacity=0,setTimeout((function(){t._i=[c[0][0],c[1][0]],u(!0),t.update(),t.style.opacity=1}),0))}}return t._i?t._i[1]+(e.extra_params&&e.extra_params.length?"&"+e.extra_params:""):void 0}(this) ]]]
picture_list: wifi_map
size: 100%
show_name: false
show_entity_picture: true
styles:
  icon:
    - transition: opacity 180ms ease-in-out 0s
  card:
    - --mdc-ripple-color: rgba(0,0,0,0)
    - padding: 0
```

### Square Map

Map will be rendered at 1:1 ratio when this option is enabled from configuration options. This is useful for matching the heights of cards when there are multiple maps on a single dashboard.

### Low Resolution Map

Low resolution configuration option must be enabled when Home Assistant instance running on a system or container with less than 3GB memory otherwise Home Assistance instance may not start since integration uses a lot of memory for rendering zoomable high resolution images like official APP.


### <a href="https://github.com/Tasshack/dreame-vacuum/blob/master/README.md#how-to-use" target="_blank">How to view the map on the dashboard</a>