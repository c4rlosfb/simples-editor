#!/usr/bin/env python3
"""
Generate a 2-3 minute demo video for the Simples Editor Web IDE.
Output: docs/demo.mp4
"""

import subprocess, tempfile, os, math, textwrap
from PIL import Image, ImageDraw, ImageFont

W, H = 1920, 1080
FPS = 30

# Colors - dark theme inspired by VS Code
BG = (30, 30, 30)
ACCENT = (86, 156, 214)      # blue
ACCENT2 = (206, 145, 120)    # orange/copper
GREEN = (120, 200, 120)
YELLOW = (220, 200, 80)
WHITE = (240, 240, 240)
GRAY = (160, 160, 160)
DARK = (40, 44, 52)
PANEL = (50, 50, 50)
TERMINAL_BG = (30, 30, 40)
SUCCESS = (80, 200, 120)
RED = (220, 80, 80)

# Try to find a monospace font
FONT_DIRS = [
    "/usr/share/fonts",
    "C:/Windows/Fonts",
    "/System/Library/Fonts",
]
FONT_SIZES = {
    "title": 72,
    "subtitle": 48,
    "heading": 40,
    "body": 32,
    "code": 28,
    "small": 24,
}

def find_font(size=32):
    candidates = []
    # Try system fonts
    for d in FONT_DIRS:
        if os.path.isdir(d):
            for root, dirs, files in os.walk(d):
                for f in files:
                    fp = os.path.join(root, f)
                    if "DejaVuSans-Bold.ttf" in f:
                        candidates.append((fp, "sans-bold"))
                    elif "DejaVuSans.ttf" in f:
                        candidates.append((fp, "sans"))
                    elif "DejaVuSansMono-Bold.ttf" in f:
                        candidates.append((fp, "mono-bold"))
                    elif "DejaVuSansMono.ttf" in f:
                        candidates.append((fp, "mono"))
                    elif "consola.ttf" in f:
                        candidates.append((fp, "mono"))
                    elif "segoeui.ttf" in f:
                        candidates.append((fp, "sans"))
                    elif "segoeuib.ttf" in f:
                        candidates.append((fp, "sans-bold"))
                    elif "arial.ttf" in f:
                        candidates.append((fp, "sans"))
                    elif "CascadiaCode.ttf" in f:
                        candidates.append((fp, "mono"))
    try:
        return ImageFont.truetype(candidates[0][0], size)
    except:
        try:
            if candidates:
                return ImageFont.truetype(candidates[0][0], size)
        except:
            pass
    return ImageFont.load_default()

def get_font(style="sans", size=32):
    """Get font by style name."""
    size = FONT_SIZES.get(size, size) if isinstance(size, str) else size
    try:
        if "mono" in style:
            for d in FONT_DIRS:
                if os.path.isdir(d):
                    for root, dirs, files in os.walk(d):
                        for f in files:
                            if "consola.ttf" in f:
                                return ImageFont.truetype(os.path.join(root, f), size)
                            if "CascadiaCode.ttf" in f:
                                return ImageFont.truetype(os.path.join(root, f), size)
                            if "DejaVuSansMono.ttf" in f:
                                return ImageFont.truetype(os.path.join(root, f), size)
        else:
            for d in FONT_DIRS:
                if os.path.isdir(d):
                    for root, dirs, files in os.walk(d):
                        for f in files:
                            if "segoeui.ttf" in f:
                                return ImageFont.truetype(os.path.join(root, f), size)
                            num = "b" if "bold" in style else ""
                            if f"segoeui{num}.ttf" in f or (num == "" and f == "segoeui.ttf"):
                                return ImageFont.truetype(os.path.join(root, f), size)
                            if "DejaVuSans" in f and ("Bold" in f if "bold" in style else "Bold" not in f):
                                return ImageFont.truetype(os.path.join(root, f), size)
                            if "arial.ttf" in f and "bold" not in style.lower():
                                return ImageFont.truetype(os.path.join(root, f), size)
    except:
        pass
    return ImageFont.load_default()

