using System;
using System.Drawing;
using System.Speech.Synthesis;
using System.Threading;
using System.Windows.Forms;

internal sealed class StatusOverlay : Form
{
    private const int WsExNoActivate = 0x08000000;
    private const int WsExToolWindow = 0x00000080;

    private static readonly ManualResetEvent Ready = new ManualResetEvent(false);
    private static StatusOverlay instance;
    private static Exception startupError;

    private readonly Label titleLabel;
    private readonly Label bodyLabel;
    private readonly System.Windows.Forms.Timer hideTimer;
    private readonly bool speechEnabled;
    private readonly int speechMaximumCharacters;
    private readonly string requestedVoice;
    private SpeechSynthesizer synthesizer;

    private StatusOverlay(bool enableSpeech, int maximumSpeechCharacters, int displaySeconds, string voiceName)
    {
        speechEnabled = enableSpeech;
        speechMaximumCharacters = maximumSpeechCharacters;
        requestedVoice = voiceName;

        Text = "VoiceBot";
        FormBorderStyle = FormBorderStyle.None;
        ShowInTaskbar = false;
        StartPosition = FormStartPosition.Manual;
        TopMost = true;
        Width = 390;
        Height = 165;
        BackColor = Color.FromArgb(25, 28, 34);
        Opacity = 0.94;
        Padding = new Padding(16, 13, 16, 13);

        titleLabel = new Label
        {
            Dock = DockStyle.Top,
            Height = 29,
            ForeColor = Color.FromArgb(94, 211, 255),
            Font = new Font("Segoe UI Semibold", 12.5f, FontStyle.Bold),
            TextAlign = ContentAlignment.MiddleLeft
        };

        bodyLabel = new Label
        {
            Dock = DockStyle.Fill,
            ForeColor = Color.WhiteSmoke,
            Font = new Font("Segoe UI", 10.5f, FontStyle.Regular),
            TextAlign = ContentAlignment.TopLeft,
            AutoEllipsis = true,
            Padding = new Padding(0, 6, 0, 0)
        };

        Controls.Add(bodyLabel);
        Controls.Add(titleLabel);

        hideTimer = new System.Windows.Forms.Timer();
        hideTimer.Interval = Math.Max(1, displaySeconds) * 1000;
        hideTimer.Tick += delegate
        {
            hideTimer.Stop();
            Hide();
        };

        bodyLabel.Click += delegate
        {
            try
            {
                if (!string.IsNullOrWhiteSpace(bodyLabel.Text))
                    Clipboard.SetText(bodyLabel.Text);
            }
            catch { }
        };
    }

    protected override bool ShowWithoutActivation
    {
        get { return true; }
    }

    protected override CreateParams CreateParams
    {
        get
        {
            CreateParams parameters = base.CreateParams;
            parameters.ExStyle |= WsExNoActivate | WsExToolWindow;
            return parameters;
        }
    }

    public static void Start(bool enableSpeech, int maximumSpeechCharacters, int displaySeconds, string voiceName)
    {
        var thread = new Thread(delegate()
        {
            try
            {
                Application.EnableVisualStyles();
                Application.SetCompatibleTextRenderingDefault(false);
                instance = new StatusOverlay(enableSpeech, maximumSpeechCharacters, displaySeconds, voiceName);
                Ready.Set();
                Application.Run(instance);
            }
            catch (Exception ex)
            {
                startupError = ex;
                Ready.Set();
            }
        });
        thread.Name = "VoiceBot overlay";
        thread.IsBackground = true;
        thread.SetApartmentState(ApartmentState.STA);
        thread.Start();

        if (!Ready.WaitOne(TimeSpan.FromSeconds(5)))
            throw new InvalidOperationException("The VoiceBot overlay did not start in time.");
        if (startupError != null)
            throw new InvalidOperationException("The VoiceBot overlay could not start.", startupError);
    }

    public static void Listening()
    {
        Dispatch(delegate
        {
            instance.CancelSpeech();
            // Listening is transient too: a stalled speech engine must not leave the card
            // permanently covering the desktop.
            instance.ShowMessage("LISTENING", "Speak your command now...", true);
        });
    }

    public static void Working(string transcript)
    {
        Dispatch(delegate
        {
            instance.ShowMessage("WORKING", "You: " + transcript, false);
        });
    }

    public static void Information(string title, string text)
    {
        Dispatch(delegate { instance.ShowMessage(title, text, true); });
    }

    public static void Response(string response, bool needsClarification)
    {
        Dispatch(delegate
        {
            instance.ShowMessage(needsClarification ? "CLARIFICATION NEEDED" : "CODEX", response, true);
            instance.Speak(response);
        });
    }

    private static void Dispatch(MethodInvoker action)
    {
        StatusOverlay current = instance;
        if (current == null || current.IsDisposed)
            return;
        try
        {
            if (current.InvokeRequired)
                current.BeginInvoke(action);
            else
                action();
        }
        catch (InvalidOperationException) { }
    }

    private void ShowMessage(string title, string body, bool autoHide)
    {
        hideTimer.Stop();
        titleLabel.Text = title;
        bodyLabel.Text = LimitForDisplay(body);

        Rectangle workArea = Screen.PrimaryScreen.WorkingArea;
        Location = new Point(workArea.Right - Width - 18, workArea.Top + 18);

        if (!Visible)
            Show();
        BringToFront();

        if (autoHide)
            hideTimer.Start();
    }

    private void Speak(string text)
    {
        if (!speechEnabled || string.IsNullOrWhiteSpace(text))
            return;

        if (synthesizer == null)
        {
            synthesizer = new SpeechSynthesizer();
            synthesizer.Rate = 0;
            synthesizer.Volume = 100;
            if (!string.IsNullOrWhiteSpace(requestedVoice))
            {
                foreach (InstalledVoice installed in synthesizer.GetInstalledVoices())
                {
                    if (installed.VoiceInfo.Name.IndexOf(requestedVoice, StringComparison.OrdinalIgnoreCase) >= 0)
                    {
                        synthesizer.SelectVoice(installed.VoiceInfo.Name);
                        break;
                    }
                }
            }
        }

        string spoken = CleanForSpeech(text);
        if (spoken.Length > speechMaximumCharacters)
            spoken = spoken.Substring(0, speechMaximumCharacters) + ". The remainder is shown on screen.";

        synthesizer.SpeakAsyncCancelAll();
        synthesizer.SpeakAsync(spoken);
    }

    private void CancelSpeech()
    {
        if (synthesizer != null)
            synthesizer.SpeakAsyncCancelAll();
    }

    private static string LimitForDisplay(string text)
    {
        if (string.IsNullOrWhiteSpace(text))
            return "No response text was returned.";
        string trimmed = text.Trim();
        return trimmed.Length <= 1200 ? trimmed : trimmed.Substring(0, 1200) + "...";
    }

    private static string CleanForSpeech(string text)
    {
        return text.Replace("`", string.Empty)
            .Replace("#", string.Empty)
            .Replace("*", string.Empty)
            .Replace("_", " ")
            .Replace("\r", " ")
            .Replace("\n", " ")
            .Trim();
    }

    protected override void Dispose(bool disposing)
    {
        if (disposing)
        {
            hideTimer.Dispose();
            if (synthesizer != null)
                synthesizer.Dispose();
        }
        base.Dispose(disposing);
    }
}
