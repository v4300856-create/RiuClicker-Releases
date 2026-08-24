from pathlib import Path
import re

root = Path('pro2-rust')

# Rust engine: restore the deterministic 5.22 wallhop behavior.
p = root / 'src-tauri/src/main.rs'
s = p.read_text(encoding='utf-8')

# Use MOVE_NOCOALESCE just like the old SendInput wallhop path so Windows does
# not merge short relative camera packets.
if 'MOUSEEVENTF_MOVE_NOCOALESCE' not in s:
    s = s.replace(
        'MOUSEEVENTF_MOVE, MOUSEEVENTF_RIGHTDOWN, MOUSEEVENTF_RIGHTUP,',
        'MOUSEEVENTF_MOVE, MOUSEEVENTF_MOVE_NOCOALESCE, MOUSEEVENTF_RIGHTDOWN, MOUSEEVENTF_RIGHTUP,',
        1,
    )

start = s.find('    fn run_wallhop(self: &Arc<Self>) {')
end = s.find('\n    fn move_mouse_relative(&self, dx: i32, dy: i32) {', start)
if start < 0 or end < 0:
    raise SystemExit('run_wallhop block not found')

new_wallhop = r'''    fn run_wallhop(self: &Arc<Self>) {
        // 5.22 behavior: ignore another trigger while a flick is already active.
        // Queuing another same-direction flick made the Rust build feel like it
        // only kept turning one way when the hotkey was pressed quickly.
        if self.wallhop_running.swap(true, Ordering::SeqCst) {
            return;
        }
        self.wallhop_queued.store(false, Ordering::SeqCst);

        // Snapshot settings once. Editing the UI during the flick must not change
        // the direction or return vector halfway through the operation.
        let cfg = self.settings.read().wallhop.clone();
        let engine = Arc::clone(self);
        thread::spawn(move || {
            let epoch = engine.stop_all_epoch.load(Ordering::Relaxed);
            let direction = if cfg.direction.eq_ignore_ascii_case("left") { -1 } else { 1 };
            let pixels = cfg.pixels.clamp(1, 5000);
            let vertical = cfg.vertical.clamp(-3000, 3000);
            let repeats = cfg.repeats.clamp(1, 100);
            let return_delay = cfg.return_delay_ms.min(1000);
            let repeat_gap = cfg.repeat_gap_ms.min(5000);
            let mut outstanding_x = 0i32;
            let mut outstanding_y = 0i32;

            engine.message(format!("Wallhop {}", if direction < 0 { "LEFT" } else { "RIGHT" }));

            for rep in 0..repeats {
                if engine.stop_all_epoch.load(Ordering::Relaxed) != epoch { break; }

                let dx = direction * pixels;
                let dy = vertical;
                engine.move_mouse_relative(dx, dy);
                outstanding_x += dx;
                outstanding_y += dy;

                if cfg.return_camera {
                    if return_delay > 0 {
                        let until = Instant::now() + Duration::from_millis(return_delay);
                        while Instant::now() < until {
                            if engine.stop_all_epoch.load(Ordering::Relaxed) != epoch { break; }
                            thread::sleep(Duration::from_millis(1));
                        }
                    }
                    // Exact inverse packet, same as the old 5.22 implementation.
                    if outstanding_x != 0 || outstanding_y != 0 {
                        engine.move_mouse_relative(-outstanding_x, -outstanding_y);
                        outstanding_x = 0;
                        outstanding_y = 0;
                    }
                }

                if rep + 1 < repeats && repeat_gap > 0 {
                    let until = Instant::now() + Duration::from_millis(repeat_gap);
                    while Instant::now() < until {
                        if engine.stop_all_epoch.load(Ordering::Relaxed) != epoch { break; }
                        thread::sleep(Duration::from_millis(1));
                    }
                }
            }

            // Cancellation/F12 safety: never leave the camera displaced.
            if cfg.return_camera && (outstanding_x != 0 || outstanding_y != 0) {
                engine.move_mouse_relative(-outstanding_x, -outstanding_y);
            }
            engine.wallhop_queued.store(false, Ordering::SeqCst);
            engine.wallhop_running.store(false, Ordering::SeqCst);
            engine.message("Wallhop ready");
        });
    }
'''
s = s[:start] + new_wallhop + s[end:]

old_move = '''    fn move_mouse_relative(&self, dx: i32, dy: i32) {
        if dx == 0 && dy == 0 { return; }
        self.injecting.store(true, Ordering::SeqCst);
        unsafe { mouse_event(MOUSEEVENTF_MOVE, dx, dy, 0, 0); }
        self.injecting.store(false, Ordering::SeqCst);
    }'''
new_move = '''    fn move_mouse_relative(&self, dx: i32, dy: i32) {
        if dx == 0 && dy == 0 { return; }
        self.injecting.store(true, Ordering::SeqCst);
        unsafe { mouse_event(MOUSEEVENTF_MOVE | MOUSEEVENTF_MOVE_NOCOALESCE, dx, dy, 0, 0); }
        self.injecting.store(false, Ordering::SeqCst);
    }'''
if old_move not in s:
    raise SystemExit('move_mouse_relative block not found')
s = s.replace(old_move, new_move, 1)

p.write_text(s, encoding='utf-8', newline='\n')

# UI: changing Left/Right must reach the native engine immediately, not after
# the generic debounce. This fixes pressing TEST/hotkey immediately after the switch.
p = root / 'ui/app.js'
s = p.read_text(encoding='utf-8')
old = "refreshers.push(bindValue('#wh-direction',()=>settings.wallhop.direction,v=>settings.wallhop.direction=v));"
new = "refreshers.push(bindValue('#wh-direction',()=>settings.wallhop.direction,v=>settings.wallhop.direction=v,'value',true));"
if old in s:
    s = s.replace(old, new, 1)
elif new not in s:
    raise SystemExit('wallhop direction binding not found')
p.write_text(s, encoding='utf-8', newline='\n')

print('Applied 5.22-style bidirectional wallhop hotfix')
