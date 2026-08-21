local Players = game:GetService("Players")
local UserInputService = game:GetService("UserInputService")
TweenService = game:GetService("TweenService")
local TeleportService = game:GetService("TeleportService")
local TextService = game:GetService("TextService")
local plr = Players.LocalPlayer
function isTouchMobileDevice()
    return UserInputService.TouchEnabled and not UserInputService.KeyboardEnabled
end
Settings = Settings
Window = Window
local ReplicatedStorage = game:GetService("ReplicatedStorage")

-- Persistent executor env (prefer getgenv over _G for reinject / cross-chunk state).
function getAsterEnv()
    if type(getgenv) == "function" then
        local ok, env = pcall(getgenv)
        if ok and type(env) == "table" then
            return env
        end
    end
    error("[ASTER] getgenv() is required")
end

-- Idempotency helpers: when this script is executed multiple times, disconnect
-- previously-created global connections before creating new ones.
local __ASTER_RUNTIME = getAsterEnv().__ASTER_RUNTIME
if type(__ASTER_RUNTIME) ~= "table" then
    __ASTER_RUNTIME = { connections = {} }
    getAsterEnv().__ASTER_RUNTIME = __ASTER_RUNTIME
elseif type(__ASTER_RUNTIME.connections) ~= "table" then
    __ASTER_RUNTIME.connections = {}
end
-- Bump session on each execution so stale background loops exit after reinject.
__ASTER_RUNTIME.sessionId = (__ASTER_RUNTIME.sessionId or 0) + 1
local CURRENT_SESSION = __ASTER_RUNTIME.sessionId
__ASTER_RUNTIME.tribeCacheLoopStarted = false
__ASTER_RUNTIME.autoDropLoopStarted = false
__ASTER_RUNTIME.waypointDropdownLoopStarted = false
__ASTER_RUNTIME.combatTargetLoopStarted = false
__ASTER_RUNTIME.targetHighlightLoopStarted = false
__ASTER_RUNTIME.pathFinderRefreshStarted = false
__ASTER_RUNTIME.silentAimEngineReady = false
__ASTER_RUNTIME.autoShootLoopStarted = false
__ASTER_RUNTIME.packetIdAutoSyncStarted = false
-- Kill previous master loops immediately. Stale RenderStepped/Heartbeat callbacks
-- from a prior inject can outlive the old chunk and index a nil runtime upvalue.
do
    local conns = __ASTER_RUNTIME.connections
    if type(conns) == "table" then
        for _, key in ipairs({ "masterFrame", "masterHeartbeat" }) do
            local old = conns[key]
            if old then
                pcall(function()
                    if old.Disconnect then old:Disconnect() end
                end)
                conns[key] = nil
            end
        end
    end
end
__ASTER_RUNTIME.masterFrameStarted = false
__ASTER_RUNTIME.masterHeartbeatStarted = false
__ASTER_RUNTIME.frameUpdates = {}
__ASTER_RUNTIME.heartbeatUpdates = {}
__ASTER_RUNTIME.unifiedAuraActive = false
__ASTER_RUNTIME.webhookStats = __ASTER_RUNTIME.webhookStats or {
    planted = 0,
    harvested = 0,
    broken = {},
}
__ASTER_RUNTIME.webhookResourceEids = __ASTER_RUNTIME.webhookResourceEids or {}
__ASTER_RUNTIME.recordGrindGain = __ASTER_RUNTIME.recordGrindGain or function() end
__ASTER_RUNTIME.recordGrindLoss = __ASTER_RUNTIME.recordGrindLoss or function() end
__ASTER_RUNTIME.recordChestTeleport = __ASTER_RUNTIME.recordChestTeleport or function() end


-- Canonical world folders (Booga workspace layout).
function getWorkspaceResources()
    local f = workspace:FindFirstChild("Resources")
    if f then return f end
    return nil
end
function getWorkspaceDeployables()
    local f = workspace:FindFirstChild("Deployables")
    if f then return f end
    return nil
