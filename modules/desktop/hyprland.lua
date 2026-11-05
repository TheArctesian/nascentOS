-- nascentOS defaults. Personal overrides run last; see README.md.
-- "auto" picks the scale from the panel's PPI (2x on a Framework 13, 1.5x on a Framework 16).
hl.monitor({ output = "", mode = "preferred", position = "auto", scale = "auto" })
hl.config({
  general = {
    layout = "dwindle", gaps_in = 5, gaps_out = 10, border_size = 2, resize_on_border = true,
    col = { active_border = "rgb(88c0d0)", inactive_border = "rgb(4c566a)" },
  },
  decoration = {
    -- Blur only applies to translucent surfaces: the launcher, notifications and bar, not opaque windows.
    rounding = 8, blur = { enabled = true, size = 6, passes = 3, noise = 0.02, vibrancy = 0.2 },
    shadow = { enabled = true, range = 18, render_power = 3, offset = "0 4", color = "rgba(0000004d)", color_inactive = "rgba(00000026)" },
  },
  dwindle = { preserve_split = true },
  input = {
    kb_layout = os.getenv("XKB_DEFAULT_LAYOUT") or "us", kb_variant = os.getenv("XKB_DEFAULT_VARIANT") or "",
    follow_mouse = 1, touchpad = { natural_scroll = true },
  },
  -- Render X11 apps at their native size instead of upscaling them blurrily on HiDPI panels.
  xwayland = { force_zero_scaling = true },
  misc = { disable_hyprland_logo = true, disable_splash_rendering = true, background_color = "rgb(2e3440)" },
  animations = { enabled = true },
})

-- One motion language everywhere: windows move on a critically damped spring (fluid, no bounce),
-- everything else fades with a short ease-out. Nothing slides across the screen.
hl.curve("nascentOut", { type = "bezier", points = { { 0.22, 1 }, { 0.36, 1 } } })
hl.curve("nascentIn", { type = "bezier", points = { { 0.55, 0 }, { 1, 0.45 } } })
hl.curve("nascentSpring", { type = "spring", mass = 1, stiffness = 120, dampening = 21 })
hl.animation({ leaf = "global", enabled = true, speed = 2.5, bezier = "nascentOut" })
hl.animation({ leaf = "windows", enabled = true, speed = 4, spring = "nascentSpring" })
hl.animation({ leaf = "windowsIn", enabled = true, speed = 4, spring = "nascentSpring", style = "popin 92%" })
hl.animation({ leaf = "windowsOut", enabled = true, speed = 1.6, bezier = "nascentIn", style = "popin 94%" })
hl.animation({ leaf = "windowsMove", enabled = true, speed = 4, spring = "nascentSpring" })
hl.animation({ leaf = "fadeIn", enabled = true, speed = 2.5, bezier = "nascentOut" })
hl.animation({ leaf = "fadeOut", enabled = true, speed = 1.6, bezier = "nascentIn" })
hl.animation({ leaf = "fadeSwitch", enabled = true, speed = 2.5, bezier = "nascentOut" })
hl.animation({ leaf = "border", enabled = true, speed = 2.5, bezier = "nascentOut" })
hl.animation({ leaf = "layersIn", enabled = true, speed = 2.5, bezier = "nascentOut", style = "fade" })
hl.animation({ leaf = "layersOut", enabled = true, speed = 1.6, bezier = "nascentIn", style = "fade" })
hl.animation({ leaf = "fadeLayersIn", enabled = true, speed = 2.5, bezier = "nascentOut" })
hl.animation({ leaf = "fadeLayersOut", enabled = true, speed = 1.6, bezier = "nascentIn" })
hl.animation({ leaf = "workspaces", enabled = true, speed = 2.5, bezier = "nascentOut", style = "fade" })
hl.animation({ leaf = "specialWorkspace", enabled = true, speed = 2.5, bezier = "nascentOut", style = "fade" })

-- Installer windows are dialogs, not workspaces: float them centred at a comfortable size.
hl.window_rule({ match = { class = "[Cc]alamares", modal = false },
  float = true, size = "max(1080, monitor_w*0.78) max(640, monitor_h*0.86)", center = true })
-- Rule regexes must match the whole title.
hl.window_rule({ match = { title = "^Install nascentOS.*" }, float = true, center = true })
-- Home workspaces for regular apps, as in the owner's bspwm setup.
for class, workspace in pairs({ ["^(firefox|Firefox)$"] = 2, ["^obsidian$"] = 3, ["^Zotero$"] = 4,
  ["^(signal|Signal)$"] = 5, ["^(Slack|slack)$"] = 6, ["^com.obsproject.Studio$"] = 8 }) do
  hl.window_rule({ match = { class = class }, workspace = tostring(workspace) .. " silent" })
end
hl.window_rule({ match = { class = "^(zenity|pavucontrol|org.pulseaudio.pavucontrol|nm-connection-editor|mpv)$" },
  float = true, center = true })

hl.layer_rule({ match = { namespace = "^(launcher|notifications|waybar)$" }, blur = true, ignore_alpha = 0.3 })

hl.on("hyprland.start", function()
  hl.exec_cmd("dbus-update-activation-environment --systemd DBUS_SESSION_BUS_ADDRESS WAYLAND_DISPLAY DISPLAY HYPRLAND_INSTANCE_SIGNATURE XDG_CURRENT_DESKTOP XDG_SESSION_TYPE && systemctl --user start nascent-session.target && systemctl --user start nascent-wallpaper.service")
  hl.exec_cmd("nascent-xdpi")
  hl.exec_cmd("nascent-launch bar")
  hl.exec_cmd("nascent-launch notifications")
  hl.exec_cmd("nascent-clipboard watch")
  hl.exec_cmd("nm-applet --indicator")
  hl.exec_cmd("/run/current-system/sw/libexec/polkit-gnome-authentication-agent-1")
  local live = io.open("/etc/nascentos/live-installer", "r")
  if live then
    live:close()
    hl.exec_cmd("nascent-install")
  end
end)

