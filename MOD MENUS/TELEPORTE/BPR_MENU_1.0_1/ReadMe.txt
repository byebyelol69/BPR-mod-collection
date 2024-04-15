BPR MENU BETA 1.0 (07/04/2019)
------------------------------

===========
Description
===========
BPR Menu is an in-game menu with functions to enhance the gaming experience on Burnout Paradise Remastered (PC). Amoung its functions, there are vehicle spawn, wheel, color and boost changers, teleport to saved locations and spawn saved vehicles.

============
Installation
============
Extract the files in the game folder, usually located at:
"C:\Program Files (x86)\Origin Games\BurnoutPR"

=====
Usage
=====
-Start BurnoutPRLauncher.exe. A loading screen will show up;
-Burnout Paradadise Remastered will be launched automatically a few seconds later (after opening Origin);
-The in-game menu will be displayed in about 15 seconds after the game window appears;
-BurnoutPRLauncher.exe will be closed automatically after the in-game menu shows up;
-Use the menu navigation keys to move around in the menu and the Enter key to activate selected items.

-For adding a vehicle to the "Saved Vehicles", press the hotkey Save_Vehicle (the default one is CTRL+S+V). It will save your current vehicle informations, such as display name and vehicle name, wheel, color and its type, and also boost type. After saving, you can edit the display name if you intend to;
-For adding a wheel to the "Saved Wheels", press the hotkey Save_Wheel (the default one is CTRL+S+W);
-For adding a location to the "Go to" option, press the hotkey Save_Local (the default one is CTRL+S+L). After saving, you can edit the local name if you intend to;
-For adding a color to the "Saved Colors", press the hotkey Save_Color (the default one is CTRL+S+C). It will save the current applied color and its color type. After saving, you can edit the color name if you intend to;
-For hiding the menu press the hotkey Show_Hide_Menu (the default one is Insert);
-For increasing the step press the hotkey Increase_Step (the default one is Shift); 

=======
Hotkeys
=======
-You can see and edit the menu navigation hotkeys in the file config.xml.
-Under the XML Element <Keys> you can read the keys, that uses the following structure:
<key name="KeyName">Key</key>
The attribute KeyName can't be changed.
Its text content "Key" can be edited to one key or a combination of keys.
Example:
<key name="Left">VK_LEFT</key> can be changed to:
<key name="Left">VK_CONTROL + VK_NUMPAD0</key> or <key name="Left">L</key>
-You can check this website to get other virtual key codes (VK Keys):
https://docs.microsoft.com/en-us/windows/desktop/inputdev/virtual-key-codes
-You can reload the whole config.xml file while in-game using the hotkeys under "Reload_Config".

====================
Settings Description
====================
Keys:
-Up: moves up the menu selection;
-Down: moves down the menu selection;
-Left: increases an item in the current menu item (if changeable);
-Right: decreases an item in the current menu item (if changeable);
-Enter: actives the current selection of the menu item (if activeable);
-Show_Hide_Menu: shows or hides the menu;
-Increase_Step: changes the item increment to 100 (if changeable);
-Save: generic save key, it saves the current menu item value, available for Local, Color, Vehicle and Wheel;
-Save_Local: saves your current location;
-Save_Color: saves the current vehicle color;
-Save_Vehicle: saves the current vehicle information (together with its current wheel, current color type and color, and current boost type)
-Save_Wheel: saves the current wheel;
-Reload_Config: reloads the whole config.xml file while in-game.

Options:
-Color: color display format (decimal or hexadecimal);
-Speed: speed display unit (mph, km/h or m/s).

==========
What's New
==========
Version 1.0 (07/04/2019):
-Initial public release.

===============
Uninstallation
===============
-Delete these files from your game folder: d3dMenu.dll, BurnoutPRLauncher.exe and config.xml.

==============
Special Thanks
==============
PISros for doing the initial cheat engine table, providing pointers, testing and giving ideas;
burninrubber0 for testing and giving suggestions;
Cade-H for testing and giving suggestions; 
ctrl for testing and giving suggestions;
Mingo for testing and giving suggestions;
P3RF_D4RK for testing and giving suggestions.