# stealth_hack_game.py – Vollversion (Mai 2025)
# ------------------------------------------------
# Abhängigkeit: pip install pygame>=2.1

import pygame, sys, random, os, json
from heapq import heappush, heappop
pygame.init()

# ------------------------------------------------
# 0) Leaderboard-Funktionen
# ------------------------------------------------
LB_FILE, LB_MAX = "leaderboard.txt", 5

def _lb_file(mode: str | None = None) -> str:
    return LB_FILE if mode is None else f"leaderboard_{mode}.txt"

def load_leaderboard(mode: str | None = None):
    fn = _lb_file(mode)
    if not os.path.exists(fn):
        return []
    with open(fn) as f:
        return [int(l) for l in f if l.strip().isdigit()]

def save_leaderboard(scores: list[int], mode: str | None = None):
    fn = _lb_file(mode)
    with open(fn, "w") as f:
        for s in sorted(scores, reverse=True)[:LB_MAX]:
            f.write(f"{s}\n")

def update_leaderboard(new: int, mode: str):
    for m in (None, mode):
        sc = load_leaderboard(m); sc.append(new); save_leaderboard(sc, m)

# ------------------------------------------------
# 1) Konstanten & Farben
# ------------------------------------------------
BASE_W, BASE_H = 800, 600
INFO = pygame.display.Info()
MAX_W, MAX_H = int(INFO.current_w * 0.9), int(INFO.current_h * 0.9)
FPS = 60
TILE = 20

CHASE_TIMEOUT = 10_000
PATH_COMMIT_MS = 300
SAFE_RADIUS = 250  # will be tweaked per difficulty

WHITE = (255, 255, 255); BLACK = (0, 0, 0); RED = (255, 0, 0); GREEN = (0, 255, 0)
BLUE = (0, 0, 255); GRAY = (128, 128, 128); YELLOW = (255, 255, 0); ORANGE = (255, 165, 0)

LANG_FILE = "language.cfg"

# ------------------------------------------------
# 2) Sprache (EN/DE/ES/FR)
# ------------------------------------------------
lang_texts = {
    "en": {"title": "Stealth Hack Game", "start": "Start Game", "leader": "Leaderboards",
            "ctrl": "Controls", "shopdesc": "Shop Info", "lang": "Change Language", "quit": "Quit",
            "difficulty": "Difficulty", "easy": "Easy", "normal": "Normal", "hard": "Hardcore", "night": "Nightmare",
            "settings": "Settings", "fake": "Fake Guard", "tele": "Teleport Guard", "bomber": "Bomber Guard", "on": "On", "off": "Off",
            "next": "Press Enter for next level",
            "shop_info": "EMP - disable cameras briefly | Faster - hack twice as fast | Stealth - guards react slower | Weapon - shoot bullets",
            "faster": "Faster", "stealth": "Stealth", "weapon": "Weapon", "money": "Money",
            "controls_text": "Move: W,A,S,D or Arrows | Hack: H | EMP: E | Shoot: Space or Mouse | Door: O",
            "back": "ESC – back"},
    "de": {"title": "Stealth Hack Game", "start": "Spiel Starten", "leader": "Leaderboards",
            "ctrl": "Steuerungen", "shopdesc": "Shop Infos", "lang": "Sprache wechseln", "quit": "Beenden",
            "difficulty": "Schwierigkeit", "easy": "Einfach", "normal": "Normal", "hard": "Hart", "night": "Albtraum",
            "settings": "Einstellungen", "fake": "Fake-Wächter", "tele": "Teleport-Wächter", "bomber": "Bomber-Wächter", "on": "An", "off": "Aus",
            "next": "Weiter mit Enter",
            "shop_info": "EMP - Kameras kurz deaktivieren | Schneller - halbiert Hackzeit | Stealth - Wächter sehen dich später | Waffe - ermöglicht Schießen",
            "faster": "Schneller", "stealth": "Stealth", "weapon": "Waffe", "money": "Geld",
            "controls_text": "Bewegen: W,A,S,D oder Pfeiltasten | Hack: H | EMP: E | Schießen: Space oder Maus | Tür: O",
            "back": "ESC – zurück"},
    "es": {"title": "Juego de Infiltración", "start": "Iniciar Juego", "leader": "Marcadores",
            "ctrl": "Controles", "shopdesc": "Info de Tienda", "lang": "Cambiar idioma", "quit": "Salir",
            "difficulty": "Dificultad", "easy": "Fácil", "normal": "Normal", "hard": "Extremo", "night": "Pesadilla",
            "settings": "Opciones", "fake": "Guardia Falso", "tele": "Guardia Teleport", "bomber": "Guardia Bomba", "on": "Sí", "off": "No",
            "next": "Pulsa Enter para continuar",
            "shop_info": "EMP - desactiva cámaras un momento | Rápido - hackeo más corto | Sigilo - guardias te detectan más lento | Arma - permite disparar",
            "faster": "Rápido", "stealth": "Sigilo", "weapon": "Arma", "money": "Dinero",
            "controls_text": "Mover: W,A,S,D o Flechas | Hack: H | EMP: E | Disparar: Espacio o Ratón | Puerta: O",
            "back": "ESC – volver"},
    "fr": {"title": "Jeu d’Infiltration", "start": "Démarrer", "leader": "Scores", "ctrl": "Commandes", "shopdesc": "Infos boutique", "lang": "Changer la langue", "quit": "Quitter", "difficulty": "Difficulté", "easy": "Facile", "normal": "Normal", "hard": "Difficile", "night": "Cauchemar",
            "settings": "Options", "fake": "Faux garde", "tele": "Garde téléporteur", "bomber": "Garde bombe", "on": "Oui", "off": "Non",
            "next": "Entrée pour continuer", "shop_info": "EMP - désactive les caméras un instant | Rapide - piratage deux fois plus vite | Furtif - les gardes te repèrent moins vite | Arme - permet de tirer", "faster": "Rapide", "stealth": "Furtif", "weapon": "Arme", "money": "Argent", "controls_text": "Bouger: W,A,S,D ou Flèches | Hacker: H | EMP: E | Tirer: Espace ou Souris | Porte: O", "back": "ESC – retour"}
}

