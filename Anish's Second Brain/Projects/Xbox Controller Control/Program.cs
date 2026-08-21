using System.Runtime.InteropServices;
using Microsoft.Win32;

namespace XboxControllerControl;

internal static class Program
{
    [STAThread]
    private static void Main()
    {
        ApplicationConfiguration.Initialize();
        using var app = new ControllerMouseApplication();
        Application.Run(app);
    }
}

internal sealed class ControllerMouseApplication : ApplicationContext
{
    private readonly NotifyIcon trayIcon;
    private readonly System.Windows.Forms.Timer pollTimer;
    private readonly ControllerMouseController controller = new();
    private bool hasController;

    public ControllerMouseApplication()
    {
        InstallStartupEntry();
        trayIcon = new NotifyIcon
        {
            Icon = SystemIcons.Application,
            Visible = true,
            Text = "Xbox Controller Control"
        };

        var menu = new ContextMenuStrip();
        menu.Items.Add("Switch mode", null, (_, _) => controller.ToggleMode());
        menu.Items.Add("Exit", null, (_, _) => ExitThread());
        trayIcon.ContextMenuStrip = menu;
        trayIcon.DoubleClick += (_, _) => controller.ToggleMode();

        pollTimer = new System.Windows.Forms.Timer { Interval = 8 };
        pollTimer.Tick += (_, _) => PollController();
        pollTimer.Start();
    }

    private static void InstallStartupEntry()
    {
        using var runKey = Registry.CurrentUser.CreateSubKey(
            "Software\\Microsoft\\Windows\\CurrentVersion\\Run");
        runKey?.SetValue("XboxControllerControl", $"\"{Application.ExecutablePath}\"");
    }

    private void PollController()
    {
        var state = XInput.TryGetState(0);
        var connected = state.HasValue;

        if (connected && !hasController)
        {
            hasController = true;
            controller.OnConnected();
            trayIcon.ShowBalloonTip(1200, "Xbox Controller Control", "Controller connected: Desktop mode", ToolTipIcon.Info);
        }
        else if (!connected && hasController)
        {
            hasController = false;
            controller.OnDisconnected();
            trayIcon.ShowBalloonTip(1200, "Xbox Controller Control", "Controller disconnected", ToolTipIcon.Warning);
        }

        if (state.HasValue)
            controller.Process(state.Value);

        trayIcon.Text = $"Xbox Controller Control - {controller.ModeName}";
    }

    protected override void ExitThreadCore()
    {
        pollTimer.Stop();
        trayIcon.Visible = false;
        trayIcon.Dispose();
        base.ExitThreadCore();
    }
}

internal sealed class ControllerMouseController
{
    // Change these mappings when you provide the desired controls.
    private const XInputButton ToggleButton = XInputButton.Back;
    private const int Deadzone = 4_000;
    private const double LeftStickPixelsPerTick = 15;
    private const double RightStickPixelsPerTick = 35;
    private double verticalScrollRemainder;
    private double horizontalScrollRemainder;

    private bool desktopMode;
    private XInputState previousState;
    private bool hasPreviousState;

    public string ModeName => desktopMode ? "Desktop mode" : "Game mode";

    public void OnConnected()
    {
        desktopMode = true;
        hasPreviousState = false;
    }

    public void OnDisconnected()
    {
        hasPreviousState = false;
        MouseInput.ReleaseAll();
    }

    public void ToggleMode()
    {
        desktopMode = !desktopMode;
        if (!desktopMode)
            MouseInput.ReleaseAll();
        hasPreviousState = false; // Avoid carrying held buttons across the mode boundary.
    }

    public void Process(XInputState state)
    {
        var current = state.Gamepad;
        var previous = previousState.Gamepad;

        if (IsPressed(current, previous, ToggleButton))
            ToggleMode();

        if (desktopMode)
        {
            var x = ApplyDeadzone(current.LeftThumbX);
            var y = ApplyDeadzone(current.LeftThumbY);
            MouseInput.Move(x * LeftStickPixelsPerTick, -y * LeftStickPixelsPerTick);

            var rightX = ApplyDeadzone(current.RightThumbX);
            var rightY = ApplyDeadzone(current.RightThumbY);
            MouseInput.Move(rightX * RightStickPixelsPerTick, -rightY * RightStickPixelsPerTick);

            MouseInput.SetButton(MouseButton.Right, current.LeftTrigger > 35);
            MouseInput.SetButton(MouseButton.Left, current.RightTrigger > 35);
            MouseInput.SetButton(MouseButton.Middle, IsDown(current, XInputButton.RightThumb));

            // D-pad scrolling. Accumulation keeps the scroll rate smooth at an 8 ms poll interval.
            verticalScrollRemainder += IsDown(current, XInputButton.DPadUp) ? 1.0 : 0;
            verticalScrollRemainder -= IsDown(current, XInputButton.DPadDown) ? 1.0 : 0;
            horizontalScrollRemainder += IsDown(current, XInputButton.DPadRight) ? 1.0 : 0;
            horizontalScrollRemainder -= IsDown(current, XInputButton.DPadLeft) ? 1.0 : 0;
            MouseInput.Scroll(ref verticalScrollRemainder, false);
            MouseInput.Scroll(ref horizontalScrollRemainder, true);
        }

        previousState = state;
        hasPreviousState = true;
    }

