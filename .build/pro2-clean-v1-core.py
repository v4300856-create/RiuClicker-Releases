from pathlib import Path
import json
import shutil

root = Path('pro2-rust')

def replace_once(text, old, new, label):
    if old not in text:
        raise SystemExit(f'{label} marker missing')
    return text.replace(old, new, 1)

# Use the prepared clean 1.0 UI as the base.
shutil.copyfile('.build/v1-ui-index.html', root / 'ui/index.html')
shutil.copyfile('.build/v1-ui-app.js', root / 'ui/app.js')
shutil.copyfile('.build/v1-ui-styles.css', root / 'ui/styles.css')

# Add Wallhop back to the clean UI, using the restored 5.22 native engine.
p = root / 'ui/index.html'
s = p.read_text(encoding='utf-8')
nav_marker = '<button class="nav" data-page="coordinates"><span>⌖</span><b data-i18n="nav_coords">Coordinates</b></button>'
s = replace_once(s, nav_marker, nav_marker + '\n        <button class="nav" data-page="wallhop"><span>↔</span><b data-i18n="nav_wallhop">Wallhop</b></button>', 'coordinates nav')
wallhop_html = '''      <section class="page" id="page-wallhop">
        <div class="section-head"><div><span class="eyebrow">5.22 CAMERA FLICK</span><h2 data-i18n="wallhop_title">Wallhop</h2></div><p data-i18n="wallhop_sub">Left and right work independently, with an exact camera return.</p></div>
        <div class="two-col">
          <article class="panel control-card">
            <div class="card-head"><div><span>WALLHOP</span><h3 data-i18n="direction">Direction</h3></div><button id="wallhop-hotkey" class="hotkey hotkey-btn" data-hotkey="wallhop">HOTKEY</button></div>
            <label><span data-i18n="direction">Direction</span><select id="wh-direction"><option value="left">LEFT</option><option value="right">RIGHT</option></select></label>
            <label><span data-i18n="pixels">Pixels</span><input id="wh-pixels" type="number" min="1" max="5000"></label>
            <label><span data-i18n="return_delay">Return delay · ms</span><input id="wh-return-delay" type="number" min="0" max="1000"></label>
            <label><span data-i18n="repeats">Repeats</span><input id="wh-repeats" type="number" min="1" max="100"></label>
            <label class="check-row"><span data-i18n="return_camera">Return camera</span><input id="wh-return" type="checkbox"></label>
            <button class="run-action primary wide" data-action="wallhop" data-i18n="test_wallhop">TEST WALLHOP</button>
          </article>
          <article class="panel helper wallhop-help">
            <b>5.22 MODE</b>
            <span data-i18n="wallhop_help">A second press is ignored while the flick is active. Windows receives one clean relative packet and one exact inverse packet.</span>
            <div class="sequence centered"><span>FLICK</span><i>›</i><span>RETURN</span></div>
          </article>
        </div>
      </section>\n\n'''
s = replace_once(s, '      <section class="page" id="page-lobby">', wallhop_html + '      <section class="page" id="page-lobby">', 'lobby section')
s = s.replace('<div id="update-status" class="status-note">GitHub release channel</div>', '<div id="update-status" class="status-note">Updater channel ready</div>')
p.write_text(s, encoding='utf-8', newline='\n')

