from pathlib import Path

root = Path('pro2-rust')

# Native Rust hotkey capture: bypass WebView keydown/mousedown completely.
p = root / 'src-tauri/src/main.rs'
s = p.read_text(encoding='utf-8')

capture_core = r'''
fn vk_code_is_down(vk: i32) -> bool {
    unsafe { (GetAsyncKeyState(vk) as u16 & 0x8000) != 0 }
}

fn capture_hotkey_blocking() -> Option<String> {
    let mut keys: Vec<(String, i32)> = vec![
        ("MOUSE1".into(), 0x01), ("MOUSE2".into(), 0x02), ("MOUSE3".into(), 0x04),
        ("MOUSE4".into(), 0x05), ("MOUSE5".into(), 0x06),
        ("BACKSPACE".into(), 0x08), ("TAB".into(), 0x09), ("ENTER".into(), 0x0D),
        ("SHIFT".into(), 0x10), ("CTRL".into(), 0x11), ("ALT".into(), 0x12),
        ("ESC".into(), 0x1B), ("SPACE".into(), 0x20),
        ("PAGEUP".into(), 0x21), ("PAGEDOWN".into(), 0x22), ("END".into(), 0x23),
        ("HOME".into(), 0x24), ("LEFT".into(), 0x25), ("UP".into(), 0x26),
        ("RIGHT".into(), 0x27), ("DOWN".into(), 0x28),
        ("INSERT".into(), 0x2D), ("DELETE".into(), 0x2E),
    ];
    for c in b'0'..=b'9' { keys.push(((c as char).to_string(), c as i32)); }
    for c in b'A'..=b'Z' { keys.push(((c as char).to_string(), c as i32)); }
    for n in 1..=24 { keys.push((format!("F{n}"), 0x70 + n - 1)); }

    // Ignore the mouse click/key that opened capture.
    let release_deadline = Instant::now() + Duration::from_secs(2);
    while Instant::now() < release_deadline {
        if !keys.iter().any(|(_, vk)| vk_code_is_down(*vk)) { break; }
        thread::sleep(Duration::from_millis(6));
    }

    let deadline = Instant::now() + Duration::from_secs(12);
    while Instant::now() < deadline {
        for (name, vk) in &keys {
            if vk_code_is_down(*vk) {
                if name == "ESC" { return None; }
                while vk_code_is_down(*vk) && Instant::now() < deadline {
                    thread::sleep(Duration::from_millis(5));
                }
                return Some(name.clone());
            }
        }
        thread::sleep(Duration::from_millis(4));
    }
    None
}
'''.strip()

marker = 'fn settings_path() -> PathBuf {'
if 'fn capture_hotkey_blocking()' not in s:
    if marker not in s:
        raise SystemExit('settings_path marker missing')
    s = s.replace(marker, capture_core + '\n\n' + marker, 1)

capture_cmd = r'''
#[tauri::command]
async fn capture_hotkey() -> Option<String> {
    tauri::async_runtime::spawn_blocking(capture_hotkey_blocking)
        .await
        .unwrap_or(None)
}
'''.strip()

marker = '#[tauri::command]\nfn cursor_position() -> Result<(i32, i32), String> {'
if 'async fn capture_hotkey()' not in s:
    if marker not in s:
        raise SystemExit('cursor_position marker missing')
    s = s.replace(marker, capture_cmd + '\n\n' + marker, 1)

old_handler = 'stop_all, cursor_position, pick_background, host_lobby, join_lobby, leave_lobby'
if 'stop_all, capture_hotkey, cursor_position' not in s:
    if old_handler not in s:
        raise SystemExit('invoke handler marker missing')
    s = s.replace(old_handler, 'stop_all, capture_hotkey, cursor_position, pick_background, host_lobby, join_lobby, leave_lobby', 1)

p.write_text(s, encoding='utf-8', newline='\n')