    private bool IsPressed(XInputGamepad current, XInputGamepad previous, XInputButton button) =>
        hasPreviousState && IsDown(current, button) && !IsDown(previous, button);

    private static bool IsDown(XInputGamepad gamepad, XInputButton button) =>
        (gamepad.Buttons & (ushort)button) != 0;

    private static double ApplyDeadzone(short value)
    {
        // Promote before Abs: Math.Abs(short.MinValue) overflows at -32768.
        var integerValue = (int)value;
        var magnitude = Math.Abs(integerValue);
        if (magnitude <= Deadzone) return 0;
        var sign = Math.Sign(integerValue);
        return sign * (magnitude - Deadzone) / (32767.0 - Deadzone);
    }
}

internal enum MouseButton { Left, Right, Middle }

internal static class MouseInput
{
    private const uint InputMouse = 0;
    private const uint MouseMove = 0x0001;
    private const uint LeftDown = 0x0002, LeftUp = 0x0004;
    private const uint RightDown = 0x0008, RightUp = 0x0010;
    private const uint MiddleDown = 0x0020, MiddleUp = 0x0040;
    private static readonly HashSet<MouseButton> heldButtons = [];

    public static void Move(double x, double y)
    {
        if (x == 0 && y == 0) return;
        Send(new INPUT { type = InputMouse, mouseInput = new MOUSEINPUT { dx = (int)Math.Round(x), dy = (int)Math.Round(y), flags = MouseMove } });
    }

    public static void Scroll(ref double remainder, bool horizontal)
    {
        const double scrollUnitsPerTick = 15;
        var units = (int)Math.Truncate(remainder * scrollUnitsPerTick);
        if (units == 0) return;
        remainder -= units / scrollUnitsPerTick;
        Send(new INPUT
        {
            type = InputMouse,
            mouseInput = new MOUSEINPUT
            {
                mouseData = unchecked((uint)units),
                flags = horizontal ? 0x01000u : 0x0800u
            }
        });
    }

    public static void SetButton(MouseButton button, bool down)
    {
        if (down == heldButtons.Contains(button)) return;
        heldButtons.Add(button);
        if (!down) heldButtons.Remove(button);
        var flags = button switch
        {
            MouseButton.Left => down ? LeftDown : LeftUp,
            MouseButton.Right => down ? RightDown : RightUp,
            _ => down ? MiddleDown : MiddleUp
        };
        Send(new INPUT { type = InputMouse, mouseInput = new MOUSEINPUT { flags = flags } });
    }

    public static void ReleaseAll()
    {
        foreach (var button in heldButtons.ToArray())
            SetButton(button, false);
    }

    private static void Send(INPUT input)
    {
        if (SendInput(1, [input], Marshal.SizeOf<INPUT>()) == 0)
            Marshal.GetLastWin32Error();
    }

    [DllImport("user32.dll", SetLastError = true)]
    private static extern uint SendInput(uint numberOfInputs, INPUT[] inputs, int size);

    [StructLayout(LayoutKind.Sequential)] private struct INPUT { public uint type; public MOUSEINPUT mouseInput; }
    [StructLayout(LayoutKind.Sequential)] private struct MOUSEINPUT { public int dx, dy; public uint mouseData, flags, time; public nint extraInfo; }
}

[Flags]
internal enum XInputButton : ushort
{
    DPadUp = 0x0001, DPadDown = 0x0002, DPadLeft = 0x0004, DPadRight = 0x0008,
    Start = 0x0010, Back = 0x0020, LeftThumb = 0x0040, RightThumb = 0x0080,
    LeftShoulder = 0x0100, RightShoulder = 0x0200, A = 0x1000, B = 0x2000, X = 0x4000, Y = 0x8000
}

internal static class XInput
{
    [DllImport("xinput1_4.dll", EntryPoint = "XInputGetState")]
    private static extern uint GetState(uint userIndex, out XInputState state);

    public static XInputState? TryGetState(uint index) => GetState(index, out var state) == 0 ? state : null;
}

[StructLayout(LayoutKind.Sequential)]
internal struct XInputState { public uint PacketNumber; public XInputGamepad Gamepad; }

[StructLayout(LayoutKind.Sequential)]
internal struct XInputGamepad
{
    public ushort Buttons;
    public byte LeftTrigger, RightTrigger;
    public short LeftThumbX, LeftThumbY, RightThumbX, RightThumbY;
}
