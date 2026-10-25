import pgzrun
#pgzero
import random
import math

cell = Actor("border")
cell1 = Actor("floor")
cell2 = Actor("crack")
cell3 = Actor("bones")

size_w = 9
size_h = 10

WIDTH = cell.width * size_w
HEIGHT = cell.height * size_h

TITLE = "WeCode и Драконы"
FPS = 30

ROOMS = 3
ROOM = 1

mode = "game"
win = 0

# 0 - стена, 1 - пол, 2 - трещины, 3 - кости
my_map = [
    [0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 1, 1, 1, 1, 1, 1, 1, 0],
    [0, 1, 1, 2, 1, 3, 1, 1, 0],
    [0, 1, 1, 1, 2, 1, 1, 1, 0],
    [0, 1, 3, 2, 1, 1, 3, 1, 0],
    [0, 1, 1, 1, 1, 3, 1, 1, 0],
    [0, 1, 1, 3, 1, 1, 2, 1, 0],
    [0, 1, 1, 1, 1, 1, 1, 1, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1]
]

char = Actor("stand")
char.pos = (cell.width * 1.5, cell.height * 1.5)
char.health = 100
char.attack = 5
char.armor = 2
char.has_armor = False
char.armor_equipped = False

# Отдельный актёр для анимации: столкновения всегда остаются на сетке.
char_visual = Actor("stand")
STEP_TIME = 0.18
ATTACK_TIME = 0.34
ARMOR_DEFENCE = 3
motion = None


def reset_motion():
    global motion
    motion = None
    char_visual.image = char.image
    char_visual.pos = char.pos
    char_visual.angle = 0


def take_damage(attack):
    """Броня поглощает часть каждого удара, но минимум 1 урон проходит."""
    damage = max(1, attack - char.armor)
    char.health = max(0, char.health - damage)
    return damage


def finish_turn(attacked_enemy):
    if mode == "game" and char.health > 0:
        if ROOM == ROOMS:
            boss_move()
        else:
            enemies_turn(attacked_enemy)
    check_room_end()


enemies = []
boxes = []
hearts = []
swords = []
armors = []
combat_effects = []

def random_position():
    """Выбирает случайную клетку внутри комнаты."""
    x = random.randint(1, 7) * cell.width + cell.width // 2
    y = random.randint(1, 7) * cell.height + cell.height // 2
    return x, y


def position_is_free(pos, check_enemies=True):
    """Проверяет, свободна ли клетка."""
    test = Actor("floor")
    test.pos = pos

    if test.colliderect(char):
        return False

    for box in boxes:
        if test.colliderect(box):
            return False

    if check_enemies:
        for enemy in enemies:
            if test.colliderect(enemy):
                return False

    return True


def get_free_position(check_enemies=True):
    """Ищет свободную клетку."""
    for _ in range(200):
        pos = random_position()
        if position_is_free(pos, check_enemies):
            return pos

    # Если случайный поиск не помог, проверяем все клетки.
    for row in range(1, 8):
        for column in range(1, 8):
            pos = ((column + 0.5) * cell.width,
                   (row + 0.5) * cell.height)
            if position_is_free(pos, check_enemies):
                return pos
    raise RuntimeError("В комнате нет свободной клетки")


def spawn_room():
    """Создаёт врагов и коробки текущей комнаты."""
    enemies.clear()
    boxes.clear()
    hearts.clear()
    swords.clear()
    armors.clear()
    combat_effects.clear()

    char.pos = (
        cell.width * 1.5,
        cell.height * 1.5
    )
    char.image = "stand"
    reset_motion()

    if ROOM < ROOMS:
        # В первой и второй комнатах 5 врагов
        kinds = ["skeleton", "skeleton", "archer", "runner", "guard"]
        random.shuffle(kinds)
        for kind in kinds:
            enemy = Actor("enemy")
            enemy.kind = kind
            enemy.pos = get_free_position()
            enemy.health = random.randint(10, 20) * ROOM
            enemy.attack = random.randint(5, 10) * ROOM
            enemy.bonus = random.randint(0, 2)
            enemy.armor = 0
            enemy.facing = 1
            if kind == "guard":
                enemy.health += 10 * ROOM
                enemy.attack += 2
            elif kind == "runner":
                enemy.health = 10 * ROOM
                enemy.attack = 4 * ROOM
            elif kind == "archer":
                enemy.attack = 4 * ROOM
            enemies.append(enemy)

    else:
        # В последней комнате ТОЛЬКО ОДИН БОСС
        boss = Actor("boss")
        boss.pos = get_free_position()
        boss.health = 50
        boss.attack = 15
        boss.kind = "boss"
        boss.warning = []
        enemies.append(boss)

    if ROOM == 1:
        next(e for e in enemies if e.kind == "guard").armor = ARMOR_DEFENCE

    # Коробки с гарантированным случайным бонусом
    for _ in range(3):
        box = Actor("box")
        box.pos = get_free_position()
        boxes.append(box)

def map_draw():
    for i in range(len(my_map)):
        for j in range(len(my_map[i])):
            tile = my_map[i][j]

            if tile == -1:
                continue

            if tile == 0:
                tile_actor = cell
            elif tile == 1:
                tile_actor = cell1
            elif tile == 2:
                tile_actor = cell2
            else:
                tile_actor = cell3

            tile_actor.topleft = (
                cell.width * j,
                cell.height * i
            )
            tile_actor.draw()

def draw_armor(pos, size=12):
    """Щит рисуется кодом и остаётся чётким при любом размере."""
    x, y = pos
    points = [(x-size/2, y-size/2), (x+size/2, y-size/2),
              (x+size/2, y+size/6), (x, y+size/2),
              (x-size/2, y+size/6), (x-size/2, y-size/2)]
    for a, b in zip(points, points[1:]):
        screen.draw.line(a, b, "#9fe4ff")
    screen.draw.line((x, y-size/3), (x, y+size/4), "#ecfaff")


def draw_attack():
    if motion is None or not motion["attack"]:
        return
    progress = min(1, motion["elapsed"] / ATTACK_TIME)
    if not 0.15 < progress < 0.9:
        return
    x, y = char_visual.pos
    sx, sy = motion["start"]
    tx, ty = motion["target"]
    direction = math.atan2(ty-sy, tx-sx)
    swing = (progress - 0.15) / 0.75
    angle = direction - 1.1 + swing * 2.2
    # Светлый клинок и короткий золотой след взмаха.
    for i in range(5):
        trail_angle = angle - i * 0.12
        tip = (x + math.cos(trail_angle)*40,
               y + math.sin(trail_angle)*40)
        base = (x + math.cos(trail_angle)*14,
                y + math.sin(trail_angle)*14)
        screen.draw.line(base, tip, "#fff4bd" if i == 0 else "#c99b54")
    if progress >= 0.45:
        radius = int(5 + 12 * (progress - 0.45))
        screen.draw.circle((tx, ty), radius, "#ffe5a1")
        screen.draw.text("-" + str(motion["damage"]),
                         center=(tx, ty-24-(progress-0.45)*20),
                         color="#ffe5a1", fontsize=22)


