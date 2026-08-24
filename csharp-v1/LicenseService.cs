using System.Management;
using System.Net.Http;
using System.Security.Cryptography;
using System.Text;
using System.Text.Json;

namespace RiuClicker;

public sealed class LicenseResult
{
    public bool Ok { get; set; }
    public string Message { get; set; } = "";
    public string Plan { get; set; } = "";
    public DateTimeOffset? ExpiresAt { get; set; }
}

public static class LicenseService
{
    // After Firebase deploy, replace this with your HTTPS Function URL.
    // Example: https://europe-west1-YOUR_PROJECT.cloudfunctions.net/licenseApi
    public const string Endpoint = "https://europe-west1-YOUR_PROJECT.cloudfunctions.net/licenseApi";

    private static readonly HttpClient Http = new() { Timeout = TimeSpan.FromSeconds(8) };
    private static readonly string Folder = Path.Combine(
        Environment.GetFolderPath(Environment.SpecialFolder.ApplicationData), "RiuClicker");
    private static readonly string LicenseFile = Path.Combine(Folder, "license.json");

    public static string DeviceId()
    {
        var parts = new List<string>
        {
            Environment.MachineName,
            Environment.ProcessorCount.ToString(),
            Environment.OSVersion.VersionString
        };

        try
        {
            using var searcher = new ManagementObjectSearcher("SELECT UUID FROM Win32_ComputerSystemProduct");
            foreach (ManagementObject item in searcher.Get())
            {
                var uuid = item["UUID"]?.ToString();
                if (!string.IsNullOrWhiteSpace(uuid)) parts.Add(uuid);
            }
        }
        catch { }

        var raw = string.Join("|", parts);
        var hash = SHA256.HashData(Encoding.UTF8.GetBytes(raw));
        return Convert.ToHexString(hash)[..24];
    }

    public static string? LoadSavedKey()
    {
        try
        {
            if (!File.Exists(LicenseFile)) return null;
            using var doc = JsonDocument.Parse(File.ReadAllText(LicenseFile));
            return doc.RootElement.TryGetProperty("key", out var k) ? k.GetString() : null;
        }
        catch { return null; }
    }

    public static void SaveKey(string key)
    {
        Directory.CreateDirectory(Folder);
        File.WriteAllText(LicenseFile, JsonSerializer.Serialize(new { key = Normalize(key) }));
    }

    public static void ClearSavedKey()
    {
        try { if (File.Exists(LicenseFile)) File.Delete(LicenseFile); } catch { }
    }

    public static async Task<LicenseResult> ActivateAsync(string key, CancellationToken ct = default)
        => await SendAsync("activate", key, ct);

    public static async Task<LicenseResult> ValidateAsync(string key, CancellationToken ct = default)
        => await SendAsync("validate", key, ct);

    private static async Task<LicenseResult> SendAsync(string action, string key, CancellationToken ct)
    {
        key = Normalize(key);
        if (key.Length < 12) return new() { Ok = false, Message = "Invalid license key format." };
        if (Endpoint.Contains("YOUR_PROJECT", StringComparison.OrdinalIgnoreCase))
            return new() { Ok = false, Message = "License server is not configured yet." };

        try
        {
            var json = JsonSerializer.Serialize(new
            {
                action,
                key,
                deviceId = DeviceId(),
                app = "RiuClicker",
                version = "1.0"
            });
            using var req = new HttpRequestMessage(HttpMethod.Post, Endpoint)
            {
                Content = new StringContent(json, Encoding.UTF8, "application/json")
            };
            using var res = await Http.SendAsync(req, ct);
            var body = await res.Content.ReadAsStringAsync(ct);
            if (!res.IsSuccessStatusCode)
                return new() { Ok = false, Message = "License server error." };

            using var doc = JsonDocument.Parse(body);
            var root = doc.RootElement;
            var result = new LicenseResult
            {
                Ok = root.TryGetProperty("ok", out var ok) && ok.GetBoolean(),
                Message = root.TryGetProperty("message", out var msg) ? msg.GetString() ?? "" : "",
                Plan = root.TryGetProperty("plan", out var plan) ? plan.GetString() ?? "" : ""
            };
            if (root.TryGetProperty("expiresAt", out var exp) && exp.ValueKind == JsonValueKind.String && DateTimeOffset.TryParse(exp.GetString(), out var dt))
                result.ExpiresAt = dt;
            return result;
        }
        catch (TaskCanceledException) { return new() { Ok = false, Message = "License server timeout." }; }
        catch { return new() { Ok = false, Message = "Could not connect to license server." }; }
    }

    private static string Normalize(string key)
        => key.Trim().ToUpperInvariant().Replace(" ", "");
}