# UI: native capture returns the exact Windows key name.
p = root / 'ui/app.js'
s = p.read_text(encoding='utf-8')
start = s.find('function normalizeKey(e) {')
end = s.find('\nfunction bindValue(', start)
if start >= 0 and end >= 0:
    block = r'''async function beginCapture(target) {
  if (capture) return;
  const button = $(hotkeyButtons[target]);
  capture = { target, button, old: button.textContent };
  button.textContent = 'PRESS KEY…';
  button.classList.add('capturing');
  try {
    const key = await invoke('capture_hotkey');
    if (!capture || capture.target !== target) return;
    finishCapture(key || null, !key);
  } catch (e) {
    if (capture && capture.target === target) finishCapture(null, true);
    toast(`Hotkey capture error: ${e}`);
  }
}
function setHotkey(target, key) {
  if (target === 'clicker1') settings.clicker1.hotkey = key;
  else if (target === 'clicker2') settings.clicker2.hotkey = key;
  else if (target === 'bolt_push') settings.bolt_push.hotkey = key;
  else if (target === 'bolts') settings.bolts.hotkey = key;
  else if (target === 'wallhop') settings.wallhop.hotkey = key;
}
function getHotkey(target) {
  if (target === 'clicker1') return settings.clicker1.hotkey;
  if (target === 'clicker2') return settings.clicker2.hotkey;
  if (target === 'bolt_push') return settings.bolt_push.hotkey;
  if (target === 'bolts') return settings.bolts.hotkey;
  return settings.wallhop.hotkey;
}
function finishCapture(key, cancel=false) {
  if (!capture) return;
  const { target, button, old } = capture;
  button.classList.remove('capturing');
  if (cancel || !key) button.textContent = old;
  else {
    setHotkey(target, key);
    button.textContent = `HOTKEY · ${key}`;
    saveSettings();
    toast(`${target.replace('_',' ').toUpperCase()} → ${key}`);
  }
  capture = null;
  renderDashboardMeta();
}

$$('.hotkey').forEach(b => b.addEventListener('click', () => beginCapture(b.dataset.hotkey)));
'''.strip()
    s = s[:start] + block + s[end:]
elif "invoke('capture_hotkey')" not in s:
    raise SystemExit('hotkey JS block markers missing')
p.write_text(s, encoding='utf-8', newline='\n')

# Startup window: same startup-overlay role as 5.22, exact requested text.
p = root / 'ui/index.html'
s = p.read_text(encoding='utf-8')
old = '''  <div id="intro" class="intro">\n    <div class="intro-orbit orbit-1"></div><div class="intro-orbit orbit-2"></div>\n    <div class="intro-mark">R</div>\n    <div class="intro-title">RIUCLICKER <b>PRO</b></div>\n    <div class="intro-sub">PRO 2.0 · STARTING</div>\n    <div class="intro-line"><i></i></div>\n  </div>'''
new = '''  <div id="intro" class="intro intro-522">\n    <div class="intro-orbit orbit-1"></div><div class="intro-orbit orbit-2"></div>\n    <div class="intro-522-window">\n      <div class="intro-522-kicker">RIUCLICKER PRO 2.0</div>\n      <div class="intro-title intro-522-title">xDragonsx on top</div>\n      <div class="intro-sub">STARTING</div>\n      <div class="intro-line"><i></i></div>\n    </div>\n  </div>'''
if old in s:
    s = s.replace(old, new, 1)
elif 'xDragonsx on top' not in s:
    raise SystemExit('intro HTML marker missing')
p.write_text(s, encoding='utf-8', newline='\n')

p = root / 'ui/styles.css'
s = p.read_text(encoding='utf-8')
css = '.intro-522-window{position:relative;z-index:2;min-width:430px;padding:34px 42px 30px;border-radius:24px;border:1px solid rgba(255,255,255,.11);background:linear-gradient(145deg,rgba(21,25,40,.94),rgba(11,13,24,.92));box-shadow:0 28px 90px rgba(0,0,0,.55),0 0 55px rgba(139,92,246,.14);backdrop-filter:blur(24px);text-align:center;animation:markIn .7s cubic-bezier(.2,.9,.2,1) forwards}.intro-522-kicker{font-size:9px;font-weight:900;letter-spacing:3px;color:#77839f}.intro-522-title{font-size:30px!important;letter-spacing:1px!important;font-weight:900!important;margin-top:15px!important;background:linear-gradient(90deg,#fff,#c9baff 48%,#82edf8);-webkit-background-clip:text;color:transparent}.intro-522-window .intro-sub{margin-top:10px}.intro-522-window .intro-line{margin-left:auto;margin-right:auto}'
if '.intro-522-window{' not in s:
    s = s.rstrip() + '\n' + css + '\n'
p.write_text(s, encoding='utf-8', newline='\n')

print('Applied native hotkey capture + xDragonsx 5.22-style intro')
