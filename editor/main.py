import json
import math
from pathlib import Path
import pygame
pygame.init()
SCREEN = pygame.display.set_mode((1100, 750), pygame.RESIZABLE)
pygame.display.set_caption("SoulSide - World Editor")
clock = pygame.time.Clock()
font = pygame.font.SysFont("consolas", 17)
small_font = pygame.font.SysFont("consolas", 14)
ROOT = Path(__file__).resolve().parent.parent
ROOM_DIR = ROOT / "world" / "rooms"
CONNECTIONS_PATH = ROOT / "world" / "connections.json"
ROOM_DIR.mkdir(parents=True, exist_ok=True)
BG = (24, 24, 31)
GRID_COLOR = (48, 48, 58)
ROOM_COLOR = (220, 220, 230)
TRIANGLE_COLOR = (90, 90, 110)
PREVIEW_COLOR = (170, 140, 220)
ENTRANCE_COLOR = (235, 65, 65)
TEXT_COLOR = (240, 240, 245)
SELECT_COLOR = (255, 205, 90)
SCALE = 50
GRID = 0.5
origin = pygame.Vector2(100, 650)
MAP_SCALE = 18
MAP_GRID = 1.0
MAP_MAJOR_GRID = 10.0
map_origin = pygame.Vector2(550, 480)
room_data = {}
room_position = (0, 0)
room_width = 10.0
room_height = 10.0
tools = ["Rechteck", "Dreieck", "Eingang", "Löschen", "Raumecken"]
tool_index = 0
drag_start = None
drag_current = None
running = True
message = "Bereit"
world_map_mode = False
room_input_mode = False
room_input_text = ""
map_drag = None
entrance_drag = None
selected_map_room = None
connection_source_room = None
selected_connection = None
connections = []
selected_border_vertex = None
border_drag = None
delete_room_armed = False
def room_path(position):
    x, y = position
    return ROOM_DIR / f"{int(x)}_{int(y)}.json"
def as_position(value):
    return (int(round(float(value[0]))), int(round(float(value[1]))))
def load_connections():
    global connections
    if not CONNECTIONS_PATH.exists():
        connections = []
        return
    try:
        with CONNECTIONS_PATH.open("r", encoding="utf-8") as f:
            data = json.load(f)
        connections = data if isinstance(data, list) else []
    except (OSError, json.JSONDecodeError) as exc:
        connections = []
        print(f"connections.json konnte nicht gelesen werden: {exc}")
def save_connections():
    CONNECTIONS_PATH.parent.mkdir(parents=True, exist_ok=True)
    temp = CONNECTIONS_PATH.with_suffix(".json.tmp")
    with temp.open("w", encoding="utf-8") as f:
        json.dump(connections, f, indent=4)
    temp.replace(CONNECTIONS_PATH)
def load_room(position):
    global room_data, room_position, room_width, room_height, message
    position = as_position(position)
    path = room_path(position)
    if path.exists():
        try:
            with path.open("r", encoding="utf-8") as f:
                room_data = json.load(f)
            room_data.setdefault("position", list(position))
            room_data.setdefault("images", [])
            room_data.setdefault("gravity", 1)
            room_data.setdefault("collision", [])
            room_data.setdefault("boarders", [[0, 0], [10, 0], [10, 10], [0, 10]])
            room_data.setdefault("editor_entrances", [])
            message = f"Geladen: {path.name}"
        except (OSError, json.JSONDecodeError) as exc:
            message = f"Raum konnte nicht geladen werden: {exc}"
            return False
    else:
        room_data = {
            "position": list(position), "images": [], "gravity": 1,
            "collision": [], "boarders": [[0, 0], [10, 0], [10, 10], [0, 10]],
            "editor_entrances": [],
        }
        message = f"Neuer Raum: {position} (mit S speichern)"
    room_position = as_position(room_data.get("position", position))
    room_data["position"] = list(room_position)
    borders = room_data.get("boarders", [])
    if len(borders) >= 3:
        room_width = max(float(p[0]) for p in borders) - min(float(p[0]) for p in borders)
        room_height = max(float(p[1]) for p in borders) - min(float(p[1]) for p in borders)
    else:
        room_width = room_height = 10.0
    return True
def save_room():
    global message
    room_data["position"] = list(room_position)
    path = room_path(room_position)
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(".json.tmp")
    with temp.open("w", encoding="utf-8") as f:
        json.dump(room_data, f, indent=4)
    temp.replace(path)
    message = f"Gespeichert: {path.name}"
def all_room_files():
    result = []
    for path in ROOM_DIR.glob("*.json"):
        if path.name == "connections.json":
            continue
        try:
            with path.open("r", encoding="utf-8") as f:
                data = json.load(f)
            pos = as_position(data.get("position", path.stem.split("_", 1)))
            borders = data.get("boarders", [[0, 0], [10, 0], [10, 10], [0, 10]])
            if not borders:
                borders = [[0, 0], [10, 0], [10, 10], [0, 10]]
            result.append({"path": path, "position": pos, "data": data, "borders": borders})
        except (OSError, ValueError, TypeError, json.JSONDecodeError):
            continue
    return result