def draw():
    screen.fill("#202633")

    if mode == "game":
        map_draw()
        draw_combat_zones()

        char_visual.draw()
        if char.armor_equipped:
            draw_armor((char_visual.x-13, char_visual.y+5))

        for enemy in enemies:
            enemy.draw()
            draw_enemy_role(enemy)
            if getattr(enemy, "armor", 0):
                draw_armor((enemy.x-14, enemy.y+5))
            screen.draw.text(
                str(enemy.health),
                center=(enemy.x, enemy.y - enemy.height // 2 - 10),
                color="white",
                fontsize=18
            )

        for box in boxes:
            box.draw()

        for heart in hearts:
            heart.draw()

        for sword in swords:
            sword.draw()

        for armor in armors:
            draw_armor(armor.pos, 28)
        draw_attack()
        if char.has_armor and not char.armor_equipped:
            screen.draw.text("E — надеть броню (+3)", center=(WIDTH/2, 15),
                             color="#9fe4ff", fontsize=20)

        if ROOM < ROOMS:
            screen.draw.text("Л — лучник    >> — быстрый    Т — тяжёлый",
                             center=(WIDTH/2, HEIGHT-cell.height*1.5),
                             color="#d5ddeb", fontsize=17)

        # Панель характеристик
        screen.draw.filled_rect(
            Rect(0, HEIGHT - cell.height, WIDTH, cell.height),
            "#151922"
        )

        screen.draw.text(
            "HP: " + str(max(0, char.health)),
            topleft=(8, HEIGHT - 35),
            color="white",
            fontsize=20
        )

        screen.draw.text(
            "ATK: " + str(char.attack),
            topleft=(100, HEIGHT - 35),
            color="white",
            fontsize=20
        )

        screen.draw.text(
            "Броня: " + str(char.armor),
            topleft=(190, HEIGHT - 35),
            color="#9fc9ee",
            fontsize=20
        )

        screen.draw.text(
            "Комната: " + str(ROOM) + "/" + str(ROOMS),
            topleft=(300, HEIGHT - 35),
            color="white",
            fontsize=18
        )

        if ROOM == ROOMS and not (char.has_armor and not char.armor_equipped):
            screen.draw.text(
                "БОСС: выйди из красной полосы!" if boss_reference() is not None and boss_reference().warning else "БОСС",
                center=(WIDTH // 2, 15),
                color="#ff6973",
                fontsize=20
            )

    elif mode == "end":
        screen.fill("#202633")

        if win == 1:
            screen.draw.text(
                "ПОБЕДА!",
                center=(WIDTH // 2, HEIGHT // 2 - 30),
                color="yellow",
                fontsize=48
            )
            screen.draw.text(
                "Ты победил босса!",
                center=(WIDTH // 2, HEIGHT // 2 + 20),
                color="white",
                fontsize=25
            )
        else:
            screen.draw.text(
                "ПОРАЖЕНИЕ",
                center=(WIDTH // 2, HEIGHT // 2 - 30),
                color="red",
                fontsize=44
            )

        screen.draw.text(
            "Нажми R, чтобы начать заново",
            center=(WIDTH // 2, HEIGHT // 2 + 65),
            color="white",
            fontsize=20
        )

def open_box(box):
    """Каждая коробка обязательно выдаёт случайный бонус."""
    pos = box.pos
    boxes.remove(box)

    if random.choice([True, False]):
        bonus = Actor("heart")
        bonus.pos = pos
        hearts.append(bonus)
    else:
        bonus = Actor("sword")
        bonus.pos = pos
        swords.append(bonus)

def collect_bonuses():
    for heart in hearts[:]:
        if char.colliderect(heart):
            char.health = min(100, char.health + 25)
            hearts.remove(heart)

    for sword in swords[:]:
        if char.colliderect(sword):
            char.attack += 5
            swords.remove(sword)

    for armor in armors[:]:
        if char.colliderect(armor):
            char.has_armor = True
            armors.remove(armor)


def attack_enemy(enemy):
    """Атака игрока при попытке войти в клетку врага."""
    damage = char.attack
    if enemy is not boss_reference():
        # Положение героя уже восстановлено после столкновения.
        if (char.x - enemy.x) * enemy.facing < 0:
            damage *= 2
        if char.x != enemy.x:
            enemy.facing = 1 if char.x > enemy.x else -1
            enemy.image = "enemy" if enemy.facing == 1 else "enemy_left"
    damage = max(1, damage - getattr(enemy, "armor", 0))
    enemy.health -= damage

    # У босса каждый удар проходит только через предупреждение на поле.
    if enemy is not boss_reference():
        take_damage(enemy.attack)

    if enemy.health <= 0:
        if getattr(enemy, "armor", 0) and random.random() < 0.5:
            armor = Actor("floor")  # Только геометрия клетки для подбора.
            armor.pos = enemy.pos
            armors.append(armor)
        # Обычные враги могут оставить бонус
        if enemy in enemies and enemy is not boss_reference():
            if getattr(enemy, "bonus", 0) == 1:
                heart = Actor("heart")
                heart.pos = enemy.pos
                hearts.append(heart)

            elif getattr(enemy, "bonus", 0) == 2:
                sword = Actor("sword")
                sword.pos = enemy.pos
                swords.append(sword)

        if enemy in enemies:
            enemies.remove(enemy)

    return damage


def boss_reference():
    """Возвращает босса только в последней комнате."""
    if ROOM != ROOMS:
        return None

    for enemy in enemies:
        if enemy.image == "boss":
            return enemy

    return None

def inside_room(pos):
    x, y = pos
    return cell.width < x < WIDTH-cell.width and cell.height < y < HEIGHT-2*cell.height


def face_player(enemy):
    if enemy.kind != "boss" and char.x != enemy.x:
        enemy.facing = 1 if char.x > enemy.x else -1
        enemy.image = "enemy" if enemy.facing == 1 else "enemy_left"


def approach_player(enemy, steps):
    """Движение по свободным клеткам, без наложений и прохода через коробки."""
    for _ in range(steps):
        dx, dy = char.x-enemy.x, char.y-enemy.y
        if abs(dx)+abs(dy) <= cell.width:
            break
        directions = [(cell.width if dx > 0 else -cell.width, 0)] if dx else []
        if dy:
            directions.append((0, cell.height if dy > 0 else -cell.height))
        if abs(dy) > abs(dx):
            directions.reverse()
        for step_x, step_y in directions:
            target = (enemy.x+step_x, enemy.y+step_y)
            if (inside_room(target) and target != char.pos
                    and not any(box.pos == target for box in boxes)
                    and not any(other is not enemy and other.pos == target for other in enemies)):
                enemy.pos = target
                face_player(enemy)
                break
        else:
            break


def archer_can_shoot(enemy):
    dx, dy = char.x-enemy.x, char.y-enemy.y
    if dx and dy or abs(dx)+abs(dy) > 5*cell.width:
        return False
    step_x = 0 if not dx else (cell.width if dx > 0 else -cell.width)
    step_y = 0 if not dy else (cell.height if dy > 0 else -cell.height)
    pos = (enemy.x+step_x, enemy.y+step_y)
    while pos != char.pos:
        if any(item.pos == pos for item in boxes+enemies if item is not enemy):
            return False
        pos = (pos[0]+step_x, pos[1]+step_y)
    return True


def enemies_turn(attacked_enemy):
    for enemy in enemies:
        if char.health <= 0:
            break
        # Уже ответивший враг не атакует второй раз за тот же ход.
        if enemy is attacked_enemy:
            continue
        if enemy.kind == "archer" and archer_can_shoot(enemy):
            face_player(enemy)
            take_damage(enemy.attack)
            combat_effects.append({"start": enemy.pos, "end": char.pos, "time": 0.3, "kind": "arrow"})
        elif enemy.kind == "runner":
            if abs(char.x-enemy.x)+abs(char.y-enemy.y) <= cell.width:
                face_player(enemy)
                take_damage(enemy.attack)
            elif abs(char.x-enemy.x)+abs(char.y-enemy.y) <= 4*cell.width:
                approach_player(enemy, 2)


def boss_move():
    """Подготовка и удар занимают разные ходы; зона удара фиксирована."""
    boss = boss_reference()
    if boss is None:
        return
    if boss.warning:
        if char.pos in boss.warning:
            take_damage(boss.attack)
        combat_effects.append({"cells": boss.warning[:], "time": 0.35, "kind": "blast"})
        boss.warning = []
        return
    approach_player(boss, 2)
    if max(abs(char.x-boss.x), abs(char.y-boss.y)) <= 2*cell.width:
        # Полоса фиксируется сейчас: за следующий ход можно уйти в сторону.
        dx, dy = char.x-boss.x, char.y-boss.y
        if abs(dx) >= abs(dy):
            boss.warning = [((col+0.5)*cell.width, char.y) for col in range(1,8)]
        else:
            boss.warning = [(char.x, (row+0.5)*cell.height) for row in range(1,8)]


def draw_combat_zones():
    boss = boss_reference()
    if boss is not None and boss.warning:
        for x, y in boss.warning:
            rect = Rect(x-cell.width/2+3, y-cell.height/2+3, cell.width-6, cell.height-6)
            screen.draw.filled_rect(rect, "#79323b")
            screen.draw.rect(rect, "#ff6973")
            screen.draw.text("!", center=(x,y), color="#ffccaa", fontsize=28)
    for effect in combat_effects:
        if effect["kind"] == "arrow":
            screen.draw.line(effect["start"], effect["end"], "#ffe2a0")
        else:
            for x, y in effect["cells"]:
                screen.draw.filled_rect(Rect(x-22,y-22,44,44), "#d76a38")


def draw_enemy_role(enemy):
    kind = enemy.kind
    labels = {"archer": ("Л", "#a8e4a0"), "runner": (">>", "#ffbd70"),
              "guard": ("Т", "#b3c9ff")}
    if kind in labels:
        label, color = labels[kind]
        screen.draw.text(label, center=(enemy.x+15, enemy.y+17), color=color, fontsize=17)
    if kind == "archer":
        x, y = enemy.x-15, enemy.y
        screen.draw.line((x,y-13), (x-5,y), "#a8e4a0")
        screen.draw.line((x-5,y), (x,y+13), "#a8e4a0")
        screen.draw.line((x,y-13), (x,y+13), "#f0e4bb")
    elif kind == "guard":
        screen.draw.line((enemy.x+16,enemy.y-6), (enemy.x+16,enemy.y+14), "#b3c9ff")
        screen.draw.filled_rect(Rect(enemy.x+10,enemy.y-10,12,7), "#8b9dbf")


def on_key_down(key):
    global ROOM, mode, win, motion

    if mode == "end":
        if key == keys.R:
            restart_game()
        return

    if motion is not None:
        return

    if key == keys.E:
        if char.has_armor and not char.armor_equipped:
            char.armor_equipped = True
            char.armor += ARMOR_DEFENCE
        return

    old_pos = char.pos

    if key == keys.RIGHT:
        char.x += cell.width
        char.image = "stand"

    elif key == keys.LEFT:
        char.x -= cell.width
        char.image = "left"

    elif key == keys.UP:
        char.y -= cell.height

    elif key == keys.DOWN:
        char.y += cell.height

    else:
        return

    # Не разрешаем выходить за стены и в панель интерфейса
    if (
        char.left < cell.width
        or char.right > WIDTH - cell.width
        or char.top < cell.height
        or char.bottom > HEIGHT - cell.height * 2
    ):
        char.pos = old_pos
        return

    target_pos = char.pos

    # Столкновение с врагом
    enemy = char.collidelist(enemies)

    if enemy != -1:
        char.pos = old_pos
        # Урон срабатывает в момент попадания клинка.

    # Открытие коробки
    for box in boxes[:]:
        if char.colliderect(box):
            open_box(box)


    collect_bonuses()

    # Ответ босса и переход комнаты ждут окончания видимого шага.
    char_visual.image = char.image
    motion = {
        "start": old_pos,
        "target": target_pos,
        "attack": enemy != -1,
        "elapsed": 0.0,
        "enemy": enemies[enemy] if enemy != -1 else None,
        "hit": False,
        "damage": 0,
    }


def check_room_end():
    global ROOM, mode, win

    if char.health <= 0:
        char.health = 0
        win = -1
        mode = "end"
        return

    if len(enemies) == 0 and not armors:
        if ROOM >= ROOMS:
            win = 1
            mode = "end"
            return

        ROOM += 1

        # Небольшое восстановление между комнатами
        char.health = min(100, char.health + 25)

        spawn_room()

def restart_game():
    global ROOM, mode, win

    ROOM = 1
    mode = "game"
    win = 0

    char.health = 100
    char.attack = 5
    char.armor = 2
    char.has_armor = False
    char.armor_equipped = False
    char.image = "stand"

    spawn_room()


def update(dt):
    if mode != "game":
        return

    global motion
    for effect in combat_effects[:]:
        effect["time"] -= max(0, dt)
        if effect["time"] <= 0:
            combat_effects.remove(effect)
    if motion is not None:
        motion["elapsed"] += max(0, dt)
        duration = ATTACK_TIME if motion["attack"] else STEP_TIME
        progress = min(1.0, motion["elapsed"] / duration)
        if motion["attack"] and not motion["hit"] and progress >= 0.45:
            motion["damage"] = attack_enemy(motion["enemy"])
            motion["hit"] = True
        # Плавное ускорение и торможение; при атаке — короткий выпад.
        eased = progress * progress * (3 - 2 * progress)
        amount = math.sin(math.pi * progress) * 0.28 if motion["attack"] else eased
        start_x, start_y = motion["start"]
        end_x, end_y = motion["target"]
        char_visual.pos = (
            start_x + (end_x - start_x) * amount,
            start_y + (end_y - start_y) * amount - math.sin(math.pi * progress) * 4,
        )
        char_visual.angle = math.sin(2 * math.pi * progress) * 5
        if progress >= 1:
            attacked_enemy = motion["enemy"]
            reset_motion()
            finish_turn(attacked_enemy)
        return

    collect_bonuses()
    check_room_end()


# Запуск игры
spawn_room()
pgzrun.go()