def draw_text_centered(draw, text, y, font_style="sans", font_size="heading", color=WHITE, max_width=1600):
    """Draw centered text with word wrap."""
    font = get_font(font_style, font_size)
    lines = []
    for paragraph in text.split('\n'):
        words = paragraph.split()
        current = ""
        for w in words:
            test = current + " " + w if current else w
            bb = draw.textbbox((0, 0), test, font=font)
            if bb[2] - bb[0] <= max_width:
                current = test
            else:
                lines.append(current)
                current = w
        if current:
            lines.append(current)
    
    total_h = len(lines) * (font_size + 8) if isinstance(font_size, int) else len(lines) * 44
    start_y = y - total_h // 2
    
    for line in lines:
        bb = draw.textbbox((0, 0), line, font=font)
        tw = bb[2] - bb[0]
        x = (W - tw) // 2
        draw.text((x, start_y), line, font=font, fill=color)
        start_y += (font_size + 8) if isinstance(font_size, int) else 44

def draw_code_block(draw, x, y, code_lines, width=800, line_height=36):
    """Draw a code block with line numbers."""
    font = get_font("mono", "code")
    # Background
    block_h = len(code_lines) * line_height + 20
    draw.rectangle([x, y, x + width, y + block_h], fill=(25, 25, 35), outline=(60, 60, 70))
    
    for i, line in enumerate(code_lines):
        text_y = y + 10 + i * line_height
        
        # Line number
        ln = str(i + 1).rjust(2)
        draw.text((x + 10, text_y), ln, font=font, fill=(100, 100, 110))
        
        # Code with basic highlighting
        rest_x = x + 50
        if line.startswith("programa") or line.startswith("fim."):
            draw.text((rest_x, text_y), line, font=font, fill=ACCENT)
        elif "leia" in line:
            draw.text((rest_x, text_y), line, font=font, fill=GREEN)
        elif "escreva" in line:
            draw.text((rest_x, text_y), line, font=font, fill=YELLOW)
        elif "se " in line or "entao" in line or "senao" in line or "fimse" in line:
            draw.text((rest_x, text_y), line, font=font, fill=(200, 150, 200))
        elif "enquanto" in line or "fimenquanto" in line:
            draw.text((rest_x, text_y), line, font=font, fill=(100, 180, 200))
        else:
            draw.text((rest_x, text_y), line, font=font, fill=WHITE)

def draw_panel(draw, x, y, w, h, title, bg=PANEL):
    """Draw a panel with title bar."""
    draw.rectangle([x, y, x + w, y + h], fill=bg, outline=(60, 60, 70))
    draw.rectangle([x, y, x + w, y + 28], fill=(60, 60, 70))
    font_small = get_font("sans", 18)
    draw.text((x + 8, y + 5), title, font=font_small, fill=GRAY)

def draw_terminal(draw, x, y, w, h, lines, prompt="$"):
    """Draw terminal output."""
    draw.rectangle([x, y, x + w, y + h], fill=TERMINAL_BG, outline=(60, 60, 70))
    font = get_font("mono", 22)
    for i, line in enumerate(lines):
        ty = y + 10 + i * 26
        if line.startswith(prompt):
            draw.text((x + 10, ty), line, font=font, fill=GREEN)
        else:
            draw.text((x + 10, ty), line, font=font, fill=WHITE)

