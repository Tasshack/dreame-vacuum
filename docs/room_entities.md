# Room entities for customized cleaning

Integration exposes and manages room entities for customized cleaning settings that are introduced on firmware version 1156. If *customized cleaning* feature is enabled, robot uses these settings on *cleaning* and *custom segment cleaning* jobs and cannot be overridden by start action parameters.

<img src="https://raw.githubusercontent.com/Tasshack/dreame-vacuum/master/docs/media/room_1_entities.png" width="500px">

Custom room cleaning settings stored on current map data and only selected map settings can be accessed via the cloud api. Therefore integration shares same room entities with other saved maps and dynamically updates their entity names and icons respectively when selected map is changed. Integration exposes rooms from all saved maps and updates their availability state according to the currently selected map.

IMAGE

With the help of this template and XXXXX card you can create a card to manage all room settings.

GIF

TEMPLATE