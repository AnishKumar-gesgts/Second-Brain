using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Globalization;
using System.IO;
using System.Media;
using System.Speech.Recognition;
using System.Text;
using System.Threading;

internal static class VoiceBot
{
    private const string EventName = @"Local\VoiceBot.TriggerActive";
    private const int ActiveMilliseconds = 1000;

    private static EventWaitHandle triggerEvent;
    private static Timer resetTimer;
    private static int isActive;
    private static readonly object CodexLock = new object();
    private static Process codexProcess;

    [STAThread]
    private static int Main(string[] args)
    {
        bool ownsInstance;
        using (var singleInstance = new Mutex(true, @"Local\VoiceBot.SingleInstance", out ownsInstance))
        {
            if (!ownsInstance)
                return 0;

            try
            {
                string appDirectory = AppDomain.CurrentDomain.BaseDirectory;
                var settings = Settings.Load(Path.Combine(appDirectory, "voicebot.ini"));
                settings.ResolvePaths(appDirectory);

                if (HasArgument(args, "--test-sound"))
                {
                    PlaySound(settings.Sound);
                    return 0;
                }

                // Fail at startup with a useful error instead of waiting until after dictation.
                settings.CodexPath = ResolveCodexPath(settings.CodexPath);
                StatusOverlay.Start(settings.SpeakResponses, settings.SpeechMaximumCharacters, settings.OverlaySeconds, settings.TtsVoice);

                if (HasArgument(args, "--test-overlay"))
                {
                    StatusOverlay.Response("VoiceBot is ready. This is how short Codex responses will appear and sound.", false);
                    Thread.Sleep(5000);
                    return 0;
                }

                bool created;
                triggerEvent = new EventWaitHandle(false, EventResetMode.ManualReset, EventName, out created);
                triggerEvent.Reset();

                RunRecognizerLoop(settings);

                return 0;
            }
            catch (Exception ex)
            {
                WriteBoundedError(
                    Path.Combine(AppDomain.CurrentDomain.BaseDirectory, "voicebot-error.txt"),
                    ex.Message);
                SystemSounds.Hand.Play();
                return 1;
            }
            finally
            {
                if (triggerEvent != null)
                {
                    triggerEvent.Reset();
                    triggerEvent.Dispose();
                }
                if (resetTimer != null)
                    resetTimer.Dispose();
            }
        }
    }

    private static void RunRecognizerLoop(Settings settings)
    {
        while (true)
        {
            try
            {
                Grammar wakeGrammar;
                using (var recognizer = CreateRecognizer(settings, out wakeGrammar))
                {
                    recognizer.SetInputToDefaultAudioDevice();
                    string errorPath = Path.Combine(AppDomain.CurrentDomain.BaseDirectory, "voicebot-error.txt");
                    if (File.Exists(errorPath))
                        File.Delete(errorPath);
                    ListenForever(recognizer, wakeGrammar, settings);
                }
                return;
            }
            catch (Exception ex)
            {
                // Windows SAPI can transiently lose its recognizer/audio device. Recreate the
                // engine instead of allowing one interruption to terminate the 24/7 listener.
                WriteBoundedError(
                    Path.Combine(AppDomain.CurrentDomain.BaseDirectory, "voicebot-error.txt"),
                    "Speech engine interrupted; retrying in 3 seconds." + Environment.NewLine + ex.Message);
                StatusOverlay.Information("MICROPHONE RESTARTING", "Windows speech recognition was interrupted. Retrying automatically...");
                SystemSounds.Hand.Play();
                Thread.Sleep(3000);
            }
        }
    }

    private static void ListenForever(SpeechRecognitionEngine recognizer, Grammar wakeGrammar, Settings settings)
    {
        while (true)
        {
            recognizer.InitialSilenceTimeout = TimeSpan.FromSeconds(30);
            RecognitionResult wakeResult = recognizer.Recognize();
            if (wakeResult == null || wakeResult.Confidence < settings.MinimumConfidence)
                continue;

            Activate(settings.Sound);
            StatusOverlay.Listening();
            recognizer.UnloadGrammar(wakeGrammar);

            var dictation = new DictationGrammar();
            recognizer.LoadGrammar(dictation);
            recognizer.InitialSilenceTimeout = TimeSpan.FromSeconds(settings.DictationStartTimeoutSeconds);
            recognizer.BabbleTimeout = TimeSpan.FromSeconds(settings.DictationMaximumSeconds);
            recognizer.EndSilenceTimeout = TimeSpan.FromSeconds(settings.EndSilenceSeconds);
            recognizer.EndSilenceTimeoutAmbiguous = TimeSpan.FromSeconds(settings.EndSilenceSeconds + 0.5);

            // Let the acknowledgement sound finish before opening dictation.
            Thread.Sleep(350);
            RecognitionResult commandResult = recognizer.Recognize(TimeSpan.FromSeconds(settings.DictationMaximumSeconds));
            recognizer.UnloadGrammar(dictation);

            recognizer.LoadGrammar(wakeGrammar);

            if (commandResult == null || string.IsNullOrWhiteSpace(commandResult.Text))
            {
                SystemSounds.Question.Play();
                StatusOverlay.Information("NOT HEARD", "No command was recognized. Say the wake phrase and try again.");
                continue;
            }

            SubmitToCodex(commandResult.Text.Trim(), settings);
        }
    }

    private static SpeechRecognitionEngine CreateRecognizer(Settings settings, out Grammar wakeGrammar)
    {
        RecognizerInfo selected = null;
        foreach (RecognizerInfo info in SpeechRecognitionEngine.InstalledRecognizers())
        {
            if (info.Culture.Equals(CultureInfo.CurrentUICulture))
            {
                selected = info;
                break;
            }

            if (selected == null && info.Culture.TwoLetterISOLanguageName == CultureInfo.CurrentUICulture.TwoLetterISOLanguageName)
                selected = info;
        }

        if (selected == null)
            throw new InvalidOperationException("No Windows speech recognizer is installed for " + CultureInfo.CurrentUICulture.DisplayName + ".");

        var engine = new SpeechRecognitionEngine(selected);
        var phrases = new Choices();
        foreach (string phrase in SpokenForms(settings.Trigger))
            phrases.Add(phrase);

        var builder = new GrammarBuilder(phrases) { Culture = selected.Culture };
        wakeGrammar = new Grammar(builder) { Name = "VoiceBot wake word" };
        engine.LoadGrammar(wakeGrammar);
        return engine;
    }

