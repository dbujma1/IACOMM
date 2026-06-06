import pygame
import random
import cv2
import time
import os
import pygame_menu
from detectar_letra import detectar_letra, detectar_letra_con_confianza
from pathlib import Path

current_dir = Path(__file__).resolve().parent

# ---------------------------------------------------------------------------
# Inicializar Pygame
# ---------------------------------------------------------------------------
pygame.init()
info = pygame.display.Info()
WIDTH, HEIGHT = info.current_w, info.current_h
screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.FULLSCREEN | pygame.SCALED)
pygame.display.set_caption("Sordolingo")

# Inicializar cámara
cap = cv2.VideoCapture(0)

# Letras posibles (vocales)
letras = ['A', 'E', 'I', 'O', 'U']

# ---------------------------------------------------------------------------
# Estilos
# ---------------------------------------------------------------------------
font_large  = pygame.font.SysFont(None, 120)
font_medium = pygame.font.SysFont(None, 80)
font_small  = pygame.font.SysFont(None, 50)
font_tiny   = pygame.font.SysFont(None, 36)

WHITE       = (255, 255, 255)
BLACK       = (0,   0,   0)
GREEN       = (0,   200, 80)
RED         = (220, 50,  50)
LIGHT_RED   = (255, 200, 200)
PURPLE      = (100, 0,   160)
LIGHT_PURPLE= (230, 210, 255)
GRAY        = (180, 180, 180)
DARK_GRAY   = (80,  80,  80)
YELLOW      = (255, 210, 0)
BLUE        = (30,  100, 220)

# ---------------------------------------------------------------------------
# Audio e imágenes
# ---------------------------------------------------------------------------
pygame.mixer.music.load(str(current_dir / 'musica.mp3'))
pygame.mixer.music.play(-1, 0.0)

sonido_acierto  = pygame.mixer.Sound(str(current_dir / "correct-this-is.mp3"))
sonido_fallo    = pygame.mixer.Sound(str(current_dir / "pacman-dies.mp3"))
sonido_victoria = pygame.mixer.Sound(str(current_dir / "victory-sonic.mp3"))

# Imágenes
imagenes_path = current_dir / "Imagenes"

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def mostrar_texto(texto, fuente, color, x, y, center=True):
    render = fuente.render(texto, True, color)
    rect = render.get_rect(center=(x, y)) if center else render.get_rect(topleft=(x, y))
    screen.blit(render, rect)
    return rect

def flush_camera(cap, n=5):
    for _ in range(n):
        cap.read()