def make_frame(scene_num, duration_sec, total_frames_start):
    """Generate a single animation frame based on scene number and progress."""
    img = Image.new("RGB", (W, H), BG)
    draw = ImageDraw.Draw(img)
    
    # --- Subtle gradient header ---
    for i in range(4):
        draw.rectangle([0, i, W, i], fill=(35 + i * 2, 35 + i * 2, 40 + i * 2))
    
    # Decorative line
    draw.rectangle([0, 4, W, 4], fill=ACCENT)
    
    # --- SCENES ---
    
    # SCENE 1: Title Screen (0-8s)
    if scene_num == 1:
        # Big logo area
        draw.rectangle([W//2 - 200, 150, W//2 + 200, 154], fill=ACCENT)
        
        draw_text_centered(draw, "Simples Editor", 280, "sans-bold", 80, WHITE)
        draw_text_centered(draw, "Web IDE para a Linguagem SIMPLES", 340, "sans", 36, GRAY)
        
        draw_text_centered(draw, 
            "Compile e execute programas SIMPLES diretamente no navegador\n"
            "sem nenhuma instalação local",
            420, "sans", 28, GRAY)
        
        # Feature badges
        badges = ["Monaco Editor", "NASM Viewer", "Terminal Interativo", "Sandbox Seguro"]
        bx = W//2 - 450
        for b in badges:
            bb = draw.textbbox((0, 0), b, font=get_font("sans", 22))
            bw = bb[2] - bb[0] + 30
            draw.rectangle([bx, 500, bx + bw, 540], fill=DARK, outline=ACCENT)
            draw.text((bx + 15, 508), b, font=get_font("sans", 22), fill=ACCENT)
            bx += bw + 20
        
        draw_text_centered(draw, "IFSULDEMINAS — Campus Poços de Caldas", 650, "sans", 24, (100,100,100))
        draw_text_centered(draw, "Disciplina de Compiladores", 685, "sans", 22, (80,80,80))
        
    # SCENE 2: Architecture Overview (8-20s)
    elif scene_num == 2:
        draw_text_centered(draw, "Arquitetura", 80, "sans-bold", 48, WHITE)
        
        # Three boxes with arrows
        boxes = [
            ("Frontend", "React + Monaco + xterm.js", 120, 180),
            ("Backend", "Flask + simplesc + NASM + LD", 120, 480),
            ("Sandbox", "Docker isolado (qemu-user-static)", 120, 780),
        ]
        
        for title, desc, x, y in boxes:
            # Box
            draw.rectangle([x, y, x + 400, y + 200], fill=DARK, outline=ACCENT)
            draw.rectangle([x, y, x + 400, y + 40], fill=(60, 60, 80))
            draw.text((x + 15, y + 8), title, font=get_font("sans-bold", 24), fill=WHITE)
            
            # Description lines
            for i, d in enumerate(desc.split(" + ")):
                draw.text((x + 15, y + 55 + i * 35), f"• {d}", font=get_font("sans", 22), fill=GRAY)
        
        # Arrow from Frontend to Backend
        for yy in [280, 380]:
            draw.line([520, yy, 520, yy + 100], fill=ACCENT, width=3)
            draw.polygon([(515, yy + 100), (525, yy + 100), (520, yy + 115)], fill=ACCENT)
        
        # Arrow from Backend to Sandbox
        for yy in [580, 680]:
            draw.line([520, yy, 520, yy + 100], fill=ACCENT, width=3)
            draw.polygon([(515, yy + 100), (525, yy + 100), (520, yy + 115)], fill=ACCENT)
        
        # Right side: flow description
        flow_y = 180
        flow_steps = [
            ("1", "Usuário escreve código SIMPLES no Monaco Editor"),
            ("2", "Backend compila com simplesc → NASM → LD"),
            ("3", "Binário executado em sandbox Docker isolado"),
            ("4", "Saída exibida no terminal interativo (xterm.js)"),
        ]
        dx = 600
        for num, desc in flow_steps:
            draw.ellipse([dx, flow_y, dx + 30, flow_y + 30], fill=ACCENT)
            draw.text((dx + 8, flow_y + 3), num, font=get_font("sans-bold", 18), fill=BG)
            draw_text_centered(draw, desc, flow_y + 70, "sans", 22, GRAY, max_width=700)
            flow_y += 175
            
    # SCENE 3: Three-Panel Layout (20-35s)
    elif scene_num == 3:
        draw_text_centered(draw, "Layout de Três Painéis", 50, "sans-bold", 42, WHITE)
        
        # Monaco Editor panel (left)
        draw_panel(draw, 30, 100, 680, 500, "Editor SIMPLES (Monaco)")
        code_lines = [
            "programa exemplo;",
            "    x: inteiro;",
            "    y: inteiro;",
            "inicio",
            '    escreva("Digite um numero: ");',
            "    leia(x);",
            "    y <- x * 2;",
            '    escreva("Dobro: ", y);',
            "fim.",
        ]
        draw_code_block(draw, 40, 135, code_lines, width=660, line_height=34)
        
        # NASM panel (right)
        draw_panel(draw, 730, 100, 550, 500, "NASM x86 (Assembly)")
        nasm_lines = [
            "section .data",
            "    msg db 'Digite um numero: ', 0",
            "section .bss",
            "    x resb 4",
            "section .text",
            "    global _start",
            "_start:",
            "    mov eax, 4",
            "    mov ebx, 1",
            "    mov ecx, msg",
            "    int 0x80",
        ]
        draw_code_block(draw, 740, 135, nasm_lines, width=530, line_height=34)
        
        # Terminal panel (bottom)
        draw_panel(draw, 30, 620, 1250, 300, "Terminal (xterm.js)")
        term_lines = [
            "$ Digite um numero: 5",
            "Dobro: 10",
            "$ Programa finalizado com codigo 0",
        ]
        draw_terminal(draw, 40, 655, 1230, 255, term_lines)
        
        # Labels
        labels = [
            ("Editor SIMPLES", 300, 85, ACCENT),
            ("NASM Assembly", 920, 85, ACCENT2),
            ("Terminal Interativo", 550, 610, GREEN),
        ]
        for txt, lx, ly, color in labels:
            bb = draw.textbbox((0, 0), txt, font=get_font("sans", 18))
            tw = bb[2] - bb[0]
            draw.rectangle([lx - tw//2 - 8, ly - 2, lx + tw//2 + 8, ly + 22], fill=BG)
            draw.text((lx - tw//2, ly), txt, font=get_font("sans", 18), fill=color)

    # SCENE 4: SIMPLES Language Features (35-50s)
    elif scene_num == 4:
        draw_text_centered(draw, "Linguagem SIMPLES", 60, "sans-bold", 44, WHITE)
        
        features = [
            ("27 palavras reservadas", "programa, inicio, fim, inteiro, flutuante, vazio,\nleia, escreva, escreval, se, entao, senao, fimse,\nenquanto, fimenquanto, para, de, ate, passo, faca, fimpara,\ne, ou, nao, div, procedimento, retorna"),
            ("Tipos de Dados", "inteiro, flutuante, vazio\nSuporta vetores e registros"),
            ("Controle de Fluxo", "se...entao...senao\nenquanto...faca\nate\npara...faca"),
            ("E/S", 'leia(variavel)\nescreva("texto", valor)'),
        ]
        
        fy = 110
        cols = 2
        for i, (title, desc) in enumerate(features):
            col = i % cols
            row = i // cols
            bx = 60 + col * 900
            by = fy + row * 280
            
            # Feature card
            draw.rectangle([bx, by, bx + 840, by + 250], fill=DARK, outline=(60, 60, 70))
            draw.rectangle([bx, by, bx + 840, by + 40], fill=(60, 60, 80))
            draw.text((bx + 15, by + 8), title, font=get_font("sans-bold", 24), fill=ACCENT)
            
            for j, line in enumerate(desc.split('\n')):
                color = GRAY if not line.startswith("programa") else ACCENT
                draw.text((bx + 20, by + 55 + j * 30), line, font=get_font("sans", 20), fill=color)

    # SCENE 5: Compilation Pipeline (50-65s)
    elif scene_num == 5:
        draw_text_centered(draw, "Pipeline de Compilação", 60, "sans-bold", 44, WHITE)
        
        pipeline_steps = [
            ("simplesc", "Código\nSIMPLES", "→", ACCENT),
            ("nasm", "Assembly\nNASM x86", "→", ACCENT2),
            ("ld", "Binário\nExecutável", "→", GREEN),
            ("Docker", "Sandbox\nIsolado", "✓", SUCCESS),
        ]
        
        start_x = 100
        box_w = 300
        box_h = 180
        gap = 70
        
        for i, (name, desc, arrow, color) in enumerate(pipeline_steps):
            x = start_x + i * (box_w + gap + 60)
            
            # Box
            draw.rectangle([x, 350, x + box_w, 350 + box_h], fill=DARK, outline=color)
            draw.rectangle([x, 350, x + box_w, 350 + 40], fill=(60, 60, 80))
            draw.text((x + 15, 358), name, font=get_font("sans-bold", 26), fill=color)
            
            for j, d in enumerate(desc.split('\n')):
                draw.text((x + 20, 405 + j * 30), d, font=get_font("sans", 20), fill=GRAY)
            
            # Arrow
            if i < len(pipeline_steps) - 1:
                ax = x + box_w + 15
                ay = 440
                draw.line([ax, ay, ax + 30, ay], fill=color, width=3)
                draw.polygon([(ax + 30, ay - 6), (ax + 30, ay + 6), (ax + 40, ay)], fill=color)
        
        # Error handling note
        draw_text_centered(draw, "Erros de compilação são parseados em {linha, coluna, mensagem}\ne exibidos como marcadores vermelhos no editor (Monaco markers)",
            650, "sans", 22, GRAY)
        draw_text_centered(draw, "Timeouts aplicados: 15s para compilação, 10s para execução",
            690, "sans", 22, GRAY)

    # SCENE 6: Interactive Features (65-80s)
    elif scene_num == 6:
        draw_text_centered(draw, "Execução Interativa", 60, "sans-bold", 44, WHITE)
        
        # Left: Code
        draw_panel(draw, 50, 120, 600, 500, "Código SIMPLES")
        code = [
            "programa soma;",
            "    a, b, soma: inteiro;",
            "inicio",
            '    escreva("Valor de a: ");',
            "    leia(a);",
            '    escreva("Valor de b: ");',
            "    leia(b);",
            "    soma <- a + b;",
            '    escreva("Soma: ", soma);',
            "fim.",
        ]
        draw_code_block(draw, 60, 155, code, width=580, line_height=34)
        
        # Right top: Terminal
        draw_panel(draw, 700, 120, 600, 250, "Terminal (xterm.js)")
        term = [
            "$ Valor de a: 10",
            "$ Valor de b: 20",
            "Soma: 30",
        ]
        draw_terminal(draw, 710, 155, 580, 205, term)
        
        # Right bottom: Features list
        draw_panel(draw, 700, 390, 600, 230, "Recursos Interativos")
        features = [
            "• WebSocket bidirecional",
            "• stdin/stdout em tempo real",
            "• Botão Stop (SIGTERM → SIGKILL)",
            "• Suporte a entrada interativa (leia)",
            "• Saída colorida no terminal",
        ]
        for i, f in enumerate(features):
            draw.text((720, 425 + i * 35), f, font=get_font("sans", 22), fill=GREEN if i > 2 else WHITE)
        
        # Flow arrows
        draw.line([650, 300, 700, 250], fill=ACCENT, width=2)
        draw.text((660, 280), "WebSocket", font=get_font("sans", 16), fill=ACCENT)

    # SCENE 7: Security & Features (80-95s)
    elif scene_num == 7:
        draw_text_centered(draw, "Segurança e Observabilidade", 60, "sans-bold", 44, WHITE)
        
        sec_features = [
            ("🔒", "Sandbox Docker", "--cap-drop=ALL, --read-only, --network=none"),
            ("⏱", "Rate Limit", "30 execuções/minuto por usuário"),
            ("📊", "Métricas", "Prometheus em /metrics"),
            ("📋", "Logs Estruturados", "JSON com structlog"),
            ("🛑", "Hard Stop", "--stop-timeout=12, SIGTERM → SIGKILL"),
            ("🔍", "Auditoria", "Tentativas de escape documentadas"),
        ]
        
        start_y = 130
        for i, (icon, title, desc) in enumerate(sec_features):
            col = i % 3
            row = i // 3
            bx = 100 + col * 580
            by = start_y + row * 280
            
            # Card
            draw.rectangle([bx, by, bx + 520, by + 230], fill=DARK, outline=(60, 60, 70))
            
            # Icon circle
            draw.ellipse([bx + 30, by + 30, bx + 90, by + 90], fill=(50, 50, 60))
            draw.text((bx + 42, by + 40), icon, font=get_font("sans", 36), fill=WHITE)
            
            draw.text((bx + 110, by + 40), title, font=get_font("sans-bold", 28), fill=ACCENT)
            draw.text((bx + 110, by + 85), desc, font=get_font("sans-mono", 20), fill=GRAY)
            
            # Checkmark
            draw.text((bx + 460, by + 170), "✓", font=get_font("sans-bold", 28), fill=SUCCESS)

    # SCENE 8: Tech Stack (95-110s)
    elif scene_num == 8:
        draw_text_centered(draw, "Stack Tecnológica", 60, "sans-bold", 44, WHITE)
        
        stacks = {
            "Frontend": [
                "React + TanStack Start",
                "Monaco Editor (Code)",
                "xterm.js (Terminal)",
                "Tailwind CSS",
                "react-resizable-panels",
            ],
            "Backend": [
                "Python / Flask",
                "flask-sock (WebSocket)",
                "Gunicorn + gevent",
                "structlog (logging)",
                "Prometheus client",
            ],
            "DevOps": [
                "Docker Compose",
                "Nginx (reverse proxy)",
                "Supabase (Auth)",
                "Oracle Cloud (OCI)",
                "TLS (certbot)",
            ],
        }
        
        col_x = [100, 720, 1340]
        for idx, (title, items) in enumerate(stacks.items()):
            x = col_x[idx]
            w = 560
            
            # Header
            draw.rectangle([x, 130, x + w, 180], fill=(60, 60, 80))
            draw.text((x + 20, 138), title, font=get_font("sans-bold", 32), fill=ACCENT)
            
            # Items
            for i, item in enumerate(items):
                iy = 200 + i * 55
                draw.ellipse([x + 20, iy + 5, x + 32, iy + 17], fill=ACCENT)
                draw.text((x + 45, iy), item, font=get_font("sans", 24), fill=WHITE)
        
        draw_text_centered(draw, "Tudo roda em Docker Compose — docker compose up para começar",
            600, "sans", 26, GRAY)

    # SCENE 9: Closing (110-125s)
    elif scene_num == 9:
        # Gradient background for closing
        draw.rectangle([0, 0, W, H], fill=(25, 28, 36))
        draw.rectangle([W//2 - 300, 250, W//2 + 300, 254], fill=ACCENT)
        
        draw_text_centered(draw, "Simples Editor", 340, "sans-bold", 64, WHITE)
        draw_text_centered(draw, "Web IDE • Compiladores • IFSULDEMINAS", 400, "sans", 28, GRAY)
        
        draw_text_centered(draw, 
            "✅ Três painéis integrados (Editor + NASM + Terminal)\n"
            "✅ Compilação completa: simplesc → nasm → ld\n"
            "✅ Execução interativa com sandbox Docker\n"
            "✅ Autenticação via Supabase\n"
            "✅ Observabilidade com métricas e logs estruturados",
            530, "sans", 26, WHITE)
        
        draw_text_centered(draw, "Obrigado!", 750, "sans-bold", 48, ACCENT)
        draw_text_centered(draw, "github.com/c4rlosfb/simples-editor", 810, "sans", 24, GRAY)
    
    return img


def create_video():
    """Main function to create the demo video."""
    print("Creating demo video frames...")
    
    # Scene definitions: (scene_num, duration_seconds)
    scenes = [
        (1, 8),    # Title
        (2, 12),   # Architecture
        (3, 15),   # Three-panel layout
        (4, 15),   # SIMPLES Language
        (5, 15),   # Compilation pipeline
        (6, 15),   # Interactive execution
        (7, 15),   # Security & features
        (8, 15),   # Tech stack
        (9, 15),   # Closing
    ]
    
    total_frames = sum(dur * FPS for _, dur in scenes)
    total_duration = total_frames / FPS
    print(f"Total duration: {total_duration:.1f}s ({total_frames} frames)")
    
    # Create temp directory for frames
    with tempfile.TemporaryDirectory() as tmpdir:
        frame_count = 0
        for scene_num, duration in scenes:
            num_frames = int(duration * FPS)
            for i in range(num_frames):
                img = make_frame(scene_num, duration, frame_count)
                frame_path = os.path.join(tmpdir, f"frame_{frame_count:06d}.png")
                img.save(frame_path)
                frame_count += 1
                if frame_count % 30 == 0:
                    print(f"  Generated {frame_count}/{total_frames} frames...")
        
        print(f"All {frame_count} frames generated. Assembling video with ffmpeg...")
        
        output_path = os.path.join(os.path.dirname(__file__), "docs", "demo.mp4")
        
        cmd = [
            "ffmpeg", "-y",
            "-framerate", str(FPS),
            "-i", os.path.join(tmpdir, "frame_%06d.png"),
            "-c:v", "libx264",
            "-preset", "medium",
            "-crf", "23",
            "-pix_fmt", "yuv420p",
            "-vf", "fps=30",
            output_path
        ]
        
        subprocess.run(cmd, check=True, capture_output=True)
        print(f"Video created: {output_path}")
        
        # Check file size
        size = os.path.getsize(output_path)
        print(f"File size: {size / 1024 / 1024:.1f} MB")
        
        return output_path


if __name__ == "__main__":
    path = create_video()
    print(f"\nDemo video ready at: {path}")
