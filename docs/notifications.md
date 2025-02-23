# Notifications with error reporting
Integration tracks certain device properties and adds persistent notifications on specific events as implemented on official App. Notification feature can be disabled from integration settings.
> All resources and strings are extracted from the official App with Z10 Pro, some of them will may fit to your device. Resources for other devices may be added on future release.

### Cleanup completed
Added when cleanup job is completed or canceled.

<img src="https://raw.githubusercontent.com/Tasshack/dreame-vacuum/main/docs/media/notification_cleanup_completed.jpg" width="400px">


### Consumable is depleted
Added when consumable life is ended.

<img src="https://raw.githubusercontent.com/Tasshack/dreame-vacuum/master/docs/media/notification_consumable_brush.jpg" width="400px">

<img src="https://raw.githubusercontent.com/Tasshack/dreame-vacuum/master/docs/media/notification_sensor.jpg" width="400px">

### Error reporting
Added when there is a fault or warning with the device.

<img src="https://raw.githubusercontent.com/Tasshack/dreame-vacuum/master/docs/media/notification_error_drop.jpg" width="400px">

<img src="https://raw.githubusercontent.com/Tasshack/dreame-vacuum/master/docs/media/notification_error_blocked.jpg" width="400px">

> Warnings are actually can be cleared from the device when notification is dismissed from Home assistant.

<img src="https://raw.githubusercontent.com/Tasshack/dreame-vacuum/master/docs/media/notification_warning_mop.jpg" width="400px">

### Cleaning paused due to low battery
Added when resume cleaning feature is enabled and vacuum cannot continue cleaning job due to low battery.

<img src="https://raw.githubusercontent.com/Tasshack/dreame-vacuum/master/docs/media/notification_low_battery.jpg" width="400px">

<img src="https://raw.githubusercontent.com/Tasshack/dreame-vacuum/master/docs/media/notification_resume_cleaning.jpg" width="400px">

### New map must be replaced
Added after mapping completed when device cannot store the new map. Official app does not allow you to make any changes when device on this state.

<img src="https://raw.githubusercontent.com/Tasshack/dreame-vacuum/master/docs/media/notification_temporary_map.jpg" width="400px">

<img src="https://raw.githubusercontent.com/Tasshack/dreame-vacuum/master/docs/media/notification_temporary_multi_map.jpg" width="400px">

### Dust collection not performed
Added when auto-emptying not performed due to the do not disturb settings.

<img src="https://raw.githubusercontent.com/Tasshack/dreame-vacuum/master/docs/media/notification_dust_collection.jpg" width="400px">

### Low Water

TODO

### Drainage Status

TODO