    private static void SubmitToCodex(string transcript, Settings settings)
    {
        lock (CodexLock)
        {
            if (codexProcess != null && !codexProcess.HasExited)
            {
                // Only one agent task at a time; do not create an unbounded process queue.
                SystemSounds.Question.Play();
                StatusOverlay.Information("BUSY", "Codex is still processing the previous command.");
                return;
            }

            string responsePath = Path.Combine(AppDomain.CurrentDomain.BaseDirectory, "voicebot-last-response.txt");
            string errorPath = Path.Combine(AppDomain.CurrentDomain.BaseDirectory, "voicebot-codex-error.txt");
            if (File.Exists(responsePath))
                File.Delete(responsePath);
            StatusOverlay.Working(transcript);
            var errorText = new StringBuilder();
            var process = new Process();
            process.StartInfo = new ProcessStartInfo
            {
                FileName = settings.CodexPath,
                Arguments = "exec --ephemeral --model " + QuoteArgument(settings.CodexModel) + " --config model_reasoning_effort=" + settings.CodexReasoningEffort + " --sandbox workspace-write --skip-git-repo-check --color never -o " + QuoteArgument(responsePath) + " -",
                WorkingDirectory = settings.Workspace,
                UseShellExecute = false,
                CreateNoWindow = true,
                RedirectStandardInput = true,
                RedirectStandardOutput = true,
                RedirectStandardError = true
            };
            process.EnableRaisingEvents = true;
            process.OutputDataReceived += delegate { };
            process.ErrorDataReceived += delegate(object sender, DataReceivedEventArgs e)
            {
                if (string.IsNullOrEmpty(e.Data))
                    return;
                lock (errorText)
                {
                    if (errorText.Length < 8000)
                        errorText.AppendLine(e.Data);
                }
            };
            process.Exited += delegate
            {
                int exitCode = -1;
                try
                {
                    process.WaitForExit();
                    exitCode = process.ExitCode;
                }
                catch { }

                if (exitCode == 0)
                {
                    if (File.Exists(errorPath))
                        File.Delete(errorPath);
                    string response = File.Exists(responsePath)
                        ? File.ReadAllText(responsePath, Encoding.UTF8).Trim()
                        : "Codex finished successfully without returning text.";
                    bool needsClarification = LooksLikeClarification(response);
                    StatusOverlay.Response(response, needsClarification);
                    PlaySound(needsClarification ? settings.ClarificationSound : settings.ResponseCompleteSound);
                }
                else
                {
                    string message;
                    lock (errorText)
                        message = errorText.ToString();
                    WriteBoundedError(errorPath, "Codex exited with code " + exitCode + "." + Environment.NewLine + message);
                    StatusOverlay.Information("CODEX ERROR", "The command failed. See voicebot-codex-error.txt for details.");
                    SystemSounds.Hand.Play();
                }

                lock (CodexLock)
                {
                    if (object.ReferenceEquals(codexProcess, process))
                        codexProcess = null;
                }
                process.Dispose();
            };

            if (!process.Start())
                throw new InvalidOperationException("Codex CLI did not start.");

            codexProcess = process;
            process.BeginOutputReadLine();
            process.BeginErrorReadLine();

            string prompt =
                "The following request was transcribed from speech and may contain recognition errors. " +
                "Carry it out in the current workspace when it is clear and safe. " +
                "If it is ambiguous, destructive, security-sensitive, or high-impact, do not act; explain what clarification is needed.\n\n" +
                transcript;
            process.StandardInput.Write(prompt);
            process.StandardInput.Close();
            PlaySound(settings.CommandSubmittedSound);
        }
    }

    private static bool LooksLikeClarification(string response)
    {
        if (string.IsNullOrWhiteSpace(response))
            return false;
        string text = response.ToLowerInvariant();
        return text.Contains("?")
            || text.Contains("please clarify")
            || text.Contains("could you clarify")
            || text.Contains("which would you like")
            || text.Contains("what would you like")
            || text.Contains("what should i")
            || text.Contains("which option");
    }

    private static string ResolveCodexPath(string configuredPath)
    {
        if (!string.IsNullOrWhiteSpace(configuredPath) && !configuredPath.Equals("auto", StringComparison.OrdinalIgnoreCase))
        {
            if (File.Exists(configuredPath))
                return Path.GetFullPath(configuredPath);
            throw new FileNotFoundException("Configured CodexPath was not found: " + configuredPath);
        }

        string pathValue = Environment.GetEnvironmentVariable("PATH") ?? string.Empty;
        foreach (string directory in pathValue.Split(Path.PathSeparator))
        {
            if (string.IsNullOrWhiteSpace(directory))
                continue;
            string candidate = Path.Combine(directory.Trim(), "codex.exe");
            if (File.Exists(candidate))
                return candidate;
        }

        string extensions = Path.Combine(
            Environment.GetFolderPath(Environment.SpecialFolder.UserProfile),
            ".vscode", "extensions");
        if (Directory.Exists(extensions))
        {
            string[] directories = Directory.GetDirectories(extensions, "openai.chatgpt-*-win32-x64");
            Array.Sort(directories, StringComparer.OrdinalIgnoreCase);
            for (int index = directories.Length - 1; index >= 0; index--)
            {
                string candidate = Path.Combine(directories[index], "bin", "windows-x86_64", "codex.exe");
                if (File.Exists(candidate))
                    return candidate;
            }
        }

        throw new FileNotFoundException("codex.exe was not found on PATH or in the VS Code Codex extension. Install or sign in to Codex first.");
    }

    private static string QuoteArgument(string value)
    {
        return "\"" + value.Replace("\"", "\\\"") + "\"";
    }