end
function getWorkspaceCritters()
    local cached = __ASTER_RUNTIME.crittersFolder
    if cached and cached.Parent then
        return cached
    end
    local f = workspace:FindFirstChild("Critters")
    if not f then
        f = workspace:WaitForChild("Critters", 2)
    end
    if f then
        __ASTER_RUNTIME.crittersFolder = f
    end
    return f
end

function isWorkspaceCritterInstance(inst)
    return inst and (inst:IsA("Model") or inst:IsA("BasePart"))
end

function getWorkspaceCritterModel(inst)
    if not inst then return nil end
    if inst:IsA("Model") then return inst end
    if inst:IsA("BasePart") then
        local parent = inst.Parent
        if parent and parent:IsA("Model") then return parent end
    end
    return nil
end

function getWorkspaceCritterName(inst)
    local model = getWorkspaceCritterModel(inst)
    if model then return model.Name end
    return inst and inst.Name or ""
end

function getWorkspaceCritterPart(inst)
    if not inst then return nil end
    if inst:IsA("BasePart") then return inst end
    if inst:IsA("Model") then
        return inst.PrimaryPart
            or inst:FindFirstChild("HumanoidRootPart")
            or inst:FindFirstChild("Head")
            or inst:FindFirstChildWhichIsA("BasePart", true)
    end
    return nil
end

function isWorkspaceCritterAlive(inst)
    if not inst or not inst.Parent then return false end
    local folder = getWorkspaceCritters()
    if folder and not inst:IsDescendantOf(folder) then return false end
    local model = getWorkspaceCritterModel(inst) or (inst:IsA("Model") and inst or nil)
    if model then
        local hum = model:FindFirstChildOfClass("Humanoid")
        if hum and hum.Health <= 0 then return false end
    end
    local part = getWorkspaceCritterPart(inst)
    if not part or not part.Parent then return false end
    if part.Size.Magnitude < 0.01 then return false end
    return true
end

function critterNameMatchesFilter(modelName, filterText, allToken)
    if not modelName then return false end
    filterText = tostring(filterText or allToken or "")
    local f = string.lower(string.gsub(filterText, "^%s+", ""))
    f = string.gsub(f, "%s+$", "")
    if f == "" or f == "all" then return true end
    local token = string.lower(tostring(allToken or ""))
    if token ~= "" and f == token then return true end
    if string.sub(f, 1, 3) == "all" then return true end
    local nameLower = string.lower(modelName)
    if nameLower == f then return true end
    if string.find(nameLower, f, 1, true) then return true end
    return false
end

function forEachWorkspaceCritter(folder, fn)
    if not folder or type(fn) ~= "function" then return end
    local function walk(node)
        for _, child in ipairs(node:GetChildren()) do
            if isWorkspaceCritterInstance(child) then
                fn(child)
            elseif child:IsA("Folder") then
                walk(child)
            end
        end
    end
    walk(folder)
end

function collectWorkspaceCritters(folder)
    folder = folder or getWorkspaceCritters()
    local out = {}
    if not folder then return out end
    forEachWorkspaceCritter(folder, function(critter)
        table.insert(out, critter)
    end)
    return out
end

function getWorkspaceCritterNameList(opts)
    opts = opts or {}
    local names = {}
    local seen = {}
    if opts.includeAll ~= false then
        table.insert(names, "All")
        seen.All = true
    end
    local folder = getWorkspaceCritters()
    if folder then
        forEachWorkspaceCritter(folder, function(critter)
            local n = getWorkspaceCritterName(critter)
            if n and n ~= "" and not seen[n] then
                seen[n] = true
                table.insert(names, n)
            end
        end)
        for _, child in ipairs(folder:GetChildren()) do
            if child:IsA("Folder") then
                local n = child.Name
                if n and n ~= "" and not seen[n] then
                    seen[n] = true
                    table.insert(names, n)
                end
            end
        end
    end
    table.sort(names, function(a, b)
        if a == "All" then return true end
        if b == "All" then return false end
        return a < b
    end)
    return names
end

function getWorkspaceCrops()
    local f = workspace:FindFirstChild("Crops")
    if f then return f end
    return nil
end