-- Keybindings follow the owner's bspwm/sxhkd layout (Super+Shift+Return terminal, hjkl, Super+C close).
local function bind(keys, action, options)
  hl.bind(keys, action, options)
end
local function run(command)
  return hl.dsp.exec_cmd(command)
end

-- Launchers and session
bind("SUPER + SHIFT + Return", run("nascent launch terminal"))
bind("SUPER + Return", run("nascent launch terminal"))
bind("SUPER + P", run("nascent launch apps"))
bind("SUPER + D", run("nascent launch apps"))
bind("SUPER + SHIFT + Space", run("nascent menu"))
bind("SUPER + A", run("nascent-agent-ui"))
bind("SUPER + I", run("command -v nascent-install >/dev/null && nascent-install"))
bind("SUPER + V", run("nascent-clipboard pick"))
bind("SUPER + SHIFT + E", run("nascent-power"))
bind("SUPER + Pause", run("nascent-power"))
bind("SUPER + Escape", run("hyprctl reload"))
bind("SUPER + SHIFT + R", run("hyprctl reload"))
bind("SUPER + SHIFT + Q", hl.dsp.exit())

-- Window state
bind("SUPER + C", hl.dsp.window.close())
bind("SUPER + Q", hl.dsp.window.close())
bind("SUPER + SHIFT + C", hl.dsp.window.kill())
bind("SUPER + T", hl.dsp.window.float({ action = "unset" }))
bind("SUPER + SHIFT + T", hl.dsp.window.pseudo())
bind("SUPER + S", hl.dsp.window.float({ action = "toggle" }))
bind("SUPER + F", hl.dsp.window.fullscreen({ mode = "fullscreen" }))
bind("SUPER + Space", hl.dsp.window.fullscreen({ mode = "maximized" })) -- monocle

-- Focus, swap, resize and preselect with hjkl
local directions = { h = "left", j = "down", k = "up", l = "right" }
local preselect = { h = "l", j = "d", k = "u", l = "r" }
local resize = { h = { x = -20, y = 0 }, j = { x = 0, y = 20 }, k = { x = 0, y = -20 }, l = { x = 20, y = 0 } }
for key, direction in pairs(directions) do
  bind("SUPER + " .. key, hl.dsp.focus({ direction = direction }))
  bind("SUPER + SHIFT + " .. key, hl.dsp.window.swap({ direction = direction }))
  bind("SUPER + ALT + " .. key, hl.dsp.window.resize({ x = resize[key].x, y = resize[key].y, relative = true }),
    { repeating = true })
  bind("SUPER + CTRL + " .. key, hl.dsp.layout("preselect " .. preselect[key]))
end

-- Workspaces
for workspace = 1, 10 do
  local key = workspace % 10
  bind("SUPER + " .. key, hl.dsp.focus({ workspace = workspace }))
  bind("SUPER + SHIFT + " .. key, hl.dsp.window.move({ workspace = workspace }))
end
bind("SUPER + Left", hl.dsp.focus({ workspace = "m-1" }))
bind("SUPER + Right", hl.dsp.focus({ workspace = "m+1" }))
bind("SUPER + less", hl.dsp.focus({ workspace = "m-1" }))
bind("SUPER + greater", hl.dsp.focus({ workspace = "m+1" }))
bind("SUPER + mouse:272", hl.dsp.window.drag(), { mouse = true })
bind("SUPER + mouse:273", hl.dsp.window.resize(), { mouse = true })

-- Applications: focus the running window, otherwise launch it
bind("SUPER + B", run("nascent-browser"))
bind("SUPER + O", run("nascent-focus obsidian obsidian"))
bind("SUPER + Z", run("nascent-focus zotero zotero"))
bind("SUPER + G", run("nascent-focus signal signal-desktop"))
bind("SUPER + M", run("nascent-focus slack slack"))
bind("SUPER + Y", run("nascent-focus --requires yazi yazi nascent-launch terminal --class yazi yazi"))

-- Screenshots (copied to the clipboard)
bind("Print", run("nascent-shot full"))
bind("SUPER + SHIFT + S", run("nascent-shot area"))
bind("CTRL + Print", run("nascent-shot delayed"))

-- Hardware keys work on the lock screen too
bind("XF86AudioRaiseVolume", run("nascent-media volume up"), { locked = true, repeating = true })
bind("XF86AudioLowerVolume", run("nascent-media volume down"), { locked = true, repeating = true })
bind("XF86AudioMute", run("nascent-media volume mute"), { locked = true })
bind("XF86AudioMicMute", run("nascent-media mic mute"), { locked = true })
bind("XF86MonBrightnessUp", run("nascent-media brightness up"), { locked = true, repeating = true })
bind("XF86MonBrightnessDown", run("nascent-media brightness down"), { locked = true, repeating = true })
bind("XF86AudioPlay", run("nascent-media play"), { locked = true })
bind("XF86AudioPause", run("nascent-media play"), { locked = true })
bind("XF86AudioNext", run("nascent-media next"), { locked = true })
bind("XF86AudioPrev", run("nascent-media previous"), { locked = true })

local configHome = os.getenv("XDG_CONFIG_HOME") or (os.getenv("HOME") .. "/.config")
local themeFile = configHome .. "/nascentos/current-theme/hyprland.lua"
local theme = io.open(themeFile, "r")
if theme then
  theme:close()
  dofile(themeFile)
end

local personal = configHome .. "/nascentos/hyprland.lua"
local file = io.open(personal, "r")
if file then
  file:close()
  dofile(personal)
end
