from pathlib import Path

root = Path('src')

# Add GET KEY button below activation button.
p = root / 'ActivationWindow.xaml'
s = p.read_text(encoding='utf-8')
needle = '<Button x:Name="ActivateButton" Content="ACTIVATE LICENSE" Height="46" Click="Activate_Click" Background="#7C3AED" BorderBrush="#8B5CF6"/>'
replacement = needle + '\n                <Button x:Name="GetKeyButton" Content="GET KEY" Height="42" Margin="0,8,0,0" Click="GetKey_Click" Background="#151A29" BorderBrush="#38445F" Foreground="White"/>'
if 'x:Name="GetKeyButton"' not in s:
    if needle not in s:
        raise SystemExit('Activation button marker missing')
    s = s.replace(needle, replacement)
p.write_text(s, encoding='utf-8')

# GET KEY never downloads or opens a release asset. It opens a server-created
# LootLabs session. After the LootLabs postback is confirmed, the server page
# generates and displays the actual license key.
p = root / 'ActivationWindow.xaml.cs'
s = p.read_text(encoding='utf-8')
if 'using System.Diagnostics;' not in s:
    s = 'using System.Diagnostics;\n' + s
if 'private void GetKey_Click' not in s:
    marker = '    private async void Activate_Click(object sender, RoutedEventArgs e)\n'
    method = '''    private void GetKey_Click(object sender, RoutedEventArgs e)\n    {\n        var url = LicenseService.GetKeyStartUrl();\n        if (string.IsNullOrWhiteSpace(url))\n        {\n            StatusText.Text = "Key server is not configured. GET KEY will not download the clicker.";\n            return;\n        }\n\n        try\n        {\n            Process.Start(new ProcessStartInfo(url) { UseShellExecute = true });\n            StatusText.Text = "Key flow opened. Complete LootLabs, then copy the key shown on the final page.";\n        }\n        catch\n        {\n            StatusText.Text = "Could not open GET KEY page.";\n        }\n    }\n\n'''
    if marker not in s:
        raise SystemExit('Activate_Click marker missing')
    s = s.replace(marker, method + marker)
p.write_text(s, encoding='utf-8')

print('Applied verified GET KEY flow (no release download)')