function isRuntimeSessionActive(session)
    local rt = getAsterEnv().__ASTER_RUNTIME
    if type(rt) ~= "table" then return false end
    return session == rt.sessionId
end

function trackConnection(key, conn)
    local rt = getAsterEnv().__ASTER_RUNTIME
    if type(rt) ~= "table" then
        return conn
    end
    if type(rt.connections) ~= "table" then
        rt.connections = {}
    end
    local old = rt.connections[key]
    if old and old.Disconnect then
        pcall(function() old:Disconnect() end)
    end
    rt.connections[key] = conn
    return conn
end

if not (getAsterEnv().__ASTER_RUNTIME and getAsterEnv().__ASTER_RUNTIME.crittersFolderWatcher) then
    local rt = getAsterEnv().__ASTER_RUNTIME
    if type(rt) == "table" then
        rt.crittersFolderWatcher = true
        trackConnection("crittersFolder_ChildAdded", workspace.ChildAdded:Connect(function(child)
            local runtime = getAsterEnv().__ASTER_RUNTIME
            if child.Name == "Critters" and type(runtime) == "table" then
                runtime.crittersFolder = child
            end
        end))
    end
end

function registerFrameUpdate(key, fn)
    local rt = getAsterEnv().__ASTER_RUNTIME
    if type(rt) ~= "table" then return end
    if type(rt.frameUpdates) ~= "table" then rt.frameUpdates = {} end
    rt.frameUpdates[key] = fn
end

function unregisterFrameUpdate(key)
    local rt = getAsterEnv().__ASTER_RUNTIME
    if type(rt) ~= "table" or type(rt.frameUpdates) ~= "table" then return end
    rt.frameUpdates[key] = nil
end

function registerHeartbeatUpdate(key, fn)
    local rt = getAsterEnv().__ASTER_RUNTIME
    if type(rt) ~= "table" then return end
    if type(rt.heartbeatUpdates) ~= "table" then rt.heartbeatUpdates = {} end
    rt.heartbeatUpdates[key] = fn
end

function unregisterHeartbeatUpdate(key)
    local rt = getAsterEnv().__ASTER_RUNTIME
    if type(rt) ~= "table" or type(rt.heartbeatUpdates) ~= "table" then return end
    rt.heartbeatUpdates[key] = nil
end

function ensureMasterFrameLoop()
    local rt = getAsterEnv().__ASTER_RUNTIME
    if type(rt) ~= "table" then return end
    if type(rt.frameUpdates) ~= "table" then rt.frameUpdates = {} end
    if rt.masterFrameStarted then return end
    rt.masterFrameStarted = true
    local RunService = game:GetService("RunService")
    trackConnection("masterFrame", RunService.RenderStepped:Connect(function(dt)
        local runtime = getAsterEnv().__ASTER_RUNTIME
        local updates = runtime and runtime.frameUpdates
        if type(updates) ~= "table" then return end
        for _, fn in pairs(updates) do
            if fn then
                pcall(fn, dt)
            end
        end
    end))
end

function ensureMasterHeartbeatLoop()
    local rt = getAsterEnv().__ASTER_RUNTIME
    if type(rt) ~= "table" then return end
    if type(rt.heartbeatUpdates) ~= "table" then rt.heartbeatUpdates = {} end
    if rt.masterHeartbeatStarted then return end
    rt.masterHeartbeatStarted = true
    local RunService = game:GetService("RunService")
    trackConnection("masterHeartbeat", RunService.Heartbeat:Connect(function(dt)
        local runtime = getAsterEnv().__ASTER_RUNTIME
        local updates = runtime and runtime.heartbeatUpdates
        if type(updates) ~= "table" then return end
        for _, fn in pairs(updates) do
            if fn then
                pcall(fn, dt)
            end
        end
    end))
end

-- Allow multiple instances: re-running creates a new UI.

local ByteNetReliable = ReplicatedStorage:FindFirstChild("ByteNetReliable")
if not ByteNetReliable then
    ByteNetReliable = ReplicatedStorage:WaitForChild("ByteNetReliable", 2)
