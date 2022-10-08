# Notifications
Integration tracks certain device properties and adds persistent notifications on specific events as implemented on official App. Notification feature can be disabled from integration settings.

### Cleanup completed
Added when cleanup job is completed or canceled.

<img src="https://raw.githubusercontent.com/Tasshack/dreame-vacuum/master/docs/media/notification_cleanup_completed.png" width="20%">


### Consumable is depleted
Added when consumable life is ended.
> All resources and strings are extracted from the official App for Z10 Pro, some of them will may fit to your device. 

<img src="https://raw.githubusercontent.com/Tasshack/dreame-vacuum/master/docs/media/notification_consumable_brush.png" width="20%">

<img src="https://raw.githubusercontent.com/Tasshack/dreame-vacuum/master/docs/media/notification_consumable_filter.png" width="20%">

### Error reporting
Added when there is a fault or warning with the device.
> Warnings are actually can be cleared from the device when notification is dismissed from Home assistant.

> All resources and strings are extracted from the official App for Z10 Pro, some of them will may fit to your device. 

### Cleaning paused due to low battery
Added when resume cleaning feature is enabled and vacuum cannot continue cleaning job due to low battery.

<img src="https://raw.githubusercontent.com/Tasshack/dreame-vacuum/master/docs/media/notification_low_battery.png" width="20%">

<img src="https://raw.githubusercontent.com/Tasshack/dreame-vacuum/master/docs/media/notification_resume_cleaning.png" width="20%">

### New map must be replaced
Added after mapping completed when device cannot store the new map. Official app does not allow you to make any changes when device on this state.

<img src="https://raw.githubusercontent.com/Tasshack/dreame-vacuum/master/docs/media/temporary_map.png" width="20%">

<img src="https://raw.githubusercontent.com/Tasshack/dreame-vacuum/master/docs/media/temporary_multi_map.png" width="20%">

### Dust collection not performed
Added when auto-emptying not performed due to the do not disturb settings.

<img src="https://raw.githubusercontent.com/Tasshack/dreame-vacuum/master/docs/media/dust_collection.png" width="20%">