# Clean UI logic + Wallhop settings.
p = root / 'ui/app.js'
s = p.read_text(encoding='utf-8')
s = replace_once(s, "const hotkeyButtons={clicker1:'#c1-hotkey',clicker2:'#c2-hotkey',bolt_push:'#bp-hotkey',bolts:'#bolts-hotkey'};", "const hotkeyButtons={clicker1:'#c1-hotkey',clicker2:'#c2-hotkey',bolt_push:'#bp-hotkey',bolts:'#bolts-hotkey',wallhop:'#wallhop-hotkey'};", 'hotkey buttons')
s = s.replace("nav_coords:'Координаты',nav_lobby:'Лобби'", "nav_coords:'Координаты',nav_wallhop:'Воллхоп',nav_lobby:'Лобби'", 1)
s = s.replace("nav_coords:'Coordinates',nav_lobby:'Lobby'", "nav_coords:'Coordinates',nav_wallhop:'Wallhop',nav_lobby:'Lobby'", 1)
s = s.replace("coords_title:'Координаты',", "coords_title:'Координаты',wallhop_title:'Воллхоп',wallhop_sub:'Левая и правая стороны работают отдельно, камера точно возвращается назад.',direction:'Сторона',pixels:'Пиксели',return_delay:'Задержка возврата · мс',repeats:'Повторы',return_camera:'Вернуть камеру',test_wallhop:'ТЕСТ ВОЛЛХОПА',wallhop_help:'Повторное нажатие игнорируется, пока рывок не закончился. Windows получает один точный рывок и один точный обратный рывок.',", 1)
s = s.replace("coords_title:'Coordinates',", "coords_title:'Coordinates',wallhop_title:'Wallhop',wallhop_sub:'Left and right work independently, with an exact camera return.',direction:'Direction',pixels:'Pixels',return_delay:'Return delay · ms',repeats:'Repeats',return_camera:'Return camera',test_wallhop:'TEST WALLHOP',wallhop_help:'A second press is ignored while the flick is active. Windows receives one clean relative packet and one exact inverse packet.',", 1)
s = replace_once(s, "coordinates:{ru:'Координаты',en:'Coordinates'},lobby:{ru:'Лобби',en:'Lobby'}", "coordinates:{ru:'Координаты',en:'Coordinates'},wallhop:{ru:'Воллхоп',en:'Wallhop'},lobby:{ru:'Лобби',en:'Lobby'}", 'page names')
old_bind = "refresh.push(bind('#bp-enabled',()=>settings.bolt_push.enabled,v=>settings.bolt_push.enabled=v,'checked',true));refresh.push(bind('#bolts-enabled',()=>settings.bolts.enabled,v=>settings.bolts.enabled=v,'checked',true));refresh.push(bind('#squad-name'"
new_bind = "refresh.push(bind('#bp-enabled',()=>settings.bolt_push.enabled,v=>settings.bolt_push.enabled=v,'checked',true));refresh.push(bind('#bolts-enabled',()=>settings.bolts.enabled,v=>settings.bolts.enabled=v,'checked',true));refresh.push(bind('#wh-direction',()=>settings.wallhop.direction,v=>settings.wallhop.direction=v,'value',true));refresh.push(bind('#wh-pixels',()=>settings.wallhop.pixels,v=>settings.wallhop.pixels=v,'number'));refresh.push(bind('#wh-return-delay',()=>settings.wallhop.return_delay_ms,v=>settings.wallhop.return_delay_ms=v,'number'));refresh.push(bind('#wh-repeats',()=>settings.wallhop.repeats,v=>settings.wallhop.repeats=v,'number'));refresh.push(bind('#wh-return',()=>settings.wallhop.return_camera,v=>settings.wallhop.return_camera=v,'checked',true));refresh.push(bind('#squad-name'"
s = replace_once(s, old_bind, new_bind, 'wallhop bindings')
p.write_text(s, encoding='utf-8', newline='\n')

p = root / 'ui/styles.css'
s = p.read_text(encoding='utf-8')
if '.wallhop-help{' not in s:
    s += '\n.wallhop-help{display:flex;flex-direction:column;justify-content:center;gap:18px;min-height:330px}.wallhop-help>b{font-size:12px;letter-spacing:2px}.wallhop-help>span{color:var(--muted);line-height:1.65}.wallhop-help .sequence{margin-top:8px}\n'
p.write_text(s, encoding='utf-8', newline='\n')

# Native backend.
p = root / 'src-tauri/src/main.rs'
s = p.read_text(encoding='utf-8')

# Start clean: no broken Pro2 settings are inherited.
s = s.replace('base.join("RiuClickerPro2").join("settings.json")', 'base.join("RiuClicker").join("settings.json")')

# Save language natively.
old_appearance = '''struct AppearanceSettings {
    background_path: String,
    panel_opacity: f32,
    intro_enabled: bool,
}'''
new_appearance = '''struct AppearanceSettings {
    background_path: String,
    panel_opacity: f32,
    intro_enabled: bool,
    language: String,
}'''
if 'language: String' not in s:
    s = replace_once(s, old_appearance, new_appearance, 'appearance struct')
s = s.replace('Self { background_path: String::new(), panel_opacity: 0.84, intro_enabled: true }', 'Self { background_path: String::new(), panel_opacity: 0.84, intro_enabled: true, language: "ru".into() }')
normal_marker = '    s.appearance.panel_opacity = s.appearance.panel_opacity.clamp(0.25, 1.0);'
if 's.appearance.language' not in s:
    s = replace_once(s, normal_marker, normal_marker + '\n    if s.appearance.language != "en" { s.appearance.language = "ru".into(); }', 'appearance normalize')