def move_room(old_position, new_position):
    global room_position, room_data, message, selected_map_room
    old_position, new_position = as_position(old_position), as_position(new_position)
    old_path, new_path = room_path(old_position), room_path(new_position)
    if old_position == new_position:
        return True
    if new_path.exists():
        message = f"Verschieben abgebrochen: {new_path.name} existiert bereits"
        return False
    if not old_path.exists():
        message = f"Quelldatei fehlt: {old_path.name}"
        return False
    try:
        with old_path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        data["position"] = list(new_position)
        temp = new_path.with_suffix(".json.tmp")
        with temp.open("w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)
        # Update room references in all connections; entrance coordinates are local and stay unchanged.
        changed = False
        for connection in connections:
            for key in ("room_a", "room_b"):
                if key in connection and as_position(connection[key]) == old_position:
                    connection[key] = list(new_position)
                    changed = True
        temp.replace(new_path)
        old_path.unlink()
        if changed:
            save_connections()
        if room_position == old_position:
            load_room(new_position)
        selected_map_room = new_position
        message = f"Raum verschoben: {old_position} → {new_position}"
        return True
    except (OSError, ValueError, TypeError, json.JSONDecodeError) as exc:
        message = f"Verschieben fehlgeschlagen: {exc}"
        return False
def resize_room(direction):
    global room_width, room_height, message
    borders = room_data.get("boarders", [])
    if not borders:
        return
    left, right = min(p[0] for p in borders), max(p[0] for p in borders)
    bottom, top = min(p[1] for p in borders), max(p[1] for p in borders)
    step = 1.0
    shrinking = bool(pygame.key.get_mods() & pygame.KMOD_SHIFT)
    if direction == "up": top += -step if shrinking else step
    elif direction == "down": bottom += step if shrinking else -step
    elif direction == "left": left += step if shrinking else -step
    elif direction == "right": right += -step if shrinking else step
    elif direction == "width+": right += step
    elif direction == "width-": right -= step
    elif direction == "height+": top += step
    elif direction == "height-": top -= step
    if right - left < GRID or top - bottom < GRID:
        message = "Mindestgröße erreicht"
        return
    room_data["boarders"] = [[left, bottom], [right, bottom], [right, top], [left, top]]
    room_width, room_height = right-left, top-bottom
    # Größenänderungen sofort speichern. Der Dateiname bleibt x_y.json,
    # da er die Weltposition und nicht die Abmessungen kodiert.
    save_room()
    message = f"Raumgröße gespeichert: {room_width:g} x {room_height:g}"
def world_to_screen(point):
    return round(origin.x + point[0] * SCALE), round(origin.y - point[1] * SCALE)
def screen_to_world(point):
    return (point[0] - origin.x) / SCALE, (origin.y - point[1]) / SCALE
def snap(value, step=None):
    step = GRID if step is None else step
    return round(value / step) * step
def snapped_point(point):
    x, y = screen_to_world(point)
    return snap(x), snap(y)
def triangle_points(triangle):
    return [triangle["a"], triangle["b"], triangle["c"]]
def add_triangle(a, b, c):
    area = abs((b[0]-a[0])*(c[1]-a[1]) - (b[1]-a[1])*(c[0]-a[0]))
    if area < 1e-8:
        return
    room_data.setdefault("collision", []).append({"a": list(a), "b": list(b), "c": list(c)})
def add_rectangle(start, end):
    x1, y1 = start; x2, y2 = end
    left, right = sorted((x1, x2)); bottom, top = sorted((y1, y2))
    if right <= left or top <= bottom:
        return
    add_triangle((left,bottom), (left,top), (right,bottom))
    add_triangle((left,top), (right,top), (right,bottom))
def add_right_triangle(start, end):
    x1, y1 = start; x2, y2 = end
    left, right = sorted((x1, x2)); bottom, top = sorted((y1, y2))
    add_triangle((left,bottom), (left,top), (right,bottom))
def point_in_triangle(point, triangle):
    px, py = point; a, b, c = triangle_points(triangle)
    def sign(p1, p2, p3):
        return (p1[0]-p3[0])*(p2[1]-p3[1]) - (p2[0]-p3[0])*(p1[1]-p3[1])
    d1, d2, d3 = sign((px,py),a,b), sign((px,py),b,c), sign((px,py),c,a)
    return not ((d1 < 0 or d2 < 0 or d3 < 0) and (d1 > 0 or d2 > 0 or d3 > 0))
def erase_at(mouse_position):
    point = screen_to_world(mouse_position)
    for i in range(len(room_data.get("collision", []))-1, -1, -1):
        if point_in_triangle(point, room_data["collision"][i]):
            del room_data["collision"][i]
            return True
    return False
def border_vertex_hit_test(mouse_position, radius=12):
    """Gibt den Index einer angeklickten Umriss-Ecke zurück."""
    best_index = None
    best_distance = radius
    for i, point in enumerate(room_data.get("boarders", [])):
        distance = math.dist(mouse_position, world_to_screen(point))
        if distance < best_distance:
            best_index, best_distance = i, distance
    return best_index


def closest_border_edge(mouse_position, max_distance=14):
    """Findet die nächste Umrisskante und liefert (Einfügeindex, Punkt)."""
    borders = room_data.get("boarders", [])
    if len(borders) < 3:
        return None
    mx, my = mouse_position
    best = None
    best_distance = max_distance
    for i, a_world in enumerate(borders):
        b_world = borders[(i + 1) % len(borders)]
        ax, ay = world_to_screen(a_world)
        bx, by = world_to_screen(b_world)
        vx, vy = bx - ax, by - ay
        length2 = vx * vx + vy * vy
        if length2 == 0:
            continue
        t = max(0.0, min(1.0, ((mx-ax)*vx + (my-ay)*vy) / length2))
        px, py = ax + t*vx, ay + t*vy
        distance = math.hypot(mx-px, my-py)
        if distance < best_distance:
            best_distance = distance
            point = snapped_point((px, py))
            best = (i + 1, point)
    return best


def update_room_dimensions():
    global room_width, room_height
    borders = room_data.get("boarders", [])
    if len(borders) >= 3:
        room_width = max(float(p[0]) for p in borders) - min(float(p[0]) for p in borders)
        room_height = max(float(p[1]) for p in borders) - min(float(p[1]) for p in borders)


def delete_selected_border_vertex():
    global selected_border_vertex, message
    borders = room_data.get("boarders", [])
    if selected_border_vertex is None or not (0 <= selected_border_vertex < len(borders)):
        message = "Zuerst eine Raumecke auswählen"
        return
    if len(borders) <= 3:
        message = "Ein Raumumriss braucht mindestens 3 Ecken"
        return
    removed = selected_border_vertex
    del borders[removed]
    selected_border_vertex = None
    update_room_dimensions()
    message = f"Raumecke {removed + 1} gelöscht – mit S speichern"


def delete_room(position):
    """Löscht einen Raum und nur dessen Verbindungen; andere Räume bleiben unverändert."""
    global selected_map_room, connection_source_room, selected_connection, message
    position = as_position(position)
    path = room_path(position)
    if not path.exists():
        message = f"Raumdatei nicht gefunden: {path.name}"
        return False
    try:
        path.unlink()
        connections[:] = [c for c in connections
                          if as_position(c.get("room_a", [999999, 999999])) != position
                          and as_position(c.get("room_b", [999999, 999999])) != position]
        save_connections()
        if selected_map_room == position:
            selected_map_room = None
        if connection_source_room == position:
            connection_source_room = None
        selected_connection = None
        message = f"Raum {position} und seine Verbindungen gelöscht"
        return True
    except OSError as exc:
        message = f"Raum konnte nicht gelöscht werden: {exc}"
        return False


def add_entrance(start, end):
    if start == end:
        return
    room_data.setdefault("editor_entrances", []).append({"start": list(start), "end": list(end)})
def draw_grid():
    width, height = SCREEN.get_size()
    left = math.floor(-origin.x / SCALE); right = math.ceil((width-origin.x)/SCALE)
    bottom = math.floor((origin.y-height)/SCALE); top = math.ceil(origin.y/SCALE)
    for i in range(left, right+1):
        x = round(origin.x+i*SCALE)
        pygame.draw.line(SCREEN, GRID_COLOR, (x,0), (x,height))
    for i in range(bottom, top+1):
        y = round(origin.y-i*SCALE)
        pygame.draw.line(SCREEN, GRID_COLOR, (0,y), (width,y))
def draw_room():
    borders = [world_to_screen(p) for p in room_data.get("boarders", [])]
    if len(borders) >= 3:
        pygame.draw.polygon(SCREEN, ROOM_COLOR, borders, 2)
    # Im Raumecken-Werkzeug sind alle Umrisspunkte direkt greifbar.
    if tools[tool_index] == "Raumecken":
        for i, point in enumerate(room_data.get("boarders", [])):
            screen_point = world_to_screen(point)
            color = SELECT_COLOR if i == selected_border_vertex else (100, 220, 230)
            pygame.draw.circle(SCREEN, color, screen_point, 7 if i == selected_border_vertex else 5)
            label = small_font.render(str(i + 1), True, TEXT_COLOR)
            SCREEN.blit(label, (screen_point[0] + 7, screen_point[1] - 16))
    for triangle in room_data.get("collision", []):
        pts = [world_to_screen(p) for p in triangle_points(triangle)]
        pygame.draw.polygon(SCREEN, TRIANGLE_COLOR, pts)
        pygame.draw.polygon(SCREEN, (150,150,170), pts, 1)
    for entrance in room_data.get("editor_entrances", []):
        pygame.draw.line(SCREEN, ENTRANCE_COLOR, world_to_screen(entrance["start"]), world_to_screen(entrance["end"]), 4)
def draw_preview():
    if drag_start is None or drag_current is None:
        return
    p1, p2 = world_to_screen(snapped_point(drag_start)), world_to_screen(snapped_point(drag_current))
    if tools[tool_index] == "Eingang":
        pygame.draw.line(SCREEN, ENTRANCE_COLOR, p1, p2, 4)
    else:
        pygame.draw.rect(SCREEN, PREVIEW_COLOR, pygame.Rect(min(p1[0],p2[0]), min(p1[1],p2[1]), abs(p2[0]-p1[0]), abs(p2[1]-p1[1])), 2)
def map_to_screen(point):
    return round(map_origin.x + point[0]*MAP_SCALE), round(map_origin.y - point[1]*MAP_SCALE)
def map_screen_to_world(point):
    return (point[0]-map_origin.x)/MAP_SCALE, (map_origin.y-point[1])/MAP_SCALE
def room_rect_map(room):
    """Berechnet weiterhin das Begrenzungsrechteck für Auswahl und Dragging."""
    borders = room["borders"]
    pos_x, pos_y = room["position"]

    points = [
        map_to_screen((pos_x + float(p[0]), pos_y + float(p[1])))
        for p in borders
    ]

    min_x = min(p[0] for p in points)
    max_x = max(p[0] for p in points)
    min_y = min(p[1] for p in points)
    max_y = max(p[1] for p in points)

    return pygame.Rect(
        min_x,
        min_y,
        max(2, max_x - min_x),
        max(2, max_y - min_y),
    )
def entrance_lines_on_map():
    lines = []
    room_positions = {r["position"] for r in all_room_files()}
    for ci, conn in enumerate(connections):
        for side in ("a", "b"):
            rp = conn.get(f"room_{side}")
            ent = conn.get(f"entrance_{side}")
            if not rp or not ent or "start" not in ent or "end" not in ent:
                continue
            try:
                pos = as_position(rp)
                start = (pos[0]+float(ent["start"][0]), pos[1]+float(ent["start"][1]))
                end = (pos[0]+float(ent["end"][0]), pos[1]+float(ent["end"][1]))
                lines.append((ci, side, start, end))
            except (ValueError, TypeError, IndexError):
                continue
    return lines
def room_map_info(position):
    for room in all_room_files():
        if room["position"] == position:
            borders = room["borders"]
            return room, (
                min(float(p[0]) for p in borders),
                min(float(p[1]) for p in borders),
                max(float(p[0]) for p in borders),
                max(float(p[1]) for p in borders),
            )
    return None, (0, 0, 10, 10)
def make_connection(room_a, room_b):
    """Create a room-to-room connection using the closest room edges."""
    global message, selected_connection
    if room_a == room_b:
        message = "Bitte zwei verschiedene Räume auswählen"
        return False
    for ci, conn in enumerate(connections):
        if (as_position(conn.get("room_a", [999999, 999999])) == room_a
                and as_position(conn.get("room_b", [999999, 999999])) == room_b):
            selected_connection = ci
            message = "Diese Verbindung existiert bereits; Richtung mit Pfeiltasten ändern"
            return False
        if (as_position(conn.get("room_a", [999999, 999999])) == room_b
                and as_position(conn.get("room_b", [999999, 999999])) == room_a):
            selected_connection = ci
            message = "Umgekehrte Verbindung existiert bereits; Richtung mit Pfeiltasten ändern"
            return False
    _, ba = room_map_info(room_a)
    _, bb = room_map_info(room_b)
    ax0, ay0, ax1, ay1 = ba
    bx0, by0, bx1, by1 = bb
    agx0, agy0, agx1, agy1 = ax0+room_a[0], ay0+room_a[1], ax1+room_a[0], ay1+room_a[1]
    bgx0, bgy0, bgx1, bgy1 = bx0+room_b[0], by0+room_b[1], bx1+room_b[0], by1+room_b[1]
    acx, acy = (agx0+agx1)/2, (agy0+agy1)/2
    bcx, bcy = (bgx0+bgx1)/2, (bgy0+bgy1)/2
    # Connect the nearest sides; entrance coordinates are local to each room.
    dx, dy = bcx-acx, bcy-acy
    if abs(dx) >= abs(dy):
        if dx >= 0:
            ea_start, ea_end = [ax1, max(ay0, min(ay1-3, (ay0+ay1-3)/2))], [ax1, min(ay1, max(ay0+3, (ay0+ay1+3)/2))]
            eb_start, eb_end = [bx0, max(by0, min(by1-3, (by0+by1-3)/2))], [bx0, min(by1, max(by0+3, (by0+by1+3)/2))]
            exit_a, exit_b = "right", "left"
        else:
            ea_start, ea_end = [ax0, max(ay0, min(ay1-3, (ay0+ay1-3)/2))], [ax0, min(ay1, max(ay0+3, (ay0+ay1+3)/2))]
            eb_start, eb_end = [bx1, max(by0, min(by1-3, (by0+by1-3)/2))], [bx1, min(by1, max(by0+3, (by0+by1+3)/2))]
            exit_a, exit_b = "left", "right"
    else:
        if dy >= 0:
            ea_start, ea_end = [max(ax0, min(ax1-3, (ax0+ax1-3)/2)), ay1], [min(ax1, max(ax0+3, (ax0+ax1+3)/2)), ay1]
            eb_start, eb_end = [max(bx0, min(bx1-3, (bx0+bx1-3)/2)), by0], [min(bx1, max(bx0+3, (bx0+bx1+3)/2)), by0]
            exit_a, exit_b = "up", "down"
        else:
            ea_start, ea_end = [max(ax0, min(ax1-3, (ax0+ax1-3)/2)), ay0], [min(ax1, max(ax0+3, (ax0+ax1+3)/2)), ay0]
            eb_start, eb_end = [max(bx0, min(bx1-3, (bx0+bx1-3)/2)), by1], [min(bx1, max(bx0+3, (bx0+bx1+3)/2)), by1]
            exit_a, exit_b = "down", "up"
    connection = {
        "room_a": list(room_a),
        "room_b": list(room_b),
        "entrance_a": {"start": ea_start, "end": ea_end},
        "entrance_b": {"start": eb_start, "end": eb_end},
        "exit_direction_a": exit_a,
        "exit_direction_b": exit_b,
    }
    connections.append(connection)
    selected_connection = len(connections)-1
    save_connections()
    message = f"Verbindung {room_a} → {room_b} erstellt"
    return True
def set_selected_connection_direction(direction):
    """Set arrival/ejection direction on the selected connection side."""
    global message
    if selected_connection is None or not (0 <= selected_connection < len(connections)):
        message = "Zuerst eine rote Verbindungslinie anklicken"
        return
    conn = connections[selected_connection]
    # Left/right are most useful for horizontal room-to-room links.
    side = "a" if selected_map_room and as_position(conn.get("room_a", [-999,-999])) == selected_map_room else "b"
    conn[f"exit_direction_{side}"] = direction
    save_connections()
    message = f"Austrittsrichtung für Raum {conn.get('room_'+side)}: {direction}"
def draw_world_map():
    width, height = SCREEN.get_size()
    # Feines 1er-Raster zum Platzieren; jede 10. Linie ist deutlicher.
    left, right = map_screen_to_world((0,0))[0], map_screen_to_world((width,0))[0]
    top, bottom = map_screen_to_world((0,0))[1], map_screen_to_world((0,height))[1]
    for x in range(math.floor(left/MAP_GRID), math.ceil(right/MAP_GRID)+1):
        world_x = x * MAP_GRID
        sx = map_to_screen((world_x,0))[0]
        major = abs(world_x / MAP_MAJOR_GRID - round(world_x / MAP_MAJOR_GRID)) < 1e-6
        color = (66, 66, 80) if major else GRID_COLOR
        pygame.draw.line(SCREEN, color, (sx,0),(sx,height), 2 if major else 1)
    for y in range(math.floor(bottom/MAP_GRID), math.ceil(top/MAP_GRID)+1):
        world_y = y * MAP_GRID
        sy = map_to_screen((0,world_y))[1]
        major = abs(world_y / MAP_MAJOR_GRID - round(world_y / MAP_MAJOR_GRID)) < 1e-6
        color = (66, 66, 80) if major else GRID_COLOR
        pygame.draw.line(SCREEN, color, (0,sy),(width,sy), 2 if major else 1)
    rooms = all_room_files()
    for room in rooms:
        rect = room_rect_map(room)
        pos = room["position"]
        color = SELECT_COLOR if pos == selected_map_room else ROOM_COLOR
        borders = room["borders"]

        points = [
            map_to_screen((
                pos[0] + float(p[0]),
                pos[1] + float(p[1])
            ))
            for p in borders
        ]

        if len(points) >= 3:
            pygame.draw.polygon(SCREEN, (38, 38, 48), points)
            pygame.draw.polygon(
                SCREEN,
                color,
                points,
                3 if pos == selected_map_room else 2
            )
        label = small_font.render(f"{pos[0]}_{pos[1]}", True, TEXT_COLOR)
        SCREEN.blit(label, (rect.x+5, rect.y+5))
    for ci, side, start, end in entrance_lines_on_map():
        a, b = map_to_screen(start), map_to_screen(end)
        line_color = SELECT_COLOR if ci == selected_connection else ENTRANCE_COLOR
        pygame.draw.line(SCREEN, line_color, a, b, 5)
        pygame.draw.circle(SCREEN, (255,150,150), a, 4)
        pygame.draw.circle(SCREEN, (255,150,150), b, 4)
    hint = "WELTKARTE | Raum ziehen = in 1er-Schritten verschieben | C: Verbindung zum Zielraum | rote Linie wählen, Pfeile = Richtung | M zurück | O öffnen"
    SCREEN.blit(small_font.render(hint, True, TEXT_COLOR), (12, 12))
    SCREEN.blit(small_font.render(f"Welt-Raster: {MAP_GRID:g} (dicke Linien = {MAP_MAJOR_GRID:g}) | Zoom: {MAP_SCALE}px/Einheit", True, TEXT_COLOR), (12, 34))
    SCREEN.blit(small_font.render(message, True, TEXT_COLOR), (12, 56))
def draw_ui():
    lines = [
        f"SoulSide Editor | Raum {room_position}",
        f"Raumgröße: {room_width:g} x {room_height:g}",
        f"Raster: {GRID:g} | Zoom: {SCALE}px/Einheit",
        f"Werkzeug: {tools[tool_index]} (R wechseln)",
        "Raumecken: Punkt ziehen | Kante anklicken = Ecke hinzufügen | Entf = Ecke löschen",
        "1-5: Raster | [ ]: Breite | ; ': Höhe",
        "Numpad 8/2/4/6: Kanten | Shift = umkehren",
        "+/-: Zoom | Pfeile: Ansicht | S: Speichern",
        "O: Raum öffnen | M: Weltkarte | Entf auf Weltkarte: Raum löschen, Y bestätigen",
        message,
    ]
    y = 10
    for line in lines:
        SCREEN.blit(font.render(line, True, TEXT_COLOR), (12,y)); y += 23
def draw_room_input_dialog():
    """Zeigt eine gut sichtbare Eingabebox über beiden Editor-Ansichten."""
    if not room_input_mode:
        return
    width, height = SCREEN.get_size()
    box_w, box_h = min(620, width - 32), 190
    box = pygame.Rect((width - box_w) // 2, (height - box_h) // 2, box_w, box_h)
    shade = pygame.Surface((width, height), pygame.SRCALPHA)
    shade.fill((0, 0, 0, 170))
    SCREEN.blit(shade, (0, 0))
    pygame.draw.rect(SCREEN, (31, 31, 42), box, border_radius=10)
    pygame.draw.rect(SCREEN, SELECT_COLOR, box, 3, border_radius=10)
    title = font.render("Raum öffnen", True, TEXT_COLOR)
    hint = small_font.render("X- und Y-Koordinate eingeben, z. B. 10,0", True, TEXT_COLOR)
    prompt = font.render("Raum X,Y:", True, TEXT_COLOR)
    SCREEN.blit(title, (box.x + 22, box.y + 18))
    SCREEN.blit(hint, (box.x + 22, box.y + 52))
    SCREEN.blit(prompt, (box.x + 22, box.y + 91))
    field = pygame.Rect(box.x + 145, box.y + 83, box.w - 170, 42)
    pygame.draw.rect(SCREEN, (15, 15, 21), field, border_radius=5)
    pygame.draw.rect(SCREEN, SELECT_COLOR, field, 2, border_radius=5)
    typed = font.render(room_input_text + "|", True, TEXT_COLOR)
    SCREEN.blit(typed, (field.x + 10, field.y + 10))
    footer = small_font.render("ENTER = öffnen     ESC = abbrechen", True, (195, 195, 210))
    SCREEN.blit(footer, (box.x + 22, box.bottom - 30))
def begin_room_input():
    global room_input_mode, room_input_text, message
    room_input_mode = True
    room_input_text = ""
    pygame.key.start_text_input()
    message = "Raumkoordinaten eingeben"
def finish_room_input():
    global room_input_mode, message
    text = room_input_text.strip().replace(" ", ",")
    try:
        parts = [p for p in text.split(",") if p != ""]
        if len(parts) != 2:
            raise ValueError("Bitte X,Y eingeben, z. B. 10,0")
        pos = (int(parts[0]), int(parts[1]))
        load_room(pos)
        # Beim Öffnen eines Raums zur lokalen Bearbeitung wechseln.
        globals()["world_map_mode"] = False
    except (ValueError, OSError) as exc:
        message = f"Raum konnte nicht geöffnet werden: {exc}"
    finally:
        room_input_mode = False
        pygame.key.stop_text_input()
def entrance_hit_test(mouse_pos):
    mx, my = mouse_pos
    best = None
    best_dist = 12
    for ci, side, start, end in entrance_lines_on_map():
        a, b = map_to_screen(start), map_to_screen(end)
        vx, vy = b[0]-a[0], b[1]-a[1]
        length2 = vx*vx+vy*vy
        if length2 == 0:
            dist = math.hypot(mx-a[0], my-a[1])
        else:
            t = max(0, min(1, ((mx-a[0])*vx+(my-a[1])*vy)/length2))
            px, py = a[0]+t*vx, a[1]+t*vy
            dist = math.hypot(mx-px, my-py)
        if dist < best_dist:
            best_dist, best = dist, (ci, side, start, end, map_screen_to_world(mouse_pos))
    return best
load_room((0,0))
load_connections()
while running:
    clock.tick(60)
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if room_input_mode:
                if event.key == pygame.K_ESCAPE:
                    room_input_mode = False
                    pygame.key.stop_text_input()
                    message = "Raumauswahl abgebrochen"
                elif event.key == pygame.K_RETURN:
                    finish_room_input()
                elif event.key == pygame.K_BACKSPACE:
                    room_input_text = room_input_text[:-1]
                elif event.unicode and (event.unicode.isdigit() or event.unicode in ",-+ "):
                    room_input_text += event.unicode
                continue
            if event.type == pygame.TEXTINPUT and room_input_mode:
                # TEXTINPUT unterstützt auch Tastaturlayouts, bei denen KEYDOWN.unicode unzuverlässig ist.
                room_input_text += "".join(ch for ch in event.text if ch.isdigit() or ch in ",-+ ")
                continue
            if event.key == pygame.K_ESCAPE:
                running = False
            elif event.key == pygame.K_m:
                world_map_mode = not world_map_mode
                map_drag = None; entrance_drag = None
                message = "Weltkarte geöffnet" if world_map_mode else f"Raum {room_position} geöffnet"
            elif event.key == pygame.K_o:
                begin_room_input()
            elif world_map_mode:
                if event.key == pygame.K_LEFT:
                    if selected_connection is not None: set_selected_connection_direction("left")
                    else: map_origin.x += 30
                elif event.key == pygame.K_RIGHT:
                    if selected_connection is not None: set_selected_connection_direction("right")
                    else: map_origin.x -= 30
                elif event.key == pygame.K_UP:
                    if selected_connection is not None: set_selected_connection_direction("up")
                    else: map_origin.y += 30
                elif event.key == pygame.K_DOWN:
                    if selected_connection is not None: set_selected_connection_direction("down")
                    else: map_origin.y -= 30
                elif event.key in (pygame.K_DELETE, pygame.K_BACKSPACE):
                    if selected_map_room is None:
                        message = "Zuerst einen Raum auswählen"
                    else:
                        delete_room_armed = True
                        message = f"Raum {selected_map_room} löschen? Mit Y bestätigen, andere Taste bricht ab"
                elif event.key == pygame.K_y and delete_room_armed:
                    if selected_map_room is not None:
                        delete_room(selected_map_room)
                    delete_room_armed = False
                elif delete_room_armed:
                    delete_room_armed = False
                    message = "Raumlöschung abgebrochen"
                elif event.key == pygame.K_c:
                    if selected_map_room is None:
                        message = "Zuerst den Ausgangsraum anklicken, dann C"
                    else:
                        connection_source_room = selected_map_room
                        message = f"Ausgangsraum {connection_source_room} gewählt – jetzt Zielraum anklicken"
                elif event.key == pygame.K_BACKSPACE:
                    connection_source_room = None
                    message = "Verbindungserstellung abgebrochen"
                elif event.key in (pygame.K_PLUS, pygame.K_EQUALS, pygame.K_KP_PLUS): MAP_SCALE = min(70, MAP_SCALE+2)
                elif event.key in (pygame.K_MINUS, pygame.K_KP_MINUS): MAP_SCALE = max(5, MAP_SCALE-2)
                elif event.key == pygame.K_s:
                    save_connections(); message = "Verbindungen gespeichert"
            else:
                if event.key == pygame.K_r:
                    tool_index = (tool_index+1) % len(tools); message = f"Werkzeug: {tools[tool_index]}"
                elif event.key in (pygame.K_DELETE, pygame.K_BACKSPACE) and tools[tool_index] == "Raumecken":
                    delete_selected_border_vertex()
                elif event.key == pygame.K_s and tools[tool_index] == "Raumecken":
                    save_room()
                elif event.key in (pygame.K_1,pygame.K_2,pygame.K_3,pygame.K_4,pygame.K_5):
                    GRID = {pygame.K_1:1.0, pygame.K_2:0.5, pygame.K_3:0.25, pygame.K_4:0.1, pygame.K_5:0.05}[event.key]
                    message = f"Raster auf {GRID:g} gesetzt"
                elif event.key == pygame.K_KP8: resize_room("up")
                elif event.key == pygame.K_KP2: resize_room("down")
                elif event.key == pygame.K_KP4: resize_room("left")
                elif event.key == pygame.K_KP6: resize_room("right")
                elif event.key == pygame.K_LEFTBRACKET: resize_room("width-")
                elif event.key == pygame.K_RIGHTBRACKET: resize_room("width+")
                elif event.key == pygame.K_SEMICOLON: resize_room("height-")
                elif event.key == pygame.K_QUOTE: resize_room("height+")
                elif event.key in (pygame.K_PLUS,pygame.K_EQUALS,pygame.K_KP_PLUS): SCALE = min(200,SCALE+10)
                elif event.key in (pygame.K_MINUS,pygame.K_KP_MINUS): SCALE = max(10,SCALE-10)
                elif event.key == pygame.K_LEFT: origin.x += 30
                elif event.key == pygame.K_RIGHT: origin.x -= 30
                elif event.key == pygame.K_UP: origin.y += 30
                elif event.key == pygame.K_DOWN: origin.y -= 30
                elif event.key == pygame.K_s: save_room()
                elif event.key == pygame.K_F1: resize_room("up")
                elif event.key == pygame.K_F2: resize_room("width+")
                elif event.key == pygame.K_F3: resize_room("height+")
                elif event.key == pygame.K_F4: resize_room("width-")
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if world_map_mode:
                if event.button == 1:
                    hit = entrance_hit_test(event.pos)
                    if hit:
                        ci, side, start, end, mouse_world = hit
                        selected_connection = ci
                        entrance_drag = {"index":ci,"side":side,"start":start,"end":end,"mouse_world":mouse_world}
                        map_drag = None
                    else:
                        found = None
                        for room in reversed(all_room_files()):
                            if room_rect_map(room).collidepoint(event.pos):
                                found = room; break
                        if found:
                            clicked_position = found["position"]
                            if connection_source_room is not None:
                                make_connection(connection_source_room, clicked_position)
                                connection_source_room = None
                                selected_map_room = clicked_position
                                map_drag = None
                            else:
                                selected_map_room = clicked_position
                                rect = room_rect_map(found)
                                mouse_world = map_screen_to_world(event.pos)
                                map_drag = {"old":found["position"], "offset":(found["position"][0]-mouse_world[0], found["position"][1]-mouse_world[1]), "start":event.pos}
                            entrance_drag = None
                        else:
                            map_drag = {"pan":True,"last":event.pos}
                elif event.button == 4: MAP_SCALE = min(70, MAP_SCALE+2)
                elif event.button == 5: MAP_SCALE = max(5, MAP_SCALE-2)
            else:
                if event.button == 1:
                    if tools[tool_index] == "Raumecken":
                        hit_vertex = border_vertex_hit_test(event.pos)
                        if hit_vertex is not None:
                            selected_border_vertex = hit_vertex
                            border_drag = {"index": hit_vertex}
                            message = f"Raumecke {hit_vertex + 1} ausgewählt – ziehen zum Verschieben"
                        else:
                            edge_hit = closest_border_edge(event.pos)
                            if edge_hit is not None:
                                insert_at, point = edge_hit
                                room_data["boarders"].insert(insert_at, list(point))
                                selected_border_vertex = insert_at
                                border_drag = {"index": insert_at}
                                update_room_dimensions()
                                message = f"Raumecke {insert_at + 1} hinzugefügt – ziehen zum Positionieren"
                            else:
                                selected_border_vertex = None
                                border_drag = None
                                message = "Ecke auswählen oder nahe an einer Kante klicken, um eine hinzuzufügen"
                    elif tools[tool_index] == "Löschen":
                        message = "Dreieck gelöscht" if erase_at(event.pos) else "Kein Dreieck getroffen"
                    else:
                        drag_start = event.pos; drag_current = event.pos
                elif event.button == 4: SCALE = min(200,SCALE+5)
                elif event.button == 5: SCALE = max(10,SCALE-5)
        elif event.type == pygame.MOUSEMOTION:
            if world_map_mode:
                if map_drag and map_drag.get("pan"):
                    dx,dy = event.pos[0]-map_drag["last"][0], event.pos[1]-map_drag["last"][1]
                    map_origin.x += dx; map_origin.y += dy; map_drag["last"] = event.pos
                elif entrance_drag:
                    # Keep entrance endpoints local to their room; translate the whole segment.
                    current = map_screen_to_world(event.pos)
                    initial = entrance_drag["mouse_world"]
                    dx,dy = current[0]-initial[0], current[1]-initial[1]
                    conn = connections[entrance_drag["index"]]
                    ent = conn[f"entrance_{entrance_drag['side']}"]
                    rp = as_position(conn[f"room_{entrance_drag['side']}"])
                    ent["start"] = [snap(entrance_drag["start"][0]+dx-rp[0], 0.5), snap(entrance_drag["start"][1]+dy-rp[1], 0.5)]
                    ent["end"] = [snap(entrance_drag["end"][0]+dx-rp[0], 0.5), snap(entrance_drag["end"][1]+dy-rp[1], 0.5)]
                elif map_drag and not map_drag.get("pan"):
                    # Preview is intentionally not persisted until mouse release.
                    pass
            elif border_drag is not None:
                idx = border_drag["index"]
                if 0 <= idx < len(room_data.get("boarders", [])):
                    room_data["boarders"][idx] = list(snapped_point(event.pos))
                    update_room_dimensions()
            elif drag_start is not None:
                drag_current = event.pos
        elif event.type == pygame.MOUSEBUTTONUP:
            if world_map_mode and event.button == 1:
                if entrance_drag:
                    save_connections()
                    message = "Eingang in connections.json gespeichert"
                    entrance_drag = None
                elif map_drag and not map_drag.get("pan"):
                    old = map_drag["old"]
                    mouse_world = map_screen_to_world(event.pos)
                    offx, offy = map_drag["offset"]
                    new = (int(round(snap(mouse_world[0]+offx, MAP_GRID))), int(round(snap(mouse_world[1]+offy, MAP_GRID))))
                    move_room(old, new)
                    map_drag = None
                elif map_drag and map_drag.get("pan"):
                    map_drag = None
            elif not world_map_mode and event.button == 1 and border_drag is not None:
                border_drag = None
                message = "Raumecke verschoben – mit S speichern"
            elif not world_map_mode and event.button == 1 and drag_start is not None:
                a, b = snapped_point(drag_start), snapped_point(event.pos)
                selected = tools[tool_index]
                if selected == "Rechteck": add_rectangle(a,b); message = "Rechteck hinzugefügt"
                elif selected == "Dreieck": add_right_triangle(a,b); message = "Dreieck hinzugefügt"
                elif selected == "Eingang": add_entrance(a,b); message = "Lokale Eingangsmarkierung hinzugefügt (noch keine Spielverbindung)"
                drag_start = None; drag_current = None
    SCREEN.fill(BG)
    if world_map_mode:
        draw_world_map()
    else:
        draw_grid(); draw_room(); draw_preview(); draw_ui()
    draw_room_input_dialog()
    pygame.display.flip()
pygame.quit()
