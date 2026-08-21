# VoiceBot

VoiceBot is a small Windows wake-word and voice-command listener. Wake-word detection and transcription use the local Windows speech recognizer. After transcription, the command is piped to the authenticated Codex CLI in the background.

It does **not** save microphone audio, a transcript history, or an activation history. Like every speech recognizer it must keep a very short live audio buffer while listening, but that buffer is transient and is never written by this app. Only the latest Codex response is retained, overwriting `build\voicebot-last-response.txt` each time.

## Use a voice command

1. Say **"voice bot"** fluidly.
2. Wait for the acknowledgement ping.
3. Say one command, such as **"inspect this project and explain what it does."**
4. Stop talking. After 1.2 seconds of silence, the transcript is piped directly to `codex exec`.

An exclamation sound means the Codex task finished successfully. A question sound means no speech was recognized or another Codex task is still running. The error sound means Codex failed; the latest bounded error is in `build\voicebot-codex-error.txt`.

A short beep confirms that Codex accepted the command. If Codex asks a clarification question, the overlay is labeled **CLARIFICATION NEEDED** and a question-tone plays. Say **"voice bot"** again before answering; each command is currently an independent ephemeral Codex task, so include enough context in your follow-up.

Each command is an ephemeral Codex task with write access limited to the configured workspace. There is no API key in this project; Codex uses the existing CLI sign-in. VoiceBot intentionally does not use `danger-full-access`.

## Build and run

Open PowerShell in this folder and run:

```powershell
.\build.ps1
.\build\VoiceBot.exe
```

The program deliberately has no window or tray UI. Check Task Manager for `VoiceBot.exe`. Only one copy can run at a time. To stop it:

```powershell
Stop-Process -Name VoiceBot
```

Test the configured notification sound without opening the microphone:

```powershell
.\build\VoiceBot.exe --test-sound
```

Test the top-right overlay and Windows text-to-speech:

```powershell
.\build\VoiceBot.exe --test-overlay
```

If startup fails, `build\voicebot-error.txt` contains the latest error only. A common cause is microphone access being disabled under **Settings > Privacy & security > Microphone > Let desktop apps access your microphone**.

## Configure VoiceBot

Edit `build\voicebot.ini`, then restart the process. The default begins with:

```ini
Trigger=voice bot
Confidence=0.80
Sound=Asterisk
TtsVoice=Guy
```

Say `voice bot` fluidly; the recognizer does not require a pause at the written space. Higher confidence reduces false triggers but may miss quiet speech.

The remaining settings control how long VoiceBot waits for you to begin, how much silence ends the sentence, the maximum command duration, the Codex workspace, and an optional explicit `codex.exe` location.

`TtsVoice` is matched against installed Windows voice names. If `Guy` is not installed or not exposed to desktop speech apps, VoiceBot safely uses the Windows default voice until it becomes available.

Voice commands are pinned to `gpt-5.6-luna` with `CodexReasoningEffort=low`, so they do not inherit later global model changes. This is intended to minimize latency and usage for short commands; increase the effort only if a task needs deeper reasoning.

## Start automatically at sign-in

Run this once:

```powershell
.\install-startup.ps1
```

This adds a shortcut to your personal Windows Startup folder. It does not require administrator access. To remove it:

```powershell
.\uninstall-startup.ps1
```

## Read the one-second boolean

The named manual-reset event `Local\VoiceBot.TriggerActive` is the boolean. It is signaled (`true`) for 1,000 ms after wake-word recognition, then reset (`false`).

Example C# consumer:

```csharp
using (var wakeWord = EventWaitHandle.OpenExisting(@"Local\VoiceBot.TriggerActive"))
{
    bool triggered = wakeWord.WaitOne(0);
}
```

For event-driven use, call `wakeWord.WaitOne()` to sleep at zero CPU until VoiceBot activates it.

## Resource and privacy notes

- Uses the in-process Windows speech recognizer; there is no cloud speech call or bundled AI model. Codex itself uses your authenticated OpenAI connection after a command is transcribed.
- Loads only the wake phrase while idle. The broader dictation grammar is loaded temporarily after activation and then unloaded.
- Does no periodic polling and permits only one background Codex process at a time.
- Keeps no transcript queue. The latest Codex response and latest bounded error files are overwritten rather than appended.
- Uses Windows notification sounds, so no audio asset is loaded or shipped.
