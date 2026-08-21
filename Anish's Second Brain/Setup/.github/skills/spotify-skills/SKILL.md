---
name: spotify-skills
user-invocable: true
description: "Use when you want to pause Spotify or resume/play the current playlist again."
argument-hint: "Optional: pause, play again, or resume."
---

# Skill: Spotify Skills

Quick Spotify playback control for the current session.

## When to Use

- User says "pause Spotify", "stop the music", "play it again", or "resume Spotify"
- The goal is to control the currently playing Spotify session without searching for a track or playlist

## How It Works

1. If the request is to pause, call `mcp_spotify_pausePlayback`.
2. If the request is to play again or resume, call `mcp_spotify_resumePlayback`.
3. If a device target is needed, use the last active Spotify Connect device.
4. Confirm the result briefly.

## Notes

- Use `mcp_spotify_getAvailableDevices` first if the active device is unclear.
- Use `mcp_spotify_getNowPlaying` after resuming if you want to verify the track and context.