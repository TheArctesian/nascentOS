# Optional local inference and speech

Enable on a host, independently of your desktop/provider adapters:

```nix
nascent.localAI.enable = true;
# After confirming an NVIDIA GPU and selecting the NVIDIA hardware module:
# nascent.localAI.backend = "cuda";
```

This enables an Ollama-compatible runtime at **127.0.0.1:11434**, installs
`whisper-cli` from whisper.cpp and ffmpeg, opens no firewall port and declares no
models to download. CPU is the portable default. The runtime package can be
replaced through `nascent.localAI.runtimePackage`, or this optional module can be
disabled entirely in favor of another runtime. Agent adapters need not use Ollama.

```sh
nascent ai models
# Explicit model acquisition, after choosing a model/license/size:
ollama pull MODEL
nascent ai run MODEL 'your prompt'
# Supply an existing Whisper GGML model and a compatible WAV file:
nascent ai transcribe /path/to/ggml-model.bin /path/to/audio.wav
```

For explicit Whisper model acquisition, use the installed
`whisper-cpp-download-ggml-model` from a writable model directory after choosing a
model. `ffmpeg -i input.m4a -ar 16000 -ac 1 output.wav` prepares a common input
format. Speech is initially local file transcription, not a microphone hotkey,
push-to-talk GUI or automatic dictation. Whisper uses the CPU even on the CUDA
LLM profile in this first slice. No models/audio were downloaded or transcribed
as part of validation.

The tentative RTX 3080 may have 10 or 12 GB VRAM. Confirm the card/memory and choose
model quantization, context length and concurrency accordingly; this prototype
does not promise a model fits or benchmark performance. GPU drivers/CUDA need a
physical-machine gate. The service is local to the machine, not authenticated
multi-user isolation. No orchestration daemon or automatic agent privileges are
introduced.

## Agent structure

Inspired by Omarchy's small `bin/omarchy-*` commands, selected-default files and
focused `agents/skills/` references, `nascent` dispatches to small `nascent-*`
commands. This implementation is independently authored; Omarchy's MIT notice is
retained under `third-party/`. Its installer/account copying/provider permission
bypass logic is not imported.

Add your own executable wrapper to `~/.config/nascentos/agents/NAME`, then:

```sh
nascent agent list
nascent agent set NAME
nascent agent run [provider-specific arguments]
```

Adapters run directly with argument boundaries preserved. They choose a local
model client or any installed provider CLI, and keep its normal authentication
and permission behavior. No provider or default adapter is selected for you.
`agents/skills/desktop.md` is an optional reference installed under
`/etc/nascentos/agents/skills`; no provider-specific instruction loader is imposed.
