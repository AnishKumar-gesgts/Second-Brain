# Xbox Controller Control

This Windows tray utility converts an Xbox controller into mouse input.

- Desktop mode: left stick moves the mouse; right stick moves it at higher sensitivity; LT is right click and RT is left click; right-stick-click is middle click.
- D-pad up/down scrolls vertically; D-pad left/right scrolls horizontally.
- Game mode: mouse emulation is disabled, so controller games receive their normal input.
- Press the Back/View button to switch modes. This is the mode-switch button. A newly connected controller starts in Desktop mode.
- The app polls XInput without recording controller input, mouse input, audio, or transcripts.

The mappings are intentionally centralized in `ControllerMouseController` so they can be changed when the desired controls are finalized.

## Build and run

Install the .NET 10 SDK, then run:

```powershell
dotnet run
```

The app runs in the notification area and registers itself for the current user's Windows startup on first launch. Exit it from the tray menu. Once running, it automatically enters Desktop mode whenever an XInput controller is plugged in.

The current implementation checks controller 1. Supporting multiple controllers is straightforward if needed.