def load_language():
    try:
        with open(LANG_FILE) as f:
            code = json.load(f)
            return code if code in lang_texts else "en"
    except:
        return "en"


def save_language(code: str):
    try:
        open(LANG_FILE, "w").write(json.dumps(code))
    except:
        pass


current_language = load_language()

# Difficulty settings
DIFFICULTIES = {
    "easy": {
        "patrol": 1.5, "chase": 2.5, "obstacles": 1.5,
        "guard_offset": 0, "door_lvl": 3, "safe": 250,
        "ammo": 6, "emp": 4, "reload": 0.8, "emp_cd": 0.8,
        "cam_rot": 0.5, "reward": 1.0,
        "special": 1, "tele_ms": 1500, "bomb_cd": 4000, "bomb_delay": 2000
    },
    "normal": {
        "patrol": 2.2, "chase": 3.2, "obstacles": 1.0,
        "guard_offset": 1, "door_lvl": 2, "safe": 250,
        "ammo": 5, "emp": 3, "reload": 1.0, "emp_cd": 1.0,
        "cam_rot": 1.0, "reward": 1.0,
        "special": 2, "tele_ms": 1000, "bomb_cd": 3000, "bomb_delay": 1600
    },
    "hardcore": {
        "patrol": 2.2, "chase": 4.0, "obstacles": 0.7,
        "guard_offset": 1, "door_lvl": 2, "safe": 180,
        "ammo": 3, "emp": 2, "reload": 1.3, "emp_cd": 1.3,
        "cam_rot": 2.0, "reward": 0.7,
        "special": 3, "tele_ms": 700, "bomb_cd": 2500, "bomb_delay": 1000
    },
    "nightmare": {
        "patrol": 3.0, "chase": 5.0, "obstacles": 0.5,
        "guard_offset": 1, "door_lvl": 2, "safe": 120,
        "ammo": 0, "emp": 0, "reload": 1.5, "emp_cd": 1.5,
        "cam_rot": 3.0, "reward": 0.5,
        "special": 99, "tele_ms": 500, "bomb_cd": 2000, "bomb_delay": 600
    }
}
difficulty_mode = "normal"
guard_opts = {"fake": True, "teleport": True, "bomber": True}
def cfg(k):
    return DIFFICULTIES[difficulty_mode][k]

# ------------------------------------------------
# 3) Geometrie / Sicht
# ------------------------------------------------

def ccw(A, B, C):
    return (C[1] - A[1]) * (B[0] - A[0]) > (B[1] - A[1]) * (C[0] - A[0])


def segments_intersect(a, b, c, d):
    return ccw(a, c, d) != ccw(b, c, d) and ccw(a, b, c) != ccw(a, b, d)


def line_intersects_rect(p1, p2, r):
    tl, tr = (r.left, r.top), (r.right, r.top); br, bl = (r.right, r.bottom), (r.left, r.bottom)
    return any(segments_intersect(p1, p2, a, b) for a, b in ((tl, tr), (tr, br), (br, bl), (bl, tl)))


def line_of_sight(p1, p2, walls):
    return not any(line_intersects_rect(p1, p2, w) for w in walls)


