# First voice-to-desktop slice

This is speech-to-text -> intent -> desktop tool execution. Speech output/TTS
is separate and no TTS engine is selected. There is no always-listening process.
The provisional activation method is a callable command with text or a recorded
WAV file; a microphone push-to-talk binding is still to be implemented/tested.

```sh
nascent voice --dry-run text 'pull up my browser'
nascent voice text 'pull up my browser'
nascent voice text 'close my browser'
nascent voice windows
nascent voice --window 0xADDRESS text 'close my browser'
# Requires the optional Whisper tools and a model you acquired explicitly:
nascent voice audio /path/to/ggml-model.bin /path/to/command.wav
# Opt into an already installed small Ollama intent model:
nascent voice --model YOUR_MODEL --dry-run text 'please launch the browser'
```

Without `--model`, exact normalized phrases (`pull up my browser`, `open my browser`,
`open browser`, `close my browser`, `close browser`) route deterministically.
Other phrases produce `none` and execute nothing. With `--model`, the adapter
requests constrained JSON from the loopback Ollama-compatible chat endpoint;
no model is downloaded. The schema permits only `browser.open`, `browser.close`
and `none`, with no extra fields. Model output never becomes shell or Lua code.
The model adapter can be replaced without changing the dispatcher/schema.

The initial browser tool is Firefox. Open invokes a fixed executable/argument
list. Close queries current Hyprland clients, filters Firefox by application
class and validates its hex window address before dispatching a targeted normal
close. Zero/multiple windows cause a clear error and require explicit selection;
non-browser selections are refused. It never changes focus or force-kills a
process. Unsaved-work dialogs remain the browser's responsibility. A stale target
can fail; actual compositor/window lifecycle behavior still needs the VM gate.

The selector API was checked against Hyprland v0.55.4's
[window dispatcher bindings](https://github.com/hyprwm/Hyprland/blob/v0.55.4/src/config/lua/bindings/LuaBindingsDispatchers.cpp)
and [selector helper](https://github.com/hyprwm/Hyprland/blob/v0.55.4/src/config/lua/bindings/LuaBindingsInternal.cpp).
`tests/test_desktop_intent.py` covers phrase routing, schema rejection, fixed launch
arguments, targeted close, ambiguity, foreign/injected addresses, explicit selection
and invalid local-model output using mocked compositor/runtime responses. These
logic tests do not demonstrate a microphone, actual Whisper/model inference or a
real Hyprland session working.
