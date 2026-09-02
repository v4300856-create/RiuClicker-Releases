from pathlib import Path
p=Path("src/LobbyService.cs")
s=p.read_text(encoding="utf-8")
s=s.replace('owner_token=ownerToken,event=ev,','owner_token=ownerToken,@event=ev,')
p.write_text(s,encoding="utf-8")
print("lobby compile fix applied")