    private static IEnumerable<string> SpokenForms(string trigger)
    {
        var unique = new HashSet<string>(StringComparer.OrdinalIgnoreCase);
        string trimmed = trigger.Trim();
        unique.Add(trimmed);

        var spaced = new StringBuilder();
        for (int i = 0; i < trimmed.Length; i++)
        {
            char current = trimmed[i];
            if (i > 0 && char.IsUpper(current) && (char.IsLower(trimmed[i - 1]) || char.IsDigit(trimmed[i - 1])))
                spaced.Append(' ');
            spaced.Append(current);
        }
        unique.Add(spaced.ToString());

        foreach (string phrase in unique)
            yield return phrase;
    }

    private static void Activate(string sound)
    {
        if (Interlocked.CompareExchange(ref isActive, 1, 0) != 0)
            return;

        triggerEvent.Set();
        PlaySound(sound);

        if (resetTimer == null)
            resetTimer = new Timer(delegate { Deactivate(); }, null, ActiveMilliseconds, Timeout.Infinite);
        else
            resetTimer.Change(ActiveMilliseconds, Timeout.Infinite);
    }

    private static void Deactivate()
    {
        triggerEvent.Reset();
        Interlocked.Exchange(ref isActive, 0);
    }

    private static void PlaySound(string sound)
    {
        switch (sound.ToLowerInvariant())
        {
            case "beep": SystemSounds.Beep.Play(); break;
            case "exclamation": SystemSounds.Exclamation.Play(); break;
            case "hand": SystemSounds.Hand.Play(); break;
            case "question": SystemSounds.Question.Play(); break;
            default: SystemSounds.Asterisk.Play(); break;
        }
    }

    private static void WriteBoundedError(string path, string message)
    {
        string bounded = message ?? string.Empty;
        if (bounded.Length > 12000)
            bounded = bounded.Substring(0, 12000);
        File.WriteAllText(path, DateTime.Now.ToString("u") + Environment.NewLine + bounded + Environment.NewLine);
    }

    private static bool HasArgument(string[] args, string wanted)
    {
        foreach (string arg in args)
            if (string.Equals(arg, wanted, StringComparison.OrdinalIgnoreCase))
                return true;
        return false;
    }

    private sealed class Settings
    {
        public string Trigger = "voice bot";
        public float MinimumConfidence = 0.60f;
        public string Sound = "Asterisk";
        public string CommandSubmittedSound = "Beep";
        public string ResponseCompleteSound = "Exclamation";
        public string ClarificationSound = "Question";
        public double DictationStartTimeoutSeconds = 8;
        public double EndSilenceSeconds = 1.2;
        public double DictationMaximumSeconds = 30;
        public string Workspace = "..";
        public string CodexPath = "auto";
        public string CodexModel = "gpt-5.6-luna";
        public string CodexReasoningEffort = "low";
        public bool SpeakResponses = true;
        public int SpeechMaximumCharacters = 500;
        public int OverlaySeconds = 15;
        public string TtsVoice = "Guy";

        public void ResolvePaths(string appDirectory)
        {
            if (!Path.IsPathRooted(Workspace))
                Workspace = Path.GetFullPath(Path.Combine(appDirectory, Workspace));
            if (!Directory.Exists(Workspace))
                throw new DirectoryNotFoundException("Configured Workspace was not found: " + Workspace);

            if (!CodexPath.Equals("auto", StringComparison.OrdinalIgnoreCase) && !Path.IsPathRooted(CodexPath))
                CodexPath = Path.GetFullPath(Path.Combine(appDirectory, CodexPath));
        }

