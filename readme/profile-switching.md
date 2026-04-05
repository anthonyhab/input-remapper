# Per-Application Profile Switching

## Overview

Automatically switch input-remapper presets based on the currently focused application. Perfect for gamers who need different mouse/keyboard mappings for different games, or power users who want context-sensitive input configurations.

## How It Works

Profile switching uses a simple rule-based system:

1. **Profile** - A collection of default presets and application-specific rules
2. **Defaults** - Base presets applied when no specific rule matches (format: `{"Device Name": "preset_name"}`)
3. **Rules** - Override defaults when specific applications are focused
4. **Matching** - First matching rule wins; rules are evaluated in order

The profile service runs in your user session (not as root) and monitors window focus changes via your compositor's IPC.

## Quick Start

1. **Enable Profile Switching**
   - Open input-remapper GUI
   - Go to the Profiles page
   - Toggle "Enable Profile Switching"

2. **Create a New Profile**
   - Click "Create Profile"
   - Enter a name (e.g., "gaming", "work")

3. **Set Default Presets**
   - For each device, select the default preset to use when no app-specific rule matches

4. **Add Application Rules**
   - Click "Add Rule"
   - Enter the application class (see [Finding App Classes](#finding-app-classes) below)
   - Select which device and preset to use for that application

5. **Activate the Profile**
   - Select your profile from the dropdown
   - The profile is now active and will automatically switch presets based on window focus

## Finding App Classes

To create rules, you need the exact application class (window class) of the target application.

### Hyprland

Run this command in a terminal:

```bash
hyprctl activewindow | grep class
```

Then switch to the target application window and note the class value.

Alternatively, use this to get just the class:

```bash
hyprctl activewindow -j | jq -r .class
```

**Common application classes:**
- Firefox: `firefox`
- VS Code: `code`
- Terminal (alacritty): `Alacritty`
- Discord: `discord`
- Steam: `Steam`

The class name is **case-sensitive** and must match exactly.

## Example: RuneLite Gaming Setup

Here's a complete example configuration for automatically switching to an "esc" preset when playing RuneLite:

```json
{
    "version": "2.2.0",
    "enabled": true,
    "active_profile": "gaming",
    "profiles": {
        "gaming": {
            "defaults": {
                "Razer DeathAdder": "default",
                "Logitech G Pro": "default"
            },
            "rules": [
                {
                    "app_class": "net-runelite-client-RuneLite",
                    "overrides": {
                        "Razer DeathAdder": "esc"
                    }
                },
                {
                    "app_class": "steam",
                    "overrides": {
                        "Razer DeathAdder": "gaming-mouse",
                        "Logitech G Pro": "gaming-keyboard"
                    }
                }
            ]
        }
    }
}
```

Save this to `~/.config/input-remapper-2/profiles.json` (the GUI will do this for you).

## Configuration File Format

The profile configuration is stored at `~/.config/input-remapper-2/profiles.json`:

```json
{
    "version": "2.2.0",
    "enabled": true,
    "active_profile": "profile_name",
    "profiles": {
        "profile_name": {
            "defaults": {
                "Device Name 1": "default_preset",
                "Device Name 2": "another_preset"
            },
            "rules": [
                {
                    "app_class": "application-class-name",
                    "overrides": {
                        "Device Name 1": "app_specific_preset"
                    }
                }
            ]
        }
    }
}
```

### Field Descriptions

| Field | Type | Description |
|-------|------|-------------|
| `enabled` | boolean | Whether profile switching is active |
| `active_profile` | string | Name of the currently active profile |
| `profiles` | object | Map of profile names to profile definitions |
| `defaults` | object | Default presets per device (group_key → preset) |
| `rules` | array | Ordered list of application-specific rules |
| `app_class` | string | Window class to match (case-sensitive) |
| `overrides` | object | Device presets to apply when this rule matches |

## Rule Matching Behavior

Rules are evaluated in array order, and the **first matching rule wins**:

```json
"rules": [
    {"app_class": "firefox", "overrides": {"Mouse": "browser"}},
    {"app_class": "firefox", "overrides": {"Mouse": "unused"}}  // Never reached
]
```

Only the first Firefox rule would apply. If no rules match, the `defaults` are used.

## Backend Support

### Current Support

- **Hyprland** - Fully supported via Hyprland's IPC socket (`socket2.sock`)

### Planned/Extensible

The backend system is designed to support additional Wayland compositors and X11:

- Sway (i3-compatible Wayland compositor)
- KWin (KDE Plasma)
- Mutter (GNOME)
- X11 via EWMH/ICCCM

To add support for a new compositor, implement the `AppMonitorBackend` interface in `inputremapper/profile_switching/backends/`.

## Troubleshooting

### Profile switching not working

1. **Check if enabled**: Verify "Enable Profile Switching" is toggled on in the GUI
2. **Active profile**: Ensure a profile is selected as active
3. **Service running**: Check that the profile service is running (integrated with main service)

### Rules not matching

1. **Verify app class**: Use `hyprctl activewindow` to confirm the exact class name
2. **Case sensitivity**: Application classes are case-sensitive (`firefox` ≠ `Firefox`)
3. **Rule order**: Remember that only the first matching rule applies

### Finding backend issues

For Hyprland, check that the socket exists:

```bash
ls -la $XDG_RUNTIME_DIR/hypr/$HYPRLAND_INSTANCE_SIGNATURE/.socket2.sock
```

### Debug logging

Run input-remapper with debug logging to see profile switching activity:

```bash
input-remapper-gtk -d
```

Look for log messages containing "ProfileService" or "profile switching".

## Limitations

- **Hyprland only** - Currently only Hyprland is supported. Other compositors need backend implementations.
- **User session** - The profile service runs as your user (not root), so it can only switch presets, not start/stop the main daemon.
- **No X11 support** - X11 window managers are not yet supported.
- **Single compositor** - Cannot monitor windows across multiple compositors simultaneously.

## CLI Usage

While profile switching is primarily GUI-driven, you can also manipulate the configuration via Python:

```python
from inputremapper.configs.profile_switching_config import ProfileSwitchingConfig

config = ProfileSwitchingConfig()
config.load()

# Create a profile
config.create_profile(
    "gaming",
    defaults={"Mouse": "default"},
    rules=[{"app_class": "game", "overrides": {"Mouse": "game_profile"}}]
)

# Activate it
config.set_active_profile("gaming")
config.set_enabled(True)
config.save()
```

## See Also

- [Usage Guide](./usage.md) - General input-remapper usage
- [Examples](./examples.md) - Preset examples and macros