# Reliability-first macro timing. Even Instant now has real down/up time.
s = s.replace('"stable" => Self { key_hold: 24, modifier_hold: 55, step_gap: 24, mouse_gap: 30, pointer_settle: 35, final_safety: 18 },', '"stable" => Self { key_hold: 30, modifier_hold: 62, step_gap: 28, mouse_gap: 34, pointer_settle: 38, final_safety: 20 },')
s = s.replace('"turbo" => Self { key_hold: 5, modifier_hold: 11, step_gap: 3, mouse_gap: 4, pointer_settle: 6, final_safety: 9 },', '"turbo" => Self { key_hold: 10, modifier_hold: 18, step_gap: 6, mouse_gap: 8, pointer_settle: 8, final_safety: 12 },')
s = s.replace('"instant" => Self { key_hold: 4, modifier_hold: 8, step_gap: 4, mouse_gap: 3, pointer_settle: 4, final_safety: 10 },', '"instant" => Self { key_hold: 8, modifier_hold: 14, step_gap: 5, mouse_gap: 6, pointer_settle: 7, final_safety: 12 },')
s = s.replace('_ => Self { key_hold: 12, modifier_hold: 28, step_gap: 8, mouse_gap: 12, pointer_settle: 14, final_safety: 10 },', '_ => Self { key_hold: 16, modifier_hold: 34, step_gap: 10, mouse_gap: 14, pointer_settle: 16, final_safety: 12 },')

# Native F6 coordinate capture.
f6_cmd = r'''
#[tauri::command]
async fn capture_coordinate_f6(state: State<'_, AppState>) -> Result<(i32, i32), String> {
    let engine = Arc::clone(&state.engine);
    engine.injecting.store(true, Ordering::SeqCst);
    let joined = tauri::async_runtime::spawn_blocking(move || -> Result<(i32, i32), String> {
        let release_deadline = Instant::now() + Duration::from_secs(2);
        while key_is_down("F6") && Instant::now() < release_deadline {
            thread::sleep(Duration::from_millis(5));
        }
        let deadline = Instant::now() + Duration::from_secs(15);
        let mut was_down = false;
        while Instant::now() < deadline {
            let down = key_is_down("F6");
            if down && !was_down {
                let mut p = POINT { x: 0, y: 0 };
                let ok = unsafe { GetCursorPos(&mut p) };
                if ok == 0 { return Err("Could not read cursor position".into()); }
                while key_is_down("F6") && Instant::now() < deadline {
                    thread::sleep(Duration::from_millis(4));
                }
                return Ok((p.x, p.y));
            }
            was_down = down;
            thread::sleep(Duration::from_millis(4));
        }
        Err("F6 capture timed out".into())
    }).await;
    engine.injecting.store(false, Ordering::SeqCst);
    joined.map_err(|e| e.to_string())?
}
'''.strip()
if 'async fn capture_coordinate_f6' not in s:
    cursor_marker = '#[tauri::command]\nfn cursor_position() -> Result<(i32, i32), String> {'
    s = replace_once(s, cursor_marker, f6_cmd + '\n\n' + cursor_marker, 'cursor command')

handler_old = 'stop_all, capture_hotkey, cursor_position, pick_background, host_lobby, join_lobby, leave_lobby'
handler_new = 'stop_all, capture_hotkey, capture_coordinate_f6, cursor_position, pick_background, host_lobby, join_lobby, leave_lobby'
if handler_old in s:
    s = s.replace(handler_old, handler_new, 1)
elif handler_new not in s:
    raise SystemExit('invoke handler marker missing')

p.write_text(s, encoding='utf-8', newline='\n')

# Clean 1.0 identity.
p = root / 'src-tauri/Cargo.toml'
s = p.read_text(encoding='utf-8').replace('version = "2.0.0"', 'version = "1.0.0"', 1)
p.write_text(s, encoding='utf-8', newline='\n')

p = root / 'src-tauri/tauri.conf.json'
conf = json.loads(p.read_text(encoding='utf-8'))
conf['productName'] = 'RiuClicker'
conf['version'] = '1.0.0'
conf['identifier'] = 'com.riu.clicker'
win = conf['app']['windows'][0]
win['title'] = 'RiuClicker 1.0'
win['width'] = 1240
win['height'] = 800
win['minWidth'] = 1020
win['minHeight'] = 680
p.write_text(json.dumps(conf, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

print('Applied clean RiuClicker 1.0 core rebuild')