        public static Settings Load(string path)
        {
            var result = new Settings();
            if (!File.Exists(path))
                return result;

            foreach (string rawLine in File.ReadAllLines(path))
            {
                string line = rawLine.Trim();
                if (line.Length == 0 || line.StartsWith("#") || line.StartsWith(";"))
                    continue;

                int separator = line.IndexOf('=');
                if (separator < 1)
                    continue;

                string key = line.Substring(0, separator).Trim();
                string value = line.Substring(separator + 1).Trim();
                if (key.Equals("Trigger", StringComparison.OrdinalIgnoreCase) && value.Length > 0)
                    result.Trigger = value;
                else if (key.Equals("Confidence", StringComparison.OrdinalIgnoreCase))
                    result.MinimumConfidence = ParseRange(value, result.MinimumConfidence, 0, 1);
                else if (key.Equals("Sound", StringComparison.OrdinalIgnoreCase) && value.Length > 0)
                    result.Sound = value;
                else if (key.Equals("CommandSubmittedSound", StringComparison.OrdinalIgnoreCase) && value.Length > 0)
                    result.CommandSubmittedSound = value;
                else if (key.Equals("ResponseCompleteSound", StringComparison.OrdinalIgnoreCase) && value.Length > 0)
                    result.ResponseCompleteSound = value;
                else if (key.Equals("ClarificationSound", StringComparison.OrdinalIgnoreCase) && value.Length > 0)
                    result.ClarificationSound = value;
                else if (key.Equals("DictationStartTimeoutSeconds", StringComparison.OrdinalIgnoreCase))
                    result.DictationStartTimeoutSeconds = ParseRange(value, result.DictationStartTimeoutSeconds, 1, 60);
                else if (key.Equals("EndSilenceSeconds", StringComparison.OrdinalIgnoreCase))
                    result.EndSilenceSeconds = ParseRange(value, result.EndSilenceSeconds, 0.5, 5);
                else if (key.Equals("DictationMaximumSeconds", StringComparison.OrdinalIgnoreCase))
                    result.DictationMaximumSeconds = ParseRange(value, result.DictationMaximumSeconds, 3, 120);
                else if (key.Equals("Workspace", StringComparison.OrdinalIgnoreCase) && value.Length > 0)
                    result.Workspace = value;
                else if (key.Equals("CodexPath", StringComparison.OrdinalIgnoreCase) && value.Length > 0)
                    result.CodexPath = value;
                else if (key.Equals("CodexModel", StringComparison.OrdinalIgnoreCase) && value.Length > 0)
                    result.CodexModel = value;
                else if (key.Equals("CodexReasoningEffort", StringComparison.OrdinalIgnoreCase) && (value.Equals("minimal", StringComparison.OrdinalIgnoreCase) || value.Equals("low", StringComparison.OrdinalIgnoreCase) || value.Equals("medium", StringComparison.OrdinalIgnoreCase) || value.Equals("high", StringComparison.OrdinalIgnoreCase)))
                    result.CodexReasoningEffort = value.ToLowerInvariant();
                else if (key.Equals("SpeakResponses", StringComparison.OrdinalIgnoreCase))
                    result.SpeakResponses = ParseBoolean(value, result.SpeakResponses);
                else if (key.Equals("SpeechMaximumCharacters", StringComparison.OrdinalIgnoreCase))
                    result.SpeechMaximumCharacters = (int)ParseRange(value, result.SpeechMaximumCharacters, 50, 5000);
                else if (key.Equals("OverlaySeconds", StringComparison.OrdinalIgnoreCase))
                    result.OverlaySeconds = (int)ParseRange(value, result.OverlaySeconds, 3, 120);
                else if (key.Equals("TtsVoice", StringComparison.OrdinalIgnoreCase))
                    result.TtsVoice = value;
            }
            return result;
        }

        private static float ParseRange(string value, float fallback, float minimum, float maximum)
        {
            float parsed;
            if (float.TryParse(value, NumberStyles.Float, CultureInfo.InvariantCulture, out parsed) && parsed >= minimum && parsed <= maximum)
                return parsed;
            return fallback;
        }

        private static double ParseRange(string value, double fallback, double minimum, double maximum)
        {
            double parsed;
            if (double.TryParse(value, NumberStyles.Float, CultureInfo.InvariantCulture, out parsed) && parsed >= minimum && parsed <= maximum)
                return parsed;
            return fallback;
        }

        private static bool ParseBoolean(string value, bool fallback)
        {
            bool parsed;
            return bool.TryParse(value, out parsed) ? parsed : fallback;
        }
    }
}
