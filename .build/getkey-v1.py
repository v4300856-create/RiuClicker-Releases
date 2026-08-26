from pathlib import Path
import os

root = Path('src')
get_key_url = os.environ.get('RIU_GET_KEY_URL', '').strip() or 'https://loot-link.com/s?zTsiS0pO'
get_key_url_cs = get_key_url.replace('\\', '\\\\').replace('"', '\\"')

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

# Open publisher/key gateway link in the default browser.
p = root / 'ActivationWindow.xaml.cs'
s = p.read_text(encoding='utf-8')
if 'using System.Diagnostics;' not in s:
    s = 'using System.Diagnostics;\n' + s
if 'private void GetKey_Click' not in s:
    marker = '    private async void Activate_Click(object sender, RoutedEventArgs e)\n'
    method = f'''    private void GetKey_Click(object sender, RoutedEventArgs e)\n    {{\n        const string url = "{get_key_url_cs}";\n        try\n        {{\n            Process.Start(new ProcessStartInfo(url) {{ UseShellExecute = true }});\n            StatusText.Text = "GET KEY page opened in your browser.";\n        }}\n        catch\n        {{\n            StatusText.Text = "Could not open GET KEY page.";\n        }}\n    }}\n\n'''
    if marker not in s:
        raise SystemExit('Activate_Click marker missing')
    s = s.replace(marker, method + marker)
p.write_text(s, encoding='utf-8')

print('Applied GET KEY button; url=' + get_key_url)
