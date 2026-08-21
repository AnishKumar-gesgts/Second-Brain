// Minimal local Spotify MCP bridge. Credentials and refresh tokens stay outside this repo.
const fs = require('fs');
const path = require('path');
const http = require('http');
const crypto = require('crypto');
const { spawn } = require('child_process');

const HOME = process.env.USERPROFILE || process.env.HOME || process.cwd();
const CONFIG_PATH = path.join(HOME, '.codex', 'spotify.env');
const TOKEN_PATH = path.join(process.env.LOCALAPPDATA || path.join(HOME, 'AppData', 'Local'), 'VoiceBot', 'spotify-token.json');
const REDIRECT_URI = 'http://127.0.0.1:8888/callback';
const SCOPES = ['user-read-playback-state', 'user-read-currently-playing', 'user-modify-playback-state', 'playlist-read-private', 'playlist-read-collaborative'];

function loadEnv() {
  const values = {};
  if (!fs.existsSync(CONFIG_PATH)) return values;
  for (const line of fs.readFileSync(CONFIG_PATH, 'utf8').split(/\r?\n/)) {
    const match = line.match(/^\s*([A-Z0-9_]+)\s*=\s*(.*?)\s*$/);
    if (match && !match[1].startsWith('#')) values[match[1]] = match[2].replace(/^['"]|['"]$/g, '');
  }
  return Object.assign(values, process.env);
}

const env = loadEnv();
function fail(message) { throw new Error(message); }
function jsonResponse(text, isError) { return { content: [{ type: 'text', text }], ...(isError ? { isError: true } : {}) }; }
function send(id, result, error) { process.stdout.write(JSON.stringify(error ? { jsonrpc: '2.0', id, error } : { jsonrpc: '2.0', id, result }) + '\n'); }
function tokenRead() { try { return JSON.parse(fs.readFileSync(TOKEN_PATH, 'utf8')); } catch (_) { return null; } }
function tokenWrite(token) { fs.mkdirSync(path.dirname(TOKEN_PATH), { recursive: true }); fs.writeFileSync(TOKEN_PATH, JSON.stringify(token), { encoding: 'utf8', mode: 0o600 }); }
function base64url(buffer) { return buffer.toString('base64').replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, ''); }

async function beginAuth() {
  if (!env.SPOTIFY_CLIENT_ID) fail('Create ~/.codex/spotify.env with SPOTIFY_CLIENT_ID first.');
  const verifier = base64url(crypto.randomBytes(48));
  const challenge = base64url(crypto.createHash('sha256').update(verifier).digest());
  const state = base64url(crypto.randomBytes(24));
  const url = 'https://accounts.spotify.com/authorize?' + new URLSearchParams({
    client_id: env.SPOTIFY_CLIENT_ID, response_type: 'code', redirect_uri: REDIRECT_URI,
    code_challenge_method: 'S256', code_challenge: challenge, state, scope: SCOPES.join(' ')
  }).toString();

  const server = http.createServer(async (request, response) => {
    const parsed = new URL(request.url, REDIRECT_URI);
    if (parsed.pathname !== '/callback') { response.end('Spotify MCP is running.'); return; }
    if (parsed.searchParams.get('state') !== state) { response.statusCode = 400; response.end('Invalid OAuth state.'); return; }
    const code = parsed.searchParams.get('code');
    if (!code) { response.statusCode = 400; response.end('Spotify authorization failed.'); return; }
    try {
      const body = new URLSearchParams({ grant_type: 'authorization_code', code, redirect_uri: REDIRECT_URI, client_id: env.SPOTIFY_CLIENT_ID, code_verifier: verifier });
      const tokenResponse = await fetch('https://accounts.spotify.com/api/token', { method: 'POST', headers: { 'Content-Type': 'application/x-www-form-urlencoded' }, body });
      const token = await tokenResponse.json();
      if (!tokenResponse.ok) throw new Error(token.error_description || 'Spotify token exchange failed.');
      token.expires_at = Date.now() + (token.expires_in * 1000);
      tokenWrite(token);
      response.end('Spotify authorization complete. You can close this window.');
      setTimeout(() => server.close(), 250);
    } catch (error) { response.statusCode = 500; response.end(error.message); }
  });
  await new Promise((resolve, reject) => server.listen(8888, '127.0.0.1', resolve).on('error', reject));
  spawn('cmd', ['/c', 'start', '', url], { windowsHide: true, detached: true, stdio: 'ignore' }).unref();
  return 'A Spotify authorization window was opened. Approve access, then retry your command. Redirect URI: ' + REDIRECT_URI;
}

async function accessToken() {
  let token = tokenRead();
  if (!token) fail('Spotify is not authorized. Call spotify_auth, approve the browser window, then retry.');
  if (token.expires_at && token.expires_at > Date.now() + 60000) return token.access_token;
  const body = new URLSearchParams({ grant_type: 'refresh_token', refresh_token: token.refresh_token, client_id: env.SPOTIFY_CLIENT_ID });
  const response = await fetch('https://accounts.spotify.com/api/token', { method: 'POST', headers: { 'Content-Type': 'application/x-www-form-urlencoded' }, body });
  const refreshed = await response.json();
  if (!response.ok) fail(refreshed.error_description || 'Spotify token refresh failed.');
  token.access_token = refreshed.access_token; token.expires_at = Date.now() + refreshed.expires_in * 1000;
  if (refreshed.refresh_token) token.refresh_token = refreshed.refresh_token;
  tokenWrite(token); return token.access_token;
}

async function spotify(endpoint, options) {
  const token = await accessToken();
  const response = await fetch('https://api.spotify.com/v1' + endpoint, Object.assign({}, options, { headers: Object.assign({ Authorization: 'Bearer ' + token }, options && options.headers) }));
  if (response.status === 204) return null;
  const text = await response.text(); let data = null; try { data = text ? JSON.parse(text) : null; } catch (_) { data = text; }
  if (!response.ok) fail((data && (data.error && data.error.message || data.message)) || ('Spotify API returned HTTP ' + response.status));
  return data;
}

const tools = [
  { name: 'spotify_auth', description: 'Authorize this local MCP server with Spotify using OAuth PKCE.', inputSchema: { type: 'object', properties: {}, additionalProperties: false } },
  { name: 'spotify_search', description: 'Search Spotify tracks, artists, albums, and playlists.', inputSchema: { type: 'object', properties: { query: { type: 'string' } }, required: ['query'] } },
  { name: 'spotify_play', description: 'Start playback of a Spotify track URI on the active device. Requires Spotify Premium.', inputSchema: { type: 'object', properties: { uri: { type: 'string', description: 'spotify:track:... URI' } }, required: ['uri'] } },
  { name: 'spotify_pause', description: 'Pause the active Spotify playback device.', inputSchema: { type: 'object', properties: {}, additionalProperties: false } },
  { name: 'spotify_next', description: 'Skip to the next Spotify track.', inputSchema: { type: 'object', properties: {}, additionalProperties: false } },
  { name: 'spotify_currently_playing', description: 'Read the currently playing Spotify track.', inputSchema: { type: 'object', properties: {}, additionalProperties: false } }
];

async function callTool(name, args) {
  if (name === 'spotify_auth') return jsonResponse(await beginAuth());
  if (name === 'spotify_search') {
    const data = await spotify('/search?type=track,artist,album,playlist&limit=5&q=' + encodeURIComponent(args.query));
    return jsonResponse(JSON.stringify(data, null, 2));
  }
  if (name === 'spotify_play') {
    await spotify('/me/player/play', { method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ uris: [args.uri] }) });
    return jsonResponse('Playback started for ' + args.uri + '.');
  }
  if (name === 'spotify_pause') { await spotify('/me/player/pause', { method: 'PUT' }); return jsonResponse('Playback paused.'); }
  if (name === 'spotify_next') { await spotify('/me/player/next', { method: 'POST' }); return jsonResponse('Skipped to the next track.'); }
  if (name === 'spotify_currently_playing') { return jsonResponse(JSON.stringify(await spotify('/me/player/currently-playing', {}), null, 2)); }
  fail('Unknown Spotify tool: ' + name);
}

process.stdin.setEncoding('utf8'); let buffer = '';
process.stdin.on('data', chunk => { buffer += chunk; let newline; while ((newline = buffer.indexOf('\n')) >= 0) { const line = buffer.slice(0, newline).trim(); buffer = buffer.slice(newline + 1); if (!line) continue; let request; try { request = JSON.parse(line); } catch (_) { continue; } handle(request); } });
async function handle(request) {
  if (!request.id) return;
  try {
    if (request.method === 'initialize') send(request.id, { protocolVersion: '2024-11-05', capabilities: { tools: {} }, serverInfo: { name: 'voicebot-spotify', version: '1.0.0' } });
    else if (request.method === 'tools/list') send(request.id, { tools });
    else if (request.method === 'tools/call') send(request.id, await callTool(request.params.name, request.params.arguments || {}));
    else send(request.id, {});
  } catch (error) { send(request.id, jsonResponse(error.message, true)); }
}