def visible_endpoint(p1, dirvec, max_len, walls, step=5):
    pos = pygame.math.Vector2(p1)
    d = dirvec.normalize()
    for _ in range(int(max_len // step)):
        nxt = pos + d * step
        r = pygame.Rect(nxt.x, nxt.y, 2, 2)
        if any(r.colliderect(w) for w in walls):
            break
        pos = nxt
    return pos.x, pos.y

# ------------------------------------------------
# 4) Grid + A*
# ------------------------------------------------

def build_grid(walls, room_w, room_h, t=TILE):
    blocked = set()
    for r in walls:
        for gx in range(r.left // t, (r.right - 1) // t + 1):
            for gy in range(r.top // t, (r.bottom - 1) // t + 1):
                blocked.add((gx, gy))
    return room_w // t, room_h // t, blocked


def astar(s, g, blocked, gw, gh):
    def h(a, b):
        return abs(a[0] - b[0]) + abs(a[1] - b[1])

    open = [(h(s, g), s)]; came = {}; gscore = {s: 0}
    while open:
        _, cur = heappop(open)
        if cur == g:
            path = []
            while cur in came:
                path.append(cur); cur = came[cur]
            return path[::-1]
        cx, cy = cur
        for nx, ny in ((cx + 1, cy), (cx - 1, cy), (cx, cy + 1), (cx, cy - 1)):
            if not (0 <= nx < gw and 0 <= ny < gh) or (nx, ny) in blocked:
                continue
            score = gscore[cur] + 1
            if score < gscore.get((nx, ny), 1e9):
                gscore[(nx, ny)] = score; came[(nx, ny)] = cur
                heappush(open, (score + h((nx, ny), g), (nx, ny)))
    return []

# ------------------------------------------------
# 5) Text-Shortcut
# ------------------------------------------------

def draw_txt(surf, txt, size, pos, color=BLACK):
    surf.blit(pygame.font.SysFont(None, size).render(txt, True, color), pos)


def guard_collides_player(player: pygame.sprite.Sprite, guards: pygame.sprite.Group) -> bool:
    """Return True if the player should die by touching a guard."""
    for g in guards:
        if player.rect.colliderect(g.rect):
            if isinstance(g, (FakeGuard, BomberGuard)):
                continue
            if g.stun and difficulty_mode in ("easy", "normal"):
                continue
            return True
    return False

# ------------------------------------------------
# 6) Spawn-Helpers
# ------------------------------------------------

def get_valid_position(w, h, walls, room_w, room_h):
    for _ in range(100):
        x = random.randint(50, room_w - 50 - w)
        y = random.randint(50, room_h - 50 - h)
        r = pygame.Rect(x, y, w, h)
        if not any(r.colliderect(wl) for wl in walls):
            return (x + w // 2, y + h // 2)
    return (w // 2 + 50, h // 2 + 50)


def get_player_spawn(room):
    corners = [(40, 40), (room.width - 40, 40), (40, room.height - 40), (room.width - 40, room.height - 40)]
    for c in corners:
        r = pygame.Rect(0, 0, 30, 30); r.center = c
        if not any(r.colliderect(w) for w in room.inner_walls):
            return c
    return get_valid_position(30, 30, room.inner_walls, room.width, room.height)

# ------------------------------------------------
# 7) Door
# ------------------------------------------------

class Door(pygame.sprite.Sprite):
    def __init__(self, x, y, w, h, dest):
        super().__init__()
        self.rect = pygame.Rect(x, y, w, h); self.destination = dest

    def draw(self, s):
        pygame.draw.rect(s, ORANGE, self.rect)

# ------------------------------------------------
# 8) Spiel-Objekte
# ------------------------------------------------

class Player(pygame.sprite.Sprite):
    def __init__(self, pos):
        super().__init__()
        self.image = pygame.Surface((30, 30)); self.image.fill(BLUE)
        self.rect = self.image.get_rect(center=pos)
        self.speed = 4
        self.money = 100
        self.upg = {"EMP": False, "Faster": False, "Stealth": False, "Weapon": False}
        self.ammo_max = cfg("ammo")
        self.ammo = 0
        self.reload_time = int(1000 * cfg("reload"))
        self.last_shot = 0
        self.emp_max = cfg("emp")
        self.emp_left = 0
        self.emp_cd = int(3000 * cfg("emp_cd"))
        self.last_emp = 0

    def update(self, keys, walls):
        dx = keys[pygame.K_d] + keys[pygame.K_RIGHT] - keys[pygame.K_a] - keys[pygame.K_LEFT]
        dy = keys[pygame.K_s] + keys[pygame.K_DOWN] - keys[pygame.K_w] - keys[pygame.K_UP]

        rect = self.rect
        if dx or dy:
            step_x = dx * self.speed
            step_y = dy * self.speed

            cand = rect.move(step_x, step_y)
            if not any(cand.colliderect(w) for w in walls):
                rect = cand
            else:
                if step_x:
                    tmp = rect.move(step_x, 0)
                    if not any(tmp.colliderect(w) for w in walls):
                        rect = tmp
                if step_y:
                    tmp = rect.move(0, step_y)
                    if not any(tmp.colliderect(w) for w in walls):
                        rect = tmp
        rect.clamp_ip(pygame.Rect(0, 0, current_level.width, current_level.height))
        self.rect = rect

    def draw(self, s):
        s.blit(self.image, self.rect)
        now = pygame.time.get_ticks()
        if self.upg["Weapon"] and self.ammo > 0 and now - self.last_shot < self.reload_time:
            frac = (now - self.last_shot) / self.reload_time
            bw = int(30 * frac)
            br = pygame.Rect(0, 0, bw, 3)
            br.midtop = (self.rect.centerx, self.rect.bottom + 2)
            pygame.draw.rect(s, BLUE, br)
        if self.upg["Weapon"]:
            draw_txt(s, str(self.ammo), 12, (self.rect.centerx + 20, self.rect.bottom))
        if self.upg["EMP"] and self.emp_left > 0 and now - self.last_emp < self.emp_cd:
            frac = (now - self.last_emp) / self.emp_cd
            gw = int(30 * frac)
            gr = pygame.Rect(0, 0, gw, 3)
            gr.midtop = (self.rect.centerx, self.rect.bottom + 10)
            pygame.draw.rect(s, GREEN, gr)
        if self.upg["EMP"]:
            draw_txt(s, str(self.emp_left), 12, (self.rect.centerx + 20, self.rect.bottom + 8))


class Terminal(pygame.sprite.Sprite):
    BAR_W = 30; BAR_H = 5

    def __init__(self, pos):
        super().__init__()
        self.image = pygame.Surface((30, 30)); self.image.fill(GRAY)
        self.rect = self.image.get_rect(center=pos)
        self.hacked = False; self.hacking = False; self.time = 4000; self.start = 0

    def interact(self, player):
        if self.hacked or self.hacking:
            return
        self.hacking = True; self.start = pygame.time.get_ticks()
        if player.upg["Faster"]:
            self.time = 2000

    def update(self):
        if self.hacking and pygame.time.get_ticks() - self.start >= self.time:
            self.hacked = True; self.hacking = False; self.image.fill(GREEN)

    def _progress(self):
        if not self.hacking:
            return 0.0
        return (pygame.time.get_ticks() - self.start) / self.time

    def draw(self, s):
        s.blit(self.image, self.rect)
        if self.hacking:
            frac = max(0.0, min(1.0, self._progress()))
            w = int(self.BAR_W * frac)
            bar_rect = pygame.Rect(0, 0, w, self.BAR_H)
            bar_rect.midbottom = (self.rect.centerx, self.rect.top - 2)
            pygame.draw.rect(s, BLUE, bar_rect)


class Bullet(pygame.sprite.Sprite):
    def __init__(self, pos, vec):
        super().__init__()
        self.image = pygame.Surface((5, 5)); self.image.fill(BLACK)
        self.rect = self.image.get_rect(center=pos)
        self.dir = vec.normalize() if vec.length() else pygame.math.Vector2()
        self.sp = 8

    def update(self):
        self.rect.move_ip(self.dir.x * self.sp, self.dir.y * self.sp)

    def draw(self, s):
        s.blit(self.image, self.rect)


class Camera(pygame.sprite.Sprite):
    def __init__(self, pos):
        super().__init__()
        self.image = pygame.Surface((20, 20)); self.image.fill(YELLOW)
        self.rect = self.image.get_rect(center=pos)
        self.dir = pygame.math.Vector2(1, 0)
        self.vision = 200; self.angle = 45
        self.rot_speed = cfg("cam_rot")

    def update(self, emp):
        if not emp:
            self.dir = self.dir.rotate(self.rot_speed)

    def detect(self, player, walls):
        end = visible_endpoint(self.rect.center, self.dir, self.vision, walls)
        return line_intersects_rect(self.rect.center, end, player.rect)

    def draw(self, s, walls):
        s.blit(self.image, self.rect)
        end = visible_endpoint(self.rect.center, self.dir, self.vision, walls)
        pygame.draw.line(s, ORANGE, self.rect.center, end, 2)

# ---------- smooth NPC Guard ----------------------------------
class NPCGuard(pygame.sprite.Sprite):
    PATROL_SP = 2.2; CHASE_SP = 3.2; VIS = 150; ANG = 60

    def __init__(self, pos):
        super().__init__()
        self.image = pygame.Surface((30, 30)); self.image.fill(RED)
        self.rect = self.image.get_rect(center=pos)
        self.state = "patrol"
        self.PATROL_SP = cfg("patrol")
        self.CHASE_SP = cfg("chase")
        self.dir = self._rand_dir(); self.timer = 0
        self.path = []; self.idx = 0; self.last_astar = 0; self.chase_start = 0
        self.stun = False; self.stun_t = 0; self.STUN_MS = 3000
        self.look = self.dir

    def _rand_dir(self):
        v = pygame.math.Vector2(random.uniform(-1, 1), random.uniform(-1, 1))
        return (v if v.length() else pygame.math.Vector2(1, 0)).normalize()

    def _need_path(self):
        return not self.path or pygame.time.get_ticks() - self.last_astar > PATH_COMMIT_MS

    def _recalc_path(self, player, walls):
        gw, gh, blk = build_grid(walls, current_level.width, current_level.height)
        s = (self.rect.centerx // TILE, self.rect.centery // TILE)
        g = (player.rect.centerx // TILE, player.rect.centery // TILE)
        # if the player's tile is blocked (e.g. hugging a wall) choose a nearby free tile
        if g in blk:
            for dx, dy in ((1,0),(-1,0),(0,1),(0,-1)):
                cand = (g[0] + dx, g[1] + dy)
                if 0 <= cand[0] < gw and 0 <= cand[1] < gh and cand not in blk:
                    g = cand
                    break
        self.path = astar(s, g, blk, gw, gh); self.idx = 0; self.last_astar = pygame.time.get_ticks()

    def _move(self, vec, spd, walls):
        """Move with basic wall sliding to avoid getting stuck in corners."""
        if vec.length() == 0:
            return False
        vec = vec.normalize() * spd
        dx, dy = int(round(vec.x)), int(round(vec.y))

        bounds = pygame.Rect(0, 0, current_level.width, current_level.height)

        # try diagonal step first
        cand = self.rect.move(dx, dy)
        if bounds.contains(cand) and not any(cand.colliderect(w) for w in walls):
            self.rect = cand
            return True

        moved = False
        if dx:
            cand = self.rect.move(dx, 0)
            if bounds.contains(cand) and not any(cand.colliderect(w) for w in walls):
                self.rect = cand
                moved = True
        if dy:
            cand = self.rect.move(0, dy)
            if bounds.contains(cand) and not any(cand.colliderect(w) for w in walls):
                self.rect = cand
                moved = True

        if not moved:
            # small perpendicular nudge to escape tight corners
            perp = pygame.math.Vector2(-vec.y, vec.x).normalize()
            p_dx = int(round(perp.x))
            p_dy = int(round(perp.y))
            for sign in (1, -1):
                cand = self.rect.move(p_dx * sign, p_dy * sign)
                if bounds.contains(cand) and not any(cand.colliderect(w) for w in walls):
                    self.rect = cand
                    return True

        return moved

    def update(self, player, alarm, emp, walls, panic):
        now = pygame.time.get_ticks()
        if self.stun:
            if now - self.stun_t >= self.STUN_MS:
                self.stun = False; self.image.fill(RED); self.state = "patrol"
            else:
                return alarm
        to_pl = pygame.math.Vector2(player.rect.center) - pygame.math.Vector2(self.rect.center)
        self.stealth_mod = 0.85 if player.upg["Stealth"] else 1.0
        vis = self.VIS * self.stealth_mod
        ang = self.ANG
        sees = to_pl.length() < vis and (to_pl.length() == 0 or abs(self.look.angle_to(to_pl)) < ang) \
            and line_of_sight(self.rect.center, player.rect.center, walls)
        if (sees or panic) and not emp:
            if self.state != "chase":
                self.state = "chase"; self.chase_start = now; self.path = []
            alarm = alarm or panic
        elif self.state == "chase" and now - self.chase_start > CHASE_TIMEOUT:
            self.state = "patrol"

        if self.state == "patrol":
            self.timer -= 16
            if self.timer <= 0 or not self._move(self.dir, self.PATROL_SP * self.stealth_mod, walls):
                self.dir = self._rand_dir(); self.timer = random.randint(1000, 3000)
            self.look = self.dir
        else:
            if to_pl.length() > 0:
                self.look = to_pl.normalize()
            if line_of_sight(self.rect.center, player.rect.center, walls):
                self.path = []; self.idx = 0
                self._move(to_pl, self.CHASE_SP * self.stealth_mod, walls)
            else:
                if self._need_path():
                    self._recalc_path(player, walls)
                if self.path and self.idx < len(self.path):
                    wp = self.path[self.idx]
                    tgt = pygame.math.Vector2(wp[0] * TILE + TILE / 2, wp[1] * TILE + TILE / 2)
                    vec = tgt - pygame.math.Vector2(self.rect.center)
                    if vec.length() < 5:
                        self.idx += 1
                    else:
                        if not self._move(vec, self.CHASE_SP * self.stealth_mod, walls):
                            self.idx += 1
                else:
                    self._move(to_pl, self.CHASE_SP * self.stealth_mod, walls)
        return alarm

    def draw(self, s):
        s.blit(self.image, self.rect)
        length = self.VIS * getattr(self, 'stealth_mod', 1.0)
        end = (self.rect.centerx + self.look.x * length, self.rect.centery + self.look.y * length)
        pygame.draw.line(s, ORANGE, self.rect.center, end, 2)


class FakeGuard(NPCGuard):
    """Blue decoy guard that wanders between terminals."""
    def __init__(self, pos, terminals):
        super().__init__(pos)
        self.image.fill(BLUE)
        self.PATROL_SP *= 1.2
        self.terminals = terminals
        self.target = None
        self.wait = 0
        self.mode = "wander"
        self.behave_timer = 0

    def update(self, player, alarm, emp, walls, panic):
        if self.wait > 0:
            self.wait -= 16
            return alarm

        self.behave_timer -= 16
        if self.behave_timer <= 0:
            r = random.random()
            if r < 0.45:
                self.mode = "approach"; self.behave_timer = random.randint(500, 1000)
            elif r < 0.9:
                self.mode = "wander"; self.behave_timer = random.randint(500, 1000)
                self.target = random.choice(list(self.terminals))
            else:
                self.mode = "idle"; self.behave_timer = random.randint(300, 500)

        if self.mode == "approach":
            vec = pygame.math.Vector2(player.rect.center) - pygame.math.Vector2(self.rect.center)
            if vec.length() > 2:
                self._move(vec, self.PATROL_SP, walls)
            self.look = vec.normalize() if vec.length() else self.look
        elif self.mode == "wander":
            if not self.target:
                self.target = random.choice(list(self.terminals))
            vec = pygame.math.Vector2(self.target.rect.center) - pygame.math.Vector2(self.rect.center)
            if vec.length() < 5:
                self.wait = random.randint(200, 400)
                self.target = random.choice(list(self.terminals))
            else:
                self._move(vec, self.PATROL_SP, walls)
            self.look = vec.normalize() if vec.length() else self.look
        else:  # idle
            vec = pygame.math.Vector2()
        return alarm

    def draw(self, s):
        s.blit(self.image, self.rect)


class TeleportGuard(NPCGuard):
    """Guard that teleports to the alarm position when triggered."""
    COLOR = (0, 100, 0)

    def __init__(self, pos):
        super().__init__(pos)
        self.image.fill(self.COLOR)
        self.teleporting = False
        self.tp_start = 0
        self.tp_target = (0, 0)

    def update(self, player, alarm, emp, walls, panic):
        now = pygame.time.get_ticks()
        if self.teleporting:
            dur = cfg("tele_ms")
            prog = (now - self.tp_start) / dur
            if prog < 0.5:
                self.image.set_alpha(int(255 * (1 - prog * 2)))
            else:
                if self.image.get_alpha() != 255:
                    self.rect.center = self.tp_target
                self.image.set_alpha(int(255 * ((prog - 0.5) * 2)))
            if prog >= 1.0:
                self.teleporting = False
                self.image.set_alpha(255)
                self.state = "chase"
            return alarm

        if alarm and self.state == "patrol" and not self.teleporting:
            self.teleporting = True
            self.tp_start = now
            self.tp_target = player.rect.center
            return alarm
        return super().update(player, alarm, emp, walls, panic)


class BomberGuard(NPCGuard):
    """Guard that explodes when the player gets too close."""
    def __init__(self, pos):
        super().__init__(pos)
        self.image.fill(BLACK)
        self.radius = 45
        self.exploding = False
        self.exp_start = 0
        self.cool = 0
        self.killed = False
        self.CHASE_SP *= 0.9

    def update(self, player, alarm, emp, walls, panic):
        now = pygame.time.get_ticks()
        if self.exploding:
            if now - self.exp_start > cfg("bomb_delay"):
                self.exploding = False
                self.cool = now
                if pygame.math.Vector2(player.rect.center).distance_to(self.rect.center) <= self.radius:
                    self.killed = True
            return alarm

        if now - self.cool > cfg("bomb_cd"):
            if pygame.math.Vector2(player.rect.center).distance_to(self.rect.center) <= self.radius and line_of_sight(self.rect.center, player.rect.center, walls):
                self.exploding = True
                self.exp_start = now

        alarm = super().update(player, alarm, emp, walls, panic)
        return alarm

    def draw(self, s):
        blink = self.exploding and ((pygame.time.get_ticks() - self.exp_start) // 100) % 2 == 0
        col = (255, 0, 0, 160) if blink else (255, 255, 255, 80)
        surf = pygame.Surface((self.radius * 2, self.radius * 2), pygame.SRCALPHA)
        pygame.draw.circle(surf, col, (self.radius, self.radius), self.radius)
        s.blit(surf, (self.rect.centerx - self.radius, self.rect.centery - self.radius))
        super().draw(s)

# ------------------------------------------------
# 9) Room & Level
# ------------------------------------------------

def door_rect(side, w, h, thick, dw=40, dh=80):
    if side == "right":
        return pygame.Rect(w - thick - dw, (h - dh) // 2, dw, dh)
    if side == "left":
        return pygame.Rect(thick, (h - dh) // 2, dw, dh)
    if side == "top":
        return pygame.Rect((w - dh) // 2, thick, dh, dw)
    if side == "bottom":
        return pygame.Rect((w - dh) // 2, h - thick - dw, dh, dw)

def opposite(side):
    return {"right": "left", "left": "right", "top": "bottom", "bottom": "top"}[side]


class Room:
    def __init__(self, w, h, guards, idx, total, pl_spawn, back_side=None, next_side=None):
        thick = 15
        self.outer_walls = [pygame.Rect(0, 0, w, thick), pygame.Rect(0, h - thick, w, thick),
                            pygame.Rect(0, 0, thick, h), pygame.Rect(w - thick, 0, thick, h)]
        self.inner_walls = []
        def near_corner(r1, r2, margin=8):
            corners1 = [(r1.left, r1.top), (r1.right, r1.top), (r1.left, r1.bottom), (r1.right, r1.bottom)]
            corners2 = [(r2.left, r2.top), (r2.right, r2.top), (r2.left, r2.bottom), (r2.right, r2.bottom)]
            for c1 in corners1:
                for c2 in corners2:
                    if abs(c1[0] - c2[0]) < margin and abs(c1[1] - c2[1]) < margin:
                        return True
            return False

        door_areas = []
        if next_side:
            door_areas.append(door_rect(next_side, w, h, thick))
        if back_side:
            door_areas.append(door_rect(back_side, w, h, thick))

        for _ in range(int(total * 3 * cfg("obstacles"))):
            for _try in range(50):
                if random.random() < .5:
                    ww, hh = random.randint(100, 300), random.randint(20, 50)
                else:
                    hh, ww = random.randint(100, 300), random.randint(20, 50)
                x = random.randint(50, w - 50 - ww); y = random.randint(50, h - 50 - hh)
                cand = pygame.Rect(x, y, ww, hh)
                if not any(near_corner(cand, ex) for ex in self.inner_walls) and not any(cand.colliderect(dr) for dr in door_areas):
                    self.inner_walls.append(cand)
                    break
        self.doors = pygame.sprite.Group()
        if idx < total - 1 and next_side:
            r = door_rect(next_side, w, h, thick)
            self.doors.add(Door(r.x, r.y, r.width, r.height, "next"))
        if idx > 0 and back_side:
            r = door_rect(back_side, w, h, thick)
            self.doors.add(Door(r.x, r.y, r.width, r.height, "back"))

        self.pl_spawn = pl_spawn
        safe_points = [self.pl_spawn] + [d.rect.center for d in self.doors]

        self.terminals = pygame.sprite.Group(
            *[Terminal(get_valid_position(30, 30, self.inner_walls, w, h)) for _ in range(guards)])

        self.npcs = pygame.sprite.Group()
        special_limit = min(cfg("special"), max(0, guards - 1))
        num_special = random.randint(0, special_limit)
        special_indices = set(random.sample(range(1, guards), k=num_special)) if num_special else set()
        for i in range(guards):
            pos = get_valid_position(30, 30, self.inner_walls, w, h)
            while any(pygame.math.Vector2(pos).distance_to(sp) < cfg("safe") for sp in safe_points):
                pos = get_valid_position(30, 30, self.inner_walls, w, h)
            if i == 0:
                g = NPCGuard(pos)
            else:
                choices = []
                if guard_opts["fake"]:
                    choices.append("fake")
                if guard_opts["teleport"]:
                    choices.append("tele")
                if guard_opts["bomber"]:
                    choices.append("bomb")
                if choices and i in special_indices:
                    kind = random.choice(choices)
                    if kind == "fake":
                        g = FakeGuard(pos, self.terminals)
                    elif kind == "tele":
                        g = TeleportGuard(pos)
                    else:
                        g = BomberGuard(pos)
                else:
                    g = NPCGuard(pos)
            self.npcs.add(g)

        self.cameras = pygame.sprite.Group()
        for _ in range(random.randint(1, 3)):
            cpos = get_valid_position(20, 20, self.inner_walls, w, h)
            while any(pygame.math.Vector2(cpos).distance_to(sp) < cfg("safe") for sp in safe_points):
                cpos = get_valid_position(20, 20, self.inner_walls, w, h)
            self.cameras.add(Camera(cpos))

        self.bullets = pygame.sprite.Group()
        self.alarm = False; self.alarm_t = 0
        self.width = w; self.height = h

    def respawn_guards(self):
        """Teleport all guards to new random positions away from doors."""
        safe_points = [self.pl_spawn] + [d.rect.center for d in self.doors]
        for g in self.npcs:
            pos = get_valid_position(30, 30, self.inner_walls, self.width, self.height)
            while any(pygame.math.Vector2(pos).distance_to(sp) < cfg("safe") for sp in safe_points):
                pos = get_valid_position(30, 30, self.inner_walls, self.width, self.height)
            g.rect.center = pos
            g.state = "patrol"
            g.dir = g._rand_dir()
            g.path = []
            g.idx = 0
            if isinstance(g, TeleportGuard):
                g.teleporting = False
                g.image.set_alpha(255)
            if isinstance(g, BomberGuard):
                g.exploding = False
                g.killed = False
                g.cool = 0
            if isinstance(g, FakeGuard):
                g.wait = 0

    def update(self, player, emp):
        all_walls = self.outer_walls + self.inner_walls
        guard_walls = self.inner_walls
        for t in self.terminals:
            t.update()
        for c in self.cameras:
            c.update(emp)
            if not emp and c.detect(player, all_walls):
                self.alarm = True; self.alarm_t = pygame.time.get_ticks()
        dead = False
        for g in self.npcs:
            before = self.alarm
            self.alarm = g.update(player, self.alarm, emp, guard_walls, self.alarm) or self.alarm
            if not before and self.alarm:
                self.alarm_t = pygame.time.get_ticks()
            if isinstance(g, BomberGuard) and g.killed:
                dead = True
                g.killed = False
        self.bullets.update()
        for b in list(self.bullets):
            if any(b.rect.colliderect(w) for w in all_walls):
                b.kill()
            hit = pygame.sprite.spritecollideany(b, self.npcs)
            if hit:
                hit.stun = True; hit.stun_t = pygame.time.get_ticks(); hit.image.fill(GRAY); b.kill()
        if self.alarm and pygame.time.get_ticks() - self.alarm_t > CHASE_TIMEOUT:
            self.alarm = False
        return dead

    def draw(self, s):
        for r in self.outer_walls + self.inner_walls:
            pygame.draw.rect(s, BLACK, r)
        for obj in (*self.terminals, *self.npcs, *self.cameras, *self.bullets):
            if isinstance(obj, Camera):
                obj.draw(s, self.outer_walls + self.inner_walls)
            else:
                obj.draw(s)
        for d in self.doors:
            d.draw(s)


class Level:
    def __init__(self, n):
        self.n = n
        self.width = min(BASE_W + (n - 1) * 100, MAX_W)
        self.height = min(BASE_H + (n - 1) * 50, MAX_H)
        if n <= 5:
            total_rooms = n
        else:
            total_rooms = random.randint(5, 7)
        guards = n + cfg("guard_offset")

        def make_sides(cnt):
            sides = []
            prev = None
            for _ in range(cnt):
                opts = ["left", "right", "top", "bottom"]
                if prev:
                    opp = opposite(prev)
                    if opp in opts:
                        opts.remove(opp)
                side = random.choice(opts)
                sides.append(side)
                prev = side
            return sides

        needed = max(0, total_rooms - 1)
        door_sides = make_sides(needed)
        while len(door_sides) < needed:
            door_sides += make_sides(needed - len(door_sides))

        tmp = Room(self.width, self.height, guards, 0, total_rooms, (0, 0), None,
                   door_sides[0] if door_sides else None)
        spawn = get_player_spawn(tmp)
        self.rooms = []
        for i in range(total_rooms):
            back = opposite(door_sides[i - 1]) if i > 0 else None
            nxt = door_sides[i] if i < total_rooms - 1 else None
            self.rooms.append(Room(self.width, self.height, guards, i, total_rooms, spawn, back, nxt))
        self.cur = 0

    def update(self, player, emp):
        return self.rooms[self.cur].update(player, emp)

    def draw(self, s):
        self.rooms[self.cur].draw(s)

    def all_hacked(self):
        return all(t.hacked for r in self.rooms for t in r.terminals)

# ------------------------------------------------
# 10) Mini-Menüs
# ------------------------------------------------

def shop(player, lvl):
    base = {"EMP": 50, "Faster": 30, "Stealth": 40, "Weapon": 60}
    price = {k: base[k] * lvl for k in base}; keys = list(base)
    t = lang_texts[current_language]
    name = {
        "EMP": "EMP",
        "Faster": t.get("faster", "Faster"),
        "Stealth": t.get("stealth", "Stealth"),
        "Weapon": t.get("weapon", "Weapon"),
    }
    scr = pygame.display.get_surface(); font = pygame.font.SysFont(None, 30); clk = pygame.time.Clock()
    pygame.event.clear()
    open_shop = True
    while open_shop:
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if e.type == pygame.KEYDOWN:
                if e.unicode in "1234":
                    k = keys[int(e.unicode) - 1]
                    if k == "Weapon" and player.money >= price[k] and not player.upg["Weapon"]:
                        player.money -= price[k]; player.upg["Weapon"] = True
                        player.ammo = player.ammo_max
                    elif k == "EMP" and player.money >= price[k] and not player.upg["EMP"]:
                        player.money -= price[k]; player.upg["EMP"] = True
                        player.emp_left = player.emp_max
                    elif player.money >= price[k] and not player.upg[k]:
                        player.money -= price[k]; player.upg[k] = True
                if e.key == pygame.K_RETURN:
                    open_shop = False
        scr.fill(WHITE); y = 80
        for i, k in enumerate(keys):
            scr.blit(font.render(f"{i+1}) {name[k]} – {price[k]}", True, BLACK), (50, y)); y += 35
        scr.blit(font.render(f"{t.get('money', 'Money')}: {player.money}", True, BLACK), (50, y + 20))
        pygame.display.flip(); clk.tick(30)
    pygame.event.clear()


def simple_menu(scr, title, options, start=0):
    sel = start
    while True:
        scr.fill(WHITE); draw_txt(scr, title, 50, (50, 40))
        for i, opt in enumerate(options):
            draw_txt(scr, opt, 36, (60, 150 + i * 45), ORANGE if i == sel else BLACK)
        pygame.display.flip()
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if e.type == pygame.KEYDOWN:
                if e.key == pygame.K_UP:
                    sel = (sel - 1) % len(options)
                if e.key == pygame.K_DOWN:
                    sel = (sel + 1) % len(options)
                if e.key == pygame.K_RETURN:
                    return sel
                if e.key == pygame.K_ESCAPE:
                    return len(options) - 1


def show_leader(scr):
    t = lang_texts[current_language]
    while True:
        opts = ["Overall", t["easy"], t["normal"], t["hard"], t["night"], t["back"]]
        sel = simple_menu(scr, t["leader"], opts)
        if sel == len(opts) - 1:
            return
        mode = None if sel == 0 else ["easy", "normal", "hardcore", "nightmare"][sel - 1]
        entries = sorted(load_leaderboard(mode), reverse=True)[:5] or ["---"]
        back = simple_menu(scr, t["leader"], [f"{i+1}. {v}" for i, v in enumerate(entries)] + [t["back"]])
        if back == len(entries):
            continue
        else:
            return


def show_controls(scr):
    t = lang_texts[current_language]
    simple_menu(scr, t["ctrl"], t["controls_text"].split(" | ") + [t["back"]])


def show_shop_info(scr):
    t = lang_texts[current_language]
    simple_menu(scr, t["shopdesc"], t["shop_info"].split(" | ") + [t["back"]])


def settings_menu(scr):
    t = lang_texts[current_language]
    while True:
        opts = [
            f"{t['fake']}: {t['on'] if guard_opts['fake'] else t['off']}",
            f"{t['tele']}: {t['on'] if guard_opts['teleport'] else t['off']}",
            f"{t['bomber']}: {t['on'] if guard_opts['bomber'] else t['off']}",
            t['back']
        ]
        sel = simple_menu(scr, t['settings'], opts)
        if sel == len(opts) - 1:
            return
        if sel == 0:
            guard_opts['fake'] = not guard_opts['fake']
        elif sel == 1:
            guard_opts['teleport'] = not guard_opts['teleport']
        elif sel == 2:
            guard_opts['bomber'] = not guard_opts['bomber']


def lang_menu(scr):
    global current_language
    langs = [("English", "en"), ("Deutsch", "de"), ("Español", "es"), ("Français", "fr"), (lang_texts[current_language]["back"], None)]
    sel = simple_menu(scr, lang_texts[current_language]["lang"], [n for n, _ in langs])
    code = langs[sel][1]
    if code:
        current_language = code
        save_language(current_language)


def difficulty_menu(scr):
    global difficulty_mode
    t = lang_texts[current_language]
    opts = [t["easy"], t["normal"], t["hard"], t["night"], t["back"]]
    sel = simple_menu(scr, t["difficulty"], opts, start=1)
    if sel < 4:
        difficulty_mode = ["easy", "normal", "hardcore", "nightmare"][sel]

def main_menu():
    scr = pygame.display.set_mode((BASE_W, BASE_H))
    while True:
        t = lang_texts[current_language]
        choice = simple_menu(scr, t["title"], [t["start"], t["difficulty"], t["settings"], t["leader"], t["ctrl"], t["shopdesc"], t["lang"], t["quit"]])
        if choice == 0:
            main_game()
        if choice == 1:
            difficulty_menu(scr)
        if choice == 2:
            settings_menu(scr)
        if choice == 3:
            show_leader(scr)
        if choice == 4:
            show_controls(scr)
        if choice == 5:
            show_shop_info(scr)
        if choice == 6:
            lang_menu(scr)
        if choice == 7:
            pygame.quit(); sys.exit()

# ------------------------------------------------
# 11) Hauptspiel
# ------------------------------------------------

def main_game():
    global current_level
    lvl = 1; rooms_done = 0
    current_level = Level(lvl)
    scr = pygame.display.set_mode((current_level.width, current_level.height))
    player = Player(get_player_spawn(current_level.rooms[0]))
    emp = False; emp_t = 0
    clock = pygame.time.Clock(); running = True
    while running:
        dt = clock.tick(FPS)
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                running = False
            elif e.type == pygame.KEYDOWN:
                if e.key == pygame.K_e and player.upg["EMP"] and player.emp_left > 0 and pygame.time.get_ticks() - player.last_emp >= player.emp_cd:
                    emp = True; emp_t = pygame.time.get_ticks()
                    player.emp_left -= 1
                    player.last_emp = emp_t
                if e.key == pygame.K_h:
                    for t in current_level.rooms[current_level.cur].terminals:
                        if player.rect.colliderect(t.rect):
                            t.interact(player)
                if e.key == pygame.K_SPACE and player.upg["Weapon"] and player.ammo > 0 and pygame.time.get_ticks() - player.last_shot >= player.reload_time:
                    vec = pygame.math.Vector2(pygame.mouse.get_pos()) - pygame.math.Vector2(player.rect.center) 
                    current_level.rooms[current_level.cur].bullets.add(Bullet(player.rect.center, vec))
                    player.ammo -= 1
                    player.last_shot = pygame.time.get_ticks()
                if e.key == pygame.K_o:
                    room = current_level.rooms[current_level.cur]
                    for d in room.doors:
                        if player.rect.colliderect(d.rect):
                            # cancel hacking in the room being left
                            for t in room.terminals:
                                if t.hacking and not t.hacked:
                                    t.hacking = False; t.start = 0; t.time = 4000

                            if d.destination == "next" and current_level.cur < len(current_level.rooms) - 1:
                                next_idx = current_level.cur + 1
                                target_room = current_level.rooms[next_idx]
                                spawn_door = next((dd for dd in target_room.doors if dd.destination == "back"), None)
                            elif d.destination == "back" and current_level.cur > 0:
                                next_idx = current_level.cur - 1
                                target_room = current_level.rooms[next_idx]
                                spawn_door = next((dd for dd in target_room.doors if dd.destination == "next"), None)
                            else:
                                next_idx = current_level.cur
                                spawn_door = None

                            room.respawn_guards()
                            current_level.cur = next_idx

                            if spawn_door:
                                player.rect.center = spawn_door.rect.center
                            else:
                                player.rect.center = get_player_spawn(current_level.rooms[current_level.cur])
            elif e.type == pygame.MOUSEBUTTONDOWN and player.upg["Weapon"] and player.ammo > 0 and pygame.time.get_ticks() - player.last_shot >= player.reload_time:
                vec = pygame.math.Vector2(pygame.mouse.get_pos()) - pygame.math.Vector2(player.rect.center) 
                current_level.rooms[current_level.cur].bullets.add(Bullet(player.rect.center, vec))
                player.ammo -= 1
                player.last_shot = pygame.time.get_ticks()
        emp = emp and pygame.time.get_ticks() - emp_t < 2000
        walls = current_level.rooms[current_level.cur].inner_walls
        player.update(pygame.key.get_pressed(), walls)
        dead = current_level.update(player, emp)
        if dead or guard_collides_player(player, current_level.rooms[current_level.cur].npcs):
            running = False
        if current_level.all_hacked():
            rooms_done += current_level.n
            player.money += int(50 * lvl * cfg("reward"))
            player.upg = {k: False for k in player.upg}
            player.ammo = 0; player.emp_left = 0
            if difficulty_mode != "nightmare":
                shop(player, lvl)
            else:
                simple_menu(scr, "", [lang_texts[current_language]["next"]])
            lvl += 1
            current_level = Level(lvl)
            scr = pygame.display.set_mode((current_level.width, current_level.height))
            player.rect.center = get_player_spawn(current_level.rooms[0])
        scr.fill(WHITE); current_level.draw(scr); player.draw(scr)
        draw_txt(scr, f"Lv:{lvl}", 24, (25, 15))
        pygame.display.flip()
    update_leaderboard(rooms_done, difficulty_mode)

# ------------------------------------------------
if __name__ == "__main__":
    main_menu()