def cuenta_regresiva(segundos=3):
    for t in range(segundos, 0, -1):
        screen.fill(WHITE)
        mostrar_texto(str(t), font_large, BLACK, WIDTH // 2, HEIGHT // 2)
        pygame.display.flip()
        pygame.time.wait(1000)

def dibujar_barra_confianza(surface, x, y, w, h, valor, color_barra=GREEN):
    """Dibuja una barra de progreso horizontal."""
    pygame.draw.rect(surface, GRAY, (x, y, w, h), border_radius=6)
    fill_w = int(w * max(0.0, min(1.0, valor)))
    if fill_w > 0:
        pygame.draw.rect(surface, color_barra, (x, y, fill_w, h), border_radius=6)
    pygame.draw.rect(surface, DARK_GRAY, (x, y, w, h), 2, border_radius=6)

def frame_a_surface(frame, size=(480, 360)):
    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    surf = pygame.image.frombuffer(frame_rgb.tobytes(), frame_rgb.shape[1::-1], "RGB")
    return pygame.transform.scale(surf, size)

# ---------------------------------------------------------------------------
# MODO 1: Juego de aprendizaje
# ---------------------------------------------------------------------------
def juego_de_aprendizaje():
    for ronda in range(len(letras)):
        letra_objetivo = letras[ronda]
        imagen_path = os.path.join(imagenes_path, f"{letra_objetivo}.jpg")
        imagen_letra = pygame.image.load(imagen_path)
        imagen_letra = pygame.transform.scale(imagen_letra, (480, 360))

        acerto = False
        tiempo_inicial = time.time()

        while not acerto:
            ret, frame = cap.read()
            if not ret:
                break

            frame = cv2.flip(frame, 1)
            letra, confianza = detectar_letra_con_confianza(frame)
            cam_surf = frame_a_surface(frame, (480, 360))

            screen.fill(WHITE)

            # Título
            mostrar_texto(f"Letter  {letra_objetivo}", font_large, BLACK, WIDTH // 2, 60)

            # Imagen referencia (izquierda) y cámara (derecha)
            img_x = WIDTH // 2 - 510
            cam_x = WIDTH // 2 + 30
            img_y = HEIGHT // 2 - 200

            screen.blit(imagen_letra, (img_x, img_y))
            screen.blit(cam_surf,     (cam_x, img_y))

            # Etiquetas
            mostrar_texto("Reference", font_tiny, DARK_GRAY, img_x + 240, img_y - 20)
            mostrar_texto("Your camera", font_tiny, DARK_GRAY, cam_x + 240, img_y - 20)

            # Barra de confianza
            bw = 400
            bx = (WIDTH - bw) // 2
            by = img_y + 380
            dibujar_barra_confianza(screen, bx, by, bw, 28, confianza,
                                    GREEN if letra == letra_objetivo else RED)
            conf_pct = int(confianza * 100)
            mostrar_texto(f"Confidence: {conf_pct}%", font_tiny, DARK_GRAY, WIDTH // 2, by + 40)

            # Letra detectada
            det_color = GREEN if letra == letra_objetivo else RED
            det_text  = letra if letra else "—"
            mostrar_texto(f"Detected: {det_text}", font_medium, det_color, WIDTH // 2, by + 85)

            # Mensaje de éxito
            if letra == letra_objetivo and time.time() - tiempo_inicial >= 3:
                sonido_acierto.play()
                # Overlay semitransparente
                overlay = pygame.Surface((WIDTH, 120), pygame.SRCALPHA)
                overlay.fill((0, 200, 80, 160))
                screen.blit(overlay, (0, HEIGHT // 2 - 60))
                mostrar_texto("✓  Correct!", font_large, WHITE, WIDTH // 2, HEIGHT // 2)
                pygame.display.flip()
                time.sleep(1.5)
                acerto = True

            pygame.display.flip()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    cap.release(); pygame.quit(); return
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    return

        time.sleep(1.5)

    sonido_victoria.play()
    screen.fill(LIGHT_PURPLE)
    fuente_v = pygame.font.SysFont("arialblack", 70)
    mostrar_texto("🎉  YOU MASTERED ALL VOWELS!  🎉", fuente_v, PURPLE,    WIDTH // 2, HEIGHT // 2 - 50)
    mostrar_texto("Congratulations!",               fuente_v, (0, 128, 0), WIDTH // 2, HEIGHT // 2 + 70)
    pygame.display.flip()
    pygame.time.wait(5000)

# ---------------------------------------------------------------------------
# MODO 2: Juego contra el reloj
# ---------------------------------------------------------------------------
def juego_contra_reloj():
    puntuacion      = 0
    tiempo_por_ronda = 6
    rondas           = 5

    for ronda in range(rondas):
        letra_objetivo = random.choice(letras)
        flush_camera(cap, n=15)
        cuenta_regresiva(3)

        inicio_ronda = time.time()
        consec = 0
        ultima = None
        acerto = False

        while time.time() - inicio_ronda < tiempo_por_ronda:
            ret, frame = cap.read()
            if not ret:
                break

            frame = cv2.flip(frame, 1)
            letra, confianza = detectar_letra_con_confianza(frame)
            cam_surf = frame_a_surface(frame, (520, 390))

            if letra == letra_objetivo:
                consec = consec + 1 if letra == ultima else 1
                ultima = letra
                if consec >= 3:
                    sonido_acierto.play()
                    puntuacion += 1
                    acerto = True
                    time.sleep(0.8)
                    break
            else:
                consec = 0
                ultima = None

            screen.fill(WHITE)

            # HUD superior
            mostrar_texto(f"Score: {puntuacion}",        font_medium, BLACK,  WIDTH * 1 // 4, 45)
            mostrar_texto(f"Round {ronda+1}/{rondas}",   font_medium, BLACK,  WIDTH * 2 // 4, 45)
            t_rest = max(0, int(tiempo_por_ronda - (time.time() - inicio_ronda)))
            color_t = RED if t_rest <= 2 else BLACK
            mostrar_texto(f"⏱  {t_rest}s",               font_medium, color_t, WIDTH * 3 // 4, 45)

            # Letra objetivo grande
            col_letra = GREEN if letra == letra_objetivo else PURPLE
            mostrar_texto(letra_objetivo, font_large, col_letra, WIDTH // 2, HEIGHT // 2 - 230)

            # Cámara centrada
            cam_x = (WIDTH - 520) // 2
            cam_y = HEIGHT // 2 - 180
            screen.blit(cam_surf, (cam_x, cam_y))

            # Barra de confianza bajo la cámara
            bw = 520
            bx = cam_x
            by = cam_y + 400
            dibujar_barra_confianza(screen, bx, by, bw, 20, confianza,
                                    GREEN if letra == letra_objetivo else RED)

            # Indicador de racha
            if consec > 0:
                mostrar_texto(f"Hold it! {consec}/3", font_small, YELLOW, WIDTH // 2, by + 40)

            pygame.display.flip()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    cap.release(); pygame.quit(); return
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    return

        if not acerto:
            sonido_fallo.play()
            screen.fill(LIGHT_RED)
            mostrar_texto("Time out!", font_large, RED, WIDTH // 2, HEIGHT // 2)
            pygame.display.flip()
            time.sleep(1.2)

    # Pantalla final
    if puntuacion == rondas:
        sonido_victoria.play()
        screen.fill((230, 255, 200))
        fuente_v = pygame.font.SysFont("arialblack", 70)
        mostrar_texto("🏆  PERFECT GAME!  🏆",          fuente_v, (0, 128, 0), WIDTH // 2, HEIGHT // 2 - 60)
        mostrar_texto("You got all letters right!",      fuente_v, (0, 100, 0), WIDTH // 2, HEIGHT // 2 + 60)
    else:
        screen.fill(WHITE)
        mostrar_texto("Finish!",                         font_large,  BLACK, WIDTH // 2, HEIGHT // 2 - 120)
        mostrar_texto(f"Final score: {puntuacion}/{rondas}", font_medium, BLACK, WIDTH // 2, HEIGHT // 2)
        stars = "⭐" * puntuacion + "☆" * (rondas - puntuacion)
        mostrar_texto(stars,                             font_medium, YELLOW, WIDTH // 2, HEIGHT // 2 + 100)

    pygame.display.flip()
    pygame.time.wait(5000)

# ---------------------------------------------------------------------------
# MODO 3: Escritura de mensajes con lenguaje de signos
# ---------------------------------------------------------------------------
def juego_escritura():
    mensaje       = []
    ultima_letra  = None
    t_ultima      = 0.0
    HOLD_TIME     = 1.0
    MAX_CHARS     = 40

    cooldown      = False
    t_cooldown    = 0.0
    COOLDOWN_TIME = 1.2

    clock = pygame.time.Clock()

    while True:
        dt = clock.tick(30) / 1000.0

        ret, frame = cap.read()
        if not ret:
            continue

        frame = cv2.flip(frame, 1)
        letra, confianza = detectar_letra_con_confianza(frame)
        cam_surf = frame_a_surface(frame, (420, 315))

        ahora = time.time()

        if cooldown:
            if ahora - t_cooldown >= COOLDOWN_TIME:
                cooldown = False
                ultima_letra = None

        if not cooldown:
            if letra and letra == ultima_letra:
                progreso = min(1.0, (ahora - t_ultima) / HOLD_TIME)
                if progreso >= 1.0 and len(mensaje) < MAX_CHARS:
                    mensaje.append(letra)
                    sonido_acierto.play()
                    cooldown   = True
                    t_cooldown = ahora
            elif letra:
                ultima_letra = letra
                t_ultima     = ahora
                progreso     = 0.0
            else:
                ultima_letra = None
                progreso     = 0.0
        else:
            progreso = 1.0

        screen.fill(WHITE)

        mostrar_texto("✍  Sign Writer", font_large, PURPLE, WIDTH // 2, 55)
        mostrar_texto("Hold a vowel 1 s to type it  |  SPACE = space  |  BACKSPACE = delete  |  ENTER = done",
                      font_tiny, DARK_GRAY, WIDTH // 2, 110)

        if letra:
            ref_path = os.path.join(imagenes_path, f"{letra}.jpg")
            if os.path.exists(ref_path):
                ref_img = pygame.image.load(ref_path)
                ref_img = pygame.transform.scale(ref_img, (180, 135))
                screen.blit(ref_img, (30, HEIGHT // 2 - 250))
                mostrar_texto(letra, font_medium, PURPLE, 30 + 90, HEIGHT // 2 - 250 + 155)

        cam_x = WIDTH // 2 - 210
        cam_y = HEIGHT // 2 - 250
        screen.blit(cam_surf, (cam_x, cam_y))

        bw = 420
        bx = cam_x
        by = cam_y + 325
        col_barra = GREEN if not cooldown else YELLOW
        dibujar_barra_confianza(screen, bx, by, bw, 22, progreso if not cooldown else 1.0, col_barra)
        if cooldown:
            mostrar_texto("Added! ✓", font_small, GREEN, cam_x + bw // 2, by + 35)
        elif letra:
            t_restante = HOLD_TIME - (ahora - t_ultima)
            mostrar_texto(f"Hold {letra}: {t_restante:.1f} s", font_small, BLUE, cam_x + bw // 2, by + 35)

        det_text  = letra if letra else "—"
        det_color = GREEN if letra else GRAY
        mostrar_texto(det_text, font_large, det_color, cam_x + bw + 100, cam_y + 100)
        mostrar_texto("Detected", font_tiny, DARK_GRAY, cam_x + bw + 100, cam_y + 50)

        msg_y   = HEIGHT // 2 + 110
        msg_w   = WIDTH - 80
        msg_h   = 90
        pygame.draw.rect(screen, (245, 240, 255), (40, msg_y, msg_w, msg_h), border_radius=12)
        pygame.draw.rect(screen, PURPLE,           (40, msg_y, msg_w, msg_h), 3, border_radius=12)

        cursor = "|" if int(ahora * 2) % 2 == 0 else " "
        texto_msg = "".join(mensaje) + cursor
        fuente_msg = pygame.font.SysFont("Courier New", 52, bold=True)
        render_msg = fuente_msg.render(texto_msg, True, BLACK)
        max_w = msg_w - 30
        if render_msg.get_width() > max_w:
            surface_clip = render_msg.subsurface(
                render_msg.get_width() - max_w, 0, max_w, render_msg.get_height()
            )
            screen.blit(surface_clip, (55, msg_y + (msg_h - render_msg.get_height()) // 2))
        else:
            screen.blit(render_msg, (55, msg_y + (msg_h - render_msg.get_height()) // 2))

        mostrar_texto(f"{len(mensaje)}/{MAX_CHARS}", font_tiny, GRAY, WIDTH - 60, msg_y + msg_h + 18)

        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                cap.release(); pygame.quit(); return

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return
                elif event.key == pygame.K_BACKSPACE:
                    if mensaje:
                        mensaje.pop()
                elif event.key == pygame.K_SPACE:
                    if mensaje and mensaje[-1] != ' ' and len(mensaje) < MAX_CHARS:
                        mensaje.append(' ')
                elif event.key == pygame.K_RETURN:
                    _mostrar_mensaje_final(mensaje)
                    return

def _mostrar_mensaje_final(mensaje):
    texto = "".join(mensaje).strip()
    if not texto:
        texto = "(empty message)"

    sonido_victoria.play()
    screen.fill(LIGHT_PURPLE)

    mostrar_texto("Your message:", font_medium, PURPLE, WIDTH // 2, HEIGHT // 2 - 130)

    box_w = WIDTH - 120
    box_h = 120
    box_x = 60
    box_y = HEIGHT // 2 - 70
    pygame.draw.rect(screen, WHITE,  (box_x, box_y, box_w, box_h), border_radius=16)
    pygame.draw.rect(screen, PURPLE, (box_x, box_y, box_w, box_h), 4, border_radius=16)

    fuente_msg = pygame.font.SysFont("Courier New", 56, bold=True)
    render_msg = fuente_msg.render(texto, True, BLACK)
    mx = box_x + (box_w - render_msg.get_width()) // 2
    my = box_y + (box_h - render_msg.get_height()) // 2
    screen.blit(render_msg, (mx, my))

    mostrar_texto("Press any key to return to menu", font_small, DARK_GRAY, WIDTH // 2, HEIGHT // 2 + 100)
    pygame.display.flip()

    waiting = True
    while waiting:
        for event in pygame.event.get():
            if event.type in (pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN, pygame.QUIT):
                waiting = False

# ---------------------------------------------------------------------------
# Menú principal
# ---------------------------------------------------------------------------

def mostrar_menu():
    from pygame_menu import themes, widgets, baseimage

    ruta_fondo = str(imagenes_path / "fondo.jpg")

    print("Fondo:", ruta_fondo)
    print("Existe:", os.path.exists(ruta_fondo))

    tema = themes.THEME_DARK.copy()

    # --- Para eliminar la barra negra del título ---
    tema.title = False                                      # <-- oculta el título por completo
    tema.title_bar_style = pygame_menu.widgets.MENUBAR_STYLE_NONE  # <-- sin barra de menú

    tema.background_color = baseimage.BaseImage(
        image_path=ruta_fondo,
        drawing_mode=baseimage.IMAGE_MODE_FILL
    )

    tema.widget_background_color = (0, 0, 0, 0)
    tema.widget_font_size = 50
    tema.widget_font_color = WHITE
    tema.title_font_size = 80
    tema.selection_color = YELLOW

    tema.widget_selection_effect = widgets.HighlightSelection(
        border_width=4
    )

    menu = pygame_menu.Menu(
        '',           # título vacío (ya oculto por tema.title = False)
        WIDTH,
        HEIGHT,
        theme=tema
    )

    menu.add.vertical_margin(180)

    menu.add.label(
        "SORDOLINGO",
        font_name=pygame.font.match_font('arialblack'),
        font_size=100,
        font_color=WHITE
    )

    menu.add.vertical_margin(60)

    menu.add.button('▶ Play against the clock', juego_contra_reloj)
    menu.add.button('📖 Learn the vowels', juego_de_aprendizaje)
    menu.add.button('✍ Sign Writer', juego_escritura)

    menu.add.vertical_margin(30)
    menu.add.button('Exit', pygame_menu.events.EXIT)

    menu.mainloop(screen)

# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
mostrar_menu()

cap.release()
cv2.destroyAllWindows()
pygame.quit()