end
if not ByteNetReliable then
    for _, v in ipairs(ReplicatedStorage:GetDescendants()) do
        if v.Name == "ByteNetReliable" and v:IsA("RemoteEvent") then
            ByteNetReliable = v
            break
        end
    end
end
if not ByteNetReliable then
    task.spawn(function()
        local deadline = tick() + 20
        while not ByteNetReliable and tick() < deadline do
            local found = ReplicatedStorage:FindFirstChild("ByteNetReliable")
            if found then
                ByteNetReliable = found
                break
            end
            task.wait(0.1)
        end
        if ByteNetReliable then return end
        for _, v in ipairs(ReplicatedStorage:GetDescendants()) do
            if v.Name == "ByteNetReliable" and v:IsA("RemoteEvent") then
                ByteNetReliable = v
                break
            end
        end
    end)
end

function autoDiscoverItemID(itemName)
    if not itemName or itemName == "" then return nil end

    -- 1) Fast path: use existing cache if present
    if type(craftNameToID) == "table" then
        local cached = craftNameToID[itemName]
        if cached ~= nil then return cached end
    end

    -- 2) Module lookup (if available in this game)
    do
        local Modules = ReplicatedStorage:FindFirstChild("Modules")
        if Modules then
            local ItemIDS = Modules:FindFirstChild("ItemIDS")
            if ItemIDS and ItemIDS:FindFirstChild(itemName) then
                local v = ItemIDS[itemName].Value
                if type(craftNameToID) == "table" then craftNameToID[itemName] = v end
                if type(craftItemIDs) == "table" then craftItemIDs[v] = itemName end
                return v
            end
        end
    end

    -- 3) UI scan fallback (only if helper functions exist later in the script)
    local inventoryScan = (type(scanInventoryForItemID) == "function") and scanInventoryForItemID or nil
    local craftScan = (type(scanCraftMenuForItemID) == "function") and scanCraftMenuForItemID or nil

    if inventoryScan then
        local inventoryID = inventoryScan(itemName)
        if inventoryID then
            if type(craftNameToID) == "table" then craftNameToID[itemName] = inventoryID end
            if type(craftItemIDs) == "table" then craftItemIDs[inventoryID] = itemName end
            return inventoryID
        end
    end

    if craftScan then
        local craftMenuID = craftScan(itemName)
        if craftMenuID then
            if type(craftNameToID) == "table" then craftNameToID[itemName] = craftMenuID end
            if type(craftItemIDs) == "table" then craftItemIDs[craftMenuID] = itemName end
            return craftMenuID
        end
    end

    return nil
end

-- Packet IDs: live Modules.Packets lookup + hidden obfuscated disk cache.
-- No static fallback table — IDs are discovered in-game and persisted on change.
PACKET_IDS = {}

_packetDataStatic = { packets = PACKET_IDS }

function packetData()
    return _packetDataStatic
end

function getPacketId(packetName)
    if not packetName or packetName == "" then return nil end
    local ids = PACKET_IDS or (_packetDataStatic and _packetDataStatic.packets)
    return ids and ids[packetName] or nil
end

function resolvePacketId(...)
    for i = 1, select("#", ...) do
        local id = getPacketId(select(i, ...))
        if id then return id end
    end
    return nil
end

function getPlaceStructureId()
    return getPacketId("PlaceStructure")
end

-- Convenience: send a no-payload C→S packet by name.
function firePacket(packetName)
    if not ByteNetReliable then return false end
    local id = getPacketId(packetName)
    if not id then return false end
    local b = buffer.create(2)
    buffer.writeu8(b, 0, 0)
    buffer.writeu8(b, 1, id)
    ByteNetReliable:FireServer(b)
    return true
end

-- Live Packets lookup → obscured disk cache → auto-rewrite when any ID differs.
-- Priority: live game modules > obfuscated cache file
-- Note: Wave workspace often ignores/blocks leading-dot folders, so avoid ".folder" paths.
local PACKET_IDS_CACHE_PATH = "ASTER/sys/c7/f2a91b.dat"
local PACKET_IDS_CACHE_LEGACY_PATH = "ASTER/Booga/packet_ids.json"
local PACKET_IDS_CACHE_OBFUSCATE_KEY = "A$t3rPk7_v2"
local PACKET_IDS_CACHE_META = {
    lastSync = 0,
    lastSave = 0,
    source = "none",
    changedCount = 0,
}

