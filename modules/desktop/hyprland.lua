-- nascentOS defaults. Personal overrides run last; see README.md.
hl.monitor({ output = "", mode = "preferred", position = "auto", scale = 1 })
hl.config({
  general = {
    layout = "dwindle", gaps_in = 5, gaps_out = 10, border_size = 2,
    col = { active_border = "rgb(88c0d0)", inactive_border = "rgb(4c566a)" },
  },
  decoration = { rounding = 6, blur = { enabled = false } },
  input = { kb_layout = os.getenv("XKB_DEFAULT_LAYOUT") or "us", kb_variant = os.getenv("XKB_DEFAULT_VARIANT") or "", touchpad = { natural_scroll = true } },
  misc = { disable_hyprland_logo = true, background_color = "rgb(2e3440)" },
})
hl.window_rule({ match = { class = "[Cc]alamares", modal = false }, maximize = true })

hl.on("hyprland.start", function()
  hl.exec_cmd("dbus-update-activation-environment --systemd DBUS_SESSION_BUS_ADDRESS WAYLAND_DISPLAY DISPLAY HYPRLAND_INSTANCE_SIGNATURE XDG_CURRENT_DESKTOP XDG_SESSION_TYPE && systemctl --user start nascent-session.target && systemctl --user start nascent-wallpaper.service")
  hl.exec_cmd("nascent-launch bar")
  hl.exec_cmd("nascent-launch notifications")
  hl.exec_cmd("nm-applet --indicator")
  hl.exec_cmd("/run/current-system/sw/libexec/polkit-gnome-authentication-agent-1")
  local live = io.open("/etc/nascentos/live-installer", "r")
  if live then
    live:close()
    hl.exec_cmd("nascent-install")
  end
end)

hl.bind("SUPER + Return", hl.dsp.exec_cmd("nascent launch terminal"))
hl.bind("SUPER + Space", hl.dsp.exec_cmd("nascent menu"))
hl.bind("SUPER + D", hl.dsp.exec_cmd("nascent launch apps"))
hl.bind("SUPER + A", hl.dsp.exec_cmd("nascent-agent-ui"))
hl.bind("SUPER + I", hl.dsp.exec_cmd("command -v nascent-install >/dev/null && nascent-install"))
hl.bind("SUPER + B", hl.dsp.exec_cmd("nascent-browser"))
hl.bind("SUPER + Q", hl.dsp.window.close())
hl.bind("SUPER + F", hl.dsp.window.fullscreen({ mode = "fullscreen" }))
hl.bind("SUPER + V", hl.dsp.window.float({ action = "toggle" }))
hl.bind("SUPER + SHIFT + L", hl.dsp.exec_cmd("nascent launch lock"))
hl.bind("SUPER + SHIFT + E", hl.dsp.exit())
for _, direction in ipairs({ "left", "right", "up", "down" }) do
  hl.bind("SUPER + " .. direction, hl.dsp.focus({ direction = direction }))
end
for workspace = 1, 10 do
  local key = workspace % 10
  hl.bind("SUPER + " .. key, hl.dsp.focus({ workspace = workspace }))
  hl.bind("SUPER + SHIFT + " .. key, hl.dsp.window.move({ workspace = workspace }))
end
hl.bind("SUPER + mouse:272", hl.dsp.window.drag(), { mouse = true })
hl.bind("SUPER + mouse:273", hl.dsp.window.resize(), { mouse = true })

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
