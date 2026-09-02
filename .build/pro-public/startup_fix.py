from pathlib import Path

root=Path("src")

# Rename conflicting property and harden startup.
p=root/"PaidActivationWindow.xaml.cs"
s=p.read_text(encoding="utf-8")
s=s.replace("public bool Activated { get; private set; }","public bool LicenseActivated { get; private set; }")
s=s.replace("Activated=true;","LicenseActivated=true;")
p.write_text(s,encoding="utf-8")

(root/"App.xaml.cs").write_text(r'''using System.IO;
using System.Windows;
using System.Windows.Threading;

namespace RiuClickerCS;

public partial class App : Application
{
    static readonly string LogDir = Path.Combine(
        Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData),
        "RiuClickerPro");
    static readonly string LogFile = Path.Combine(LogDir, "startup-error.txt");

    protected override void OnStartup(StartupEventArgs e)
    {
        base.OnStartup(e);
        ShutdownMode = ShutdownMode.OnExplicitShutdown;

        Directory.CreateDirectory(LogDir);
        try { File.WriteAllText(LogFile, $"START {DateTimeOffset.Now:O}\r\n"); } catch { }

        DispatcherUnhandledException += OnDispatcherUnhandledException;
        AppDomain.CurrentDomain.UnhandledException += (_, args) =>
        {
            try { File.AppendAllText(LogFile, "APPDOMAIN: " + args.ExceptionObject + "\r\n"); } catch { }
        };
        TaskScheduler.UnobservedTaskException += (_, args) =>
        {
            try { File.AppendAllText(LogFile, "TASK: " + args.Exception + "\r\n"); } catch { }
            args.SetObserved();
        };

        Dispatcher.BeginInvoke(async () =>
        {
            try
            {
                var key = PaidLicenseService.LoadKey();
                if (!string.IsNullOrWhiteSpace(key))
                {
                    var check = await PaidLicenseService.ValidateAsync(key);
                    if (check.Ok)
                    {
                        OpenMain();
                        return;
                    }
                    PaidLicenseService.ClearKey();
                }

                var activation = new PaidActivationWindow();
                var result = activation.ShowDialog();
                if (result != true || !activation.LicenseActivated)
                {
                    Shutdown();
                    return;
                }
                OpenMain();
            }
            catch (Exception ex)
            {
                Crash("STARTUP", ex);
            }
        });
    }

    void OnDispatcherUnhandledException(object sender, DispatcherUnhandledExceptionEventArgs e)
    {
        Crash("DISPATCHER", e.Exception);
        e.Handled = true;
    }

    void Crash(string where, Exception ex)
    {
        try
        {
            File.AppendAllText(LogFile, where + ": " + ex + "\r\n");
            MessageBox.Show(
                "RiuClicker Pro startup error.\n\n" + ex.Message +
                "\n\nLog: " + LogFile,
                "RiuClicker Pro",
                MessageBoxButton.OK,
                MessageBoxImage.Error);
        }
        catch { }
        Shutdown();
    }

    void OpenMain()
    {
        var main = new MainWindow();
        MainWindow = main;
        ShutdownMode = ShutdownMode.OnMainWindowClose;
        main.Show();
        main.Activate();
    }
}
''',encoding="utf-8")

print("startup hardening applied")