local function ensurePacketCacheFolder()
    if type(makefolder) ~= "function" then return end
    pcall(function()
        if type(isfolder) == "function" then
            if not isfolder("ASTER") then makefolder("ASTER") end
            if not isfolder("ASTER/sys") then makefolder("ASTER/sys") end
            if not isfolder("ASTER/sys/c7") then makefolder("ASTER/sys/c7") end
        else
            makefolder("ASTER")
            makefolder("ASTER/sys")
            makefolder("ASTER/sys/c7")
        end
    end)
end

local function getPacketHttp()
    return game:GetService("HttpService")
end

local function xorObfuscateString(text, key)
    if type(text) ~= "string" or text == "" then return "" end
    key = key or PACKET_IDS_CACHE_OBFUSCATE_KEY
    local keyLen = #key
    if keyLen < 1 then return text end
    local out = table.create(#text)
    for i = 1, #text do
        out[i] = string.char(bit32.bxor(string.byte(text, i), string.byte(key, ((i - 1) % keyLen) + 1)))
    end
    return table.concat(out)
end

local function encodePacketCacheBlob(jsonText)
    local http = getPacketHttp()
    local xored = xorObfuscateString(jsonText, PACKET_IDS_CACHE_OBFUSCATE_KEY)
    local ok, b64 = pcall(function()
        return http:Base64Encode(xored)
    end)
    if ok and type(b64) == "string" then
        return "AX1:" .. b64
    end
    -- Fallback if Base64Encode is unavailable: still XOR, mark format.
    return "AX0:" .. xored
end

local function decodePacketCacheBlob(raw)
    if type(raw) ~= "string" or raw == "" then return nil end
    local http = getPacketHttp()

    -- New obfuscated formats
    if string.sub(raw, 1, 4) == "AX1:" then
        local b64 = string.sub(raw, 5)
        local ok, decoded = pcall(function()
            return http:Base64Decode(b64)
        end)
        if not ok or type(decoded) ~= "string" then return nil end
        return xorObfuscateString(decoded, PACKET_IDS_CACHE_OBFUSCATE_KEY)
    end
    if string.sub(raw, 1, 4) == "AX0:" then
        return xorObfuscateString(string.sub(raw, 5), PACKET_IDS_CACHE_OBFUSCATE_KEY)
    end

    -- Legacy plain JSON
    if string.sub(raw, 1, 1) == "{" then
        return raw
    end
    return nil
end

local function tryHidePacketCacheFile(path)
    -- Best-effort OS hide. Most executors cannot truly lock workspace files.
    pcall(function()
        if type(sethiddenfile) == "function" then
            sethiddenfile(path, true)
            return
        end
        if type(isfilehidden) == "function" and type(sethidden) == "function" then
            sethidden(path, true)
            return
        end
    end)
end

local function deleteLegacyPacketCache()
    if type(delfile) ~= "function" or type(isfile) ~= "function" then return end
    pcall(function()
        if isfile(PACKET_IDS_CACHE_LEGACY_PATH) then
            delfile(PACKET_IDS_CACHE_LEGACY_PATH)
        end
    end)
end

local function shallowCopyPacketMap(src)
    local out = {}
    if type(src) ~= "table" then return out end
    for k, v in pairs(src) do
        if type(k) == "string" and type(v) == "number" and v == v and v > 0 then
            out[k] = v
        end
    end
    return out
end

local function packetMapsEqual(a, b)
    if type(a) ~= "table" or type(b) ~= "table" then return false end
    for k, v in pairs(a) do
        if b[k] ~= v then return false end
    end
    for k, v in pairs(b) do
        if a[k] ~= v then return false end
    end
    return true
end

local function diffPacketMaps(oldMap, newMap)
    local changes = {}
    oldMap = oldMap or 