using System.Windows;

namespace RiuClicker;

public partial class App : Application
{
    protected override async void OnStartup(StartupEventArgs e)
    {
        base.OnStartup(e);
        ShutdownMode = ShutdownMode.OnExplicitShutdown;

        var savedKey = LicenseService.LoadSavedKey();
        if (!string.IsNullOrWhiteSpace(savedKey))
        {
            var check = await LicenseService.ValidateAsync(savedKey);
            if (check.Ok)
            {
                OpenMainWindow();
                return;
            }

            LicenseService.ClearSavedKey();
        }

        var activation = new ActivationWindow();
        var ok = activation.ShowDialog() == true && activation.Activated;
        if (!ok)
        {
            Shutdown();
            return;
        }

        OpenMainWindow();
    }

    private void OpenMainWindow()
    {
        var main = new MainWindow();
        MainWindow = main;
        ShutdownMode = ShutdownMode.OnMainWindowClose;
        main.Show();
    }
}
