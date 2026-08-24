using System.Windows;

namespace RiuClicker;

public partial class ActivationWindow : Window
{
    public bool Activated { get; private set; }

    public ActivationWindow()
    {
        InitializeComponent();
        DeviceText.Text = LicenseService.DeviceId();
    }

    private async void Activate_Click(object sender, RoutedEventArgs e)
    {
        var key = KeyBox.Text.Trim();
        if (string.IsNullOrWhiteSpace(key))
        {
            StatusText.Text = "Enter your license key.";
            return;
        }

        ActivateButton.IsEnabled = false;
        StatusText.Text = "Checking license...";
        var result = await LicenseService.ActivateAsync(key);
        ActivateButton.IsEnabled = true;

        if (!result.Ok)
        {
            StatusText.Text = string.IsNullOrWhiteSpace(result.Message) ? "Activation failed." : result.Message;
            return;
        }

        LicenseService.SaveKey(key);
        Activated = true;
        StatusText.Text = result.ExpiresAt is { } exp
            ? $"Activated · {result.Plan} · until {exp.LocalDateTime:d}"
            : $"Activated · {result.Plan}";

        await Task.Delay(450);
        DialogResult = true;
        Close();
    }
}
