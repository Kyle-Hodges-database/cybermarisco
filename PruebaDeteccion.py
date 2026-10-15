from __future__ import print_function
import glob
import numpy as np
import cv2 as cv


# =====================================================================
# 1. DETECTOR DE SELECCIÓN DE CALABAZAS ("ELIJA UNA CALABAZA")
# =====================================================================
def detect_pumpkins(hsv, w, h):
    orange_mask = cv.inRange(hsv, np.array([5, 140, 160]), np.array([26, 255, 255]))
    green_mask = cv.inRange(hsv, np.array([35, 90, 70]), np.array([85, 255, 255]))

    kernel = cv.getStructuringElement(cv.MORPH_ELLIPSE, (5, 5))
    orange_mask = cv.morphologyEx(orange_mask, cv.MORPH_CLOSE, kernel)

    contours, _ = cv.findContours(orange_mask, cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE)
    pumpkins = []

    for cnt in contours:
        x, y, bw, bh = cv.boundingRect(cnt)
        cx, cy = x + bw // 2, y + bh // 2
        rel_x, rel_y = cx / float(w), cy / float(h)

        if not (0.24 <= rel_x <= 0.76 and 0.25 <= rel_y <= 0.82):
            continue
        if not (0.07 * w <= bw <= 0.16 * w and 0.12 * h <= bh <= 0.28 * h):
            continue
        if not (0.70 <= (float(bw) / bh) <= 1.25):
            continue

        stem_roi = green_mask[max(0, int(y - 0.18 * bh)):min(h, int(y + 0.22 * bh)),
                              max(0, int(cx - 0.25 * bw)):min(w, int(cx + 0.25 * bw))]
        if stem_roi.size > 0 and (np.count_nonzero(stem_roi) / float(stem_roi.size)) > 0.08:
            pumpkins.append((cx, cy, int((bw + bh) * 0.26), "TOCAR CALABAZA"))

    if len(pumpkins) >= 3:
        pumpkins.sort(key=lambda p: (p[1], p[0]))
        return pumpkins
    return []


# =====================================================================
# 2. DETECTOR DE BOTÓN DORADO CENTRAL DE BONUS (TRIÁNGULO ROJO '▶')
# =====================================================================
def detect_golden_bonus_button(hsv, w, h):
    x1, y1 = int(w * 0.40), int(h * 0.60)
    x2, y2 = int(w * 0.60), int(h * 0.88)
    roi_hsv = hsv[y1:y2, x1:x2]

    red1 = cv.inRange(roi_hsv, np.array([0, 135, 135]), np.array([10, 255, 255]))
    red2 = cv.inRange(roi_hsv, np.array([170, 135, 135]), np.array([180, 255, 255]))
    red_mask = cv.bitwise_or(red1, red2)
    gold_mask = cv.inRange(roi_hsv, np.array([14, 100, 120]), np.array([35, 255, 255]))

    contours, _ = cv.findContours(red_mask, cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE)
    for cnt in contours:
        area = cv.contourArea(cnt)
        if not (0.0004 * w * h <= area <= 0.004 * w * h):
            continue

        approx = cv.approxPolyDP(cnt, 0.04 * cv.arcLength(cnt, True), True)
        if 3 <= len(approx) <= 5 and cv.isContourConvex(approx):
            (rcx, rcy), r_tri = cv.minEnclosingCircle(cnt)
            rcx, rcy, r_tri = int(rcx), int(rcy), max(2, int(r_tri))

            yy, xx = np.indices(roi_hsv.shape[:2])
            dist = np.hypot(xx - rcx, yy - rcy)
            ring_gold = (dist >= r_tri * 1.05) & (dist <= r_tri * 2.2)

            if np.any(ring_gold):
                if (np.count_nonzero(gold_mask[ring_gold]) / float(np.count_nonzero(ring_gold))) > 0.50:
                    return [(x1 + rcx, y1 + rcy, int(r_tri * 2.1), "BOTON BONUS DORADO")]
    return []


# =====================================================================
# 3. DETECTOR DE PANTALLA DE CARGA CENTRAL (BOTÓN '>' SOBRE FONDO OSCURO)
# =====================================================================
def detect_center_loading_button(gray, w, h):
    if (np.count_nonzero(cv.Canny(gray, 50, 150)) / float(w * h)) > 0.04:
        return []

    x1, y1 = int(w * 0.35), int(h * 0.25)
    x2, y2 = int(w * 0.65), int(h * 0.60)
    roi = cv.GaussianBlur(gray[y1:y2, x1:x2], (5, 5), 1.5)

    circles = cv.HoughCircles(
        roi, cv.HOUGH_GRADIENT, dp=1.2, minDist=int(h * 0.1),
        param1=80, param2=32, minRadius=int(h * 0.09), maxRadius=int(h * 0.16)
    )
    if circles is not None:
        cx, cy, r = np.round(circles[0, 0]).astype("int")
        return [(x1 + cx, y1 + cy, r, "CONTINUAR (CARGA)")]
    return []


# =====================================================================
# 4. DETECTOR DE BOTÓN VERDE "INICIAR JUEGO"
# =====================================================================
def detect_green_start_button(hsv, w, h):
    x1, y1 = int(w * 0.70), int(h * 0.38)
    x2, y2 = int(w * 0.88), int(h * 0.62)
    roi_hsv = hsv[y1:y2, x1:x2]

    green_mask = cv.inRange(roi_hsv, np.array([35, 80, 80]), np.array([85, 255, 255]))
    contours, _ = cv.findContours(green_mask, cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE)
    for cnt in contours:
        area = cv.contourArea(cnt)
        (rcx, rcy), r = cv.minEnclosingCircle(cnt)
        if int(h * 0.08) <= r <= int(h * 0.13) and (area / (np.pi * r * r)) > 0.75:
            return [(x1 + int(rcx), y1 + int(rcy), int(r), "INICIAR JUEGO")]
    return []


# =====================================================================
# 5A. DETECTOR RÁPIDO DE FLECHA CIRCULAR BLANCA (ESTÁNDAR / NARANJA / GRIS)
# =====================================================================
def evaluate_white_arrow_candidate(white_mask, roi_hsv, cx, cy, r_a):
    """
    Verifica en O(1) si alrededor de (cx, cy) con radio de flecha r_a existe:
    1. Centro vacío (hueco interior de las flechas).
    2. Cuerpo blanco de flecha circular repartido en los 4 cuadrantes.
    3. Foso circular inmediato no blanco (fondo negro, gris translúcido o naranja sólido).
    """
    rh, rw = white_mask.shape
    pad = int(r_a * 1.38)
    px1, py1 = max(0, cx - pad), max(0, cy - pad)
    px2, py2 = min(rw, cx + pad), min(rh, cy + pad)

    if (px2 - px1) < int(r_a * 1.8) or (py2 - py1) < int(r_a * 1.8):
        return 0.0

    sub_w = white_mask[py1:py2, px1:px2] > 0
    sub_hsv = roi_hsv[py1:py2, px1:px2]
    yy, xx = np.indices(sub_w.shape)
    dx = xx - (cx - px1)
    dy = yy - (cy - py1)
    dist = np.hypot(dx, dy)

    hole_mask = dist <= (0.30 * r_a)
    arrow_mask = (dist >= (0.40 * r_a)) & (dist <= (0.98 * r_a))
    outer_arrow_band = (dist >= (0.62 * r_a)) & (dist <= (0.94 * r_a))
    moat_mask = (dist >= (1.06 * r_a)) & (dist <= (1.28 * r_a))

    if not (np.any(hole_mask) and np.any(arrow_mask) and np.any(moat_mask)):
        return 0.0

    # 1. El centro del botón debe estar despejado de píxeles blancos
    hole_white = np.count_nonzero(sub_w & hole_mask) / float(np.count_nonzero(hole_mask))
    if hole_white > 0.18:
        return 0.0

    # 2. Densidad de la flecha blanca y del foso que la separa del borde exterior
    arrow_white = np.count_nonzero(sub_w & arrow_mask) / float(np.count_nonzero(arrow_mask))
    outer_band_white = np.count_nonzero(sub_w & outer_arrow_band) / float(np.count_nonzero(outer_arrow_band))
    moat_white = np.count_nonzero(sub_w & moat_mask) / float(np.count_nonzero(moat_mask))

    if not (0.20 <= arrow_white <= 0.78 and outer_band_white >= 0.18 and moat_white <= 0.24):
        return 0.0

    # 3. La flecha circular (simple en 'C' o doble) debe rodear el centro en los 4 cuadrantes
    q_ratios = []
    for q_mask in ((dx < 0) & (dy < 0), (dx >= 0) & (dy < 0), (dx < 0) & (dy >= 0), (dx >= 0) & (dy >= 0)):
        qm = arrow_mask & q_mask
        if not np.any(qm):
            return 0.0
        q_ratios.append(np.count_nonzero(sub_w & qm) / float(np.count_nonzero(qm)))

    if min(q_ratios) < 0.04 or sum(1 for q in q_ratios if q >= 0.12) < 3:
        return 0.0

    # 4. Validar color de fondo del botón (en los píxeles no blancos dentro del disco)
    bg_mask = (dist <= (1.22 * r_a)) & (~sub_w)
    if np.count_nonzero(bg_mask) < 15:
        return 0.0

    h_bg = sub_hsv[:, :, 0][bg_mask]
    s_bg = sub_hsv[:, :, 1][bg_mask]
    v_bg = sub_hsv[:, :, 2][bg_mask]

    med_h, med_s, med_v = np.median(h_bg), np.median(s_bg), np.median(v_bg)

    # Fondo válido A: Negro, oscuro o gris/verde/marrón translúcido
    is_dark_or_translucent = (med_v <= 155 and med_s <= 110)
    # Fondo válido B: Botón naranja intenso (ej. Dr Zappo con apuesta bonus activa)
    is_orange_button = (5 <= med_h <= 24 and med_s >= 150 and med_v >= 160 and np.std(v_bg) <= 48)

    if not (is_dark_or_translucent or is_orange_button):
        return 0.0

    # Puntuación: prioriza el botón principal más grande y mejor balanceado en sus 4 cuadrantes
    quad_balance = min(q_ratios) / (max(q_ratios) + 1e-5)
    return float(r_a) * (1.0 + 0.5 * quad_balance) * (1.0 - hole_white)


def detect_white_arrow_spin(hsv, w, h):
    x1, y1 = int(w * 0.65), int(h * 0.42)
    x2, y2 = int(w * 0.99), int(h * 0.98)
    roi_hsv = hsv[y1:y2, x1:x2]

    # Máscara de blanco puro para aislar las flechas circulares de giro
    white_mask = cv.inRange(roi_hsv, np.array([0, 0, 195]), np.array([180, 62, 255]))

    # RETR_LIST es clave para leer las flechas blancas dentro de anillos blancos cerrados
    contours, _ = cv.findContours(white_mask, cv.RETR_LIST, cv.CHAIN_APPROX_SIMPLE)

    min_part = int(h * 0.016)
    max_part = int(h * 0.185)
    boxes = []
    for cnt in contours:
        bx, by, bw, bh = cv.boundingRect(cnt)
        if min_part <= bw <= max_part and min_part <= bh <= max_part:
            boxes.append((bx, by, bx + bw, by + bh))

    # Si hay demasiados contornos pequeños por ruido, conservar los 35 mayores por área
    if len(boxes) > 35:
        boxes.sort(key=lambda b: (b[2] - b[0]) * (b[3] - b[1]), reverse=True)
        boxes = boxes[:35]

    candidate_boxes = list(boxes)
    # Emparejar contornos cercanos (para botones de 2 flechas blancas separadas)
    n = len(boxes)
    max_pair_dist = h * 0.105
    for i in range(n):
        ax1, ay1, ax2, ay2 = boxes[i]
        acx, acy = (ax1 + ax2) * 0.5, (ay1 + ay2) * 0.5
        for j in range(i + 1, n):
            bx1, by1, bx2, by2 = boxes[j]
            bcx, bcy = (bx1 + bx2) * 0.5, (by1 + by2) * 0.5
            if np.hypot(acx - bcx, acy - bcy) <= max_pair_dist:
                candidate_boxes.append((min(ax1, bx1), min(ay1, by1), max(ax2, bx2), max(ay2, by2)))

    min_ra, max_ra = int(h * 0.033), int(h * 0.088)
    best_score = 0.0
    best_btn = None

    for (bx1, by1, bx2, by2) in candidate_boxes:
        bw, bh = bx2 - bx1, by2 - by1
        if bh == 0 or not (0.72 <= (float(bw) / bh) <= 1.38):
            continue

        r_a = int((bw + bh) * 0.25)
        if not (min_ra <= r_a <= max_ra):
            continue

        cx, cy = (bx1 + bx2) // 2, (by1 + by2) // 2
        abs_x, abs_y = x1 + cx, y1 + cy
        rel_x, rel_y = abs_x / float(w), abs_y / float(h)

        in_bottom_bar = (0.68 <= rel_x <= 0.89) and (0.82 <= rel_y <= 0.96)
        in_right_side = (0.76 <= rel_x <= 0.97) and (0.44 <= rel_y <= 0.84)
        if not (in_bottom_bar or in_right_side):
            continue

        score = evaluate_white_arrow_candidate(white_mask, roi_hsv, cx, cy, r_a)
        if score > best_score:
            best_score = score
            best_btn = (abs_x, abs_y, int(r_a * 1.48), "GIRAR / CONTINUAR")

    return [best_btn] if best_btn is not None else []


# =====================================================================
# 5B. DETECTOR DE BOTÓN OSCURO TRANSLÚCIDO (EJ. BIG BASS HALLOWEEN)
# =====================================================================
def detect_dark_translucent_spin(hsv, gray, w, h):
    """
    Detecta botones oscuros con flechas grises tenues (ej. Big Bass Halloween)
    restringiendo la búsqueda a la barra inferior para excluir calderos u objetos laterales.
    """
    x1, y1 = int(w * 0.71), int(h * 0.78)
    x2, y2 = int(w * 0.86), int(h * 0.98)
    roi_gray = gray[y1:y2, x1:x2]
    roi_hsv = hsv[y1:y2, x1:x2]

    clahe = cv.createCLAHE(clipLimit=3.0, tileGridSize=(4, 4)).apply(roi_gray)
    blur = cv.GaussianBlur(clahe, (5, 5), 1.2)

    min_r, max_r = int(h * 0.070), int(h * 0.095)
    circles = cv.HoughCircles(
        blur, cv.HOUGH_GRADIENT, dp=1.2, minDist=int(h * 0.05),
        param1=70, param2=24, minRadius=min_r, maxRadius=max_r
    )
    if circles is None:
        return []

    yy, xx = np.indices(roi_gray.shape)
    for (rcx, rcy, r) in np.round(circles[0, :]).astype("int"):
        dx, dy = xx - rcx, yy - rcy
        dist = np.hypot(dx, dy)

        moat = (dist >= 0.72 * r) & (dist <= 0.92 * r)
        lr_arrows = (dist >= 0.40 * r) & (dist <= 0.75 * r) & (np.abs(dx) >= 0.32 * r) & (np.abs(dy) <= 0.45 * r)
        tb_dark = (dist >= 0.45 * r) & (dist <= 0.78 * r) & (np.abs(dy) >= 0.40 * r) & (np.abs(dx) <= 0.28 * r)

        if not (np.any(moat) and np.any(lr_arrows) and np.any(tb_dark)):
            continue

        # El foso del botón debe ser muy oscuro y acromático (descarta calderos con poción verde)
        if np.median(roi_hsv[:, :, 2][moat]) > 55 or np.median(roi_hsv[:, :, 1][moat]) > 65:
            continue

        # Las dos flechas grises laterales deben ser más claras que la zona superior/inferior
        if float(np.mean(roi_gray[lr_arrows])) > float(np.mean(roi_gray[tb_dark])) + 12.0:
            return [(x1 + rcx, y1 + rcy, r, "GIRAR / CONTINUAR")]

    return []


# =====================================================================
# 5C. DETECTOR DE BOTÓN ULTRA-TRANSPARENTE (EJ. BAMBOO PANDITS TENUE)
# =====================================================================
def detect_transparent_bamboo_spin(hsv, w, h):
    x1, y1 = int(w * 0.82), int(h * 0.58)
    x2, y2 = int(w * 0.98), int(h * 0.92)

    roi_s = hsv[y1:y2, x1:x2, 1].astype(np.float32)
    roi_v = hsv[y1:y2, x1:x2, 2].astype(np.float32)

    whiteness = roi_v - 0.55 * roi_s
    bg_horiz = cv.GaussianBlur(whiteness, (35, 3), 0)
    local_white = cv.normalize(whiteness - bg_horiz, None, 0, 255, cv.NORM_MINMAX).astype(np.uint8)
    local_white = cv.GaussianBlur(local_white, (5, 5), 1.2)

    min_r, max_r = int(h * 0.080), int(h * 0.125)
    circles = cv.HoughCircles(
        local_white, cv.HOUGH_GRADIENT, dp=1.2, minDist=int(h * 0.08),
        param1=55, param2=22, minRadius=min_r, maxRadius=max_r
    )
    if circles is None:
        return []

    yy, xx = np.indices(local_white.shape)
    best = None
    best_score = 0.0

    for (rcx, rcy, r) in np.round(circles[0, :]).astype("int"):
        dist = np.hypot(xx - rcx, yy - rcy)
        arrow_ring = (dist >= 0.45 * r) & (dist <= 0.92 * r)
        center_hole = dist <= 0.35 * r
        outer_bg = (dist >= 1.08 * r) & (dist <= 1.30 * r)

        if not (np.any(arrow_ring) and np.any(center_hole) and np.any(outer_bg)):
            continue

        # Bloquear fondos muy saturados (evita falsos positivos en escaparates de neón o piernas)
        if np.median(roi_s[arrow_ring]) > 62:
            continue

        diff_center = float(np.mean(whiteness[arrow_ring])) - float(np.mean(whiteness[center_hole]))
        diff_outer = float(np.mean(whiteness[arrow_ring])) - float(np.mean(whiteness[outer_bg]))

        if diff_center > 6.5 and diff_outer > 6.5:
            score = diff_center + diff_outer
            if score > best_score:
                best_score = score
                best = (x1 + rcx, y1 + rcy, r, "GIRAR (TRANSPARENTE)")

    return [best] if best is not None else []


# =====================================================================
# 6. DETECTOR DE PANTALLAS "PULSA / HAGA CLIC PARA CONTINUAR"
# =====================================================================
def detect_tap_anywhere_prompt(gray, w, h):
    x1, y1 = int(w * 0.25), int(h * 0.80)
    x2, y2 = int(w * 0.75), int(h * 0.98)
    roi = gray[y1:y2, x1:x2]

    grad_x = np.abs(cv.Sobel(roi, cv.CV_32F, 1, 0, ksize=3))
    grad_x = cv.normalize(grad_x, None, 0, 255, cv.NORM_MINMAX).astype(np.uint8)
    _, thresh = cv.threshold(grad_x, 0, 255, cv.THRESH_BINARY + cv.THRESH_OTSU)

    kernel = cv.getStructuringElement(cv.MORPH_RECT, (17, 4))
    closed = cv.morphologyEx(thresh, cv.MORPH_CLOSE, kernel)

    contours, _ = cv.findContours(closed, cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE)
    roi_w = x2 - x1
    for cnt in contours:
        bx, by, bw, bh = cv.boundingRect(cnt)
        cx_rel = (bx + bw * 0.5) / float(roi_w)
        if 0.42 <= cx_rel <= 0.58 and bw >= 0.35 * roi_w and (bw / float(max(1, bh))) >= 4.5:
            return [(x1 + bx + bw // 2, y1 + by + bh // 2, int(h * 0.05), "TOCAR PANTALLA PARA CONTINUAR")]
    return []


# =====================================================================
# PIPELINE PRINCIPAL JERÁRQUICO DE BAJO COSTE
# =====================================================================
def find_game_action(img_bgr):
    open_cv_image = np.array(img_bgr)
    open_cv_image = open_cv_image[:, :, ::-1].copy()
    orig_h, orig_w = open_cv_image.shape[:2]

    # Caso 0: Recortes individuales pequeños de botones (< 300x300 px)
    if max(orig_h, orig_w) < 300:
        hsv_crop = cv.cvtColor(open_cv_image, cv.COLOR_BGR2HSV)
        white_crop = cv.inRange(hsv_crop, np.array([0, 0, 185]), np.array([180, 65, 255]))
        score = evaluate_white_arrow_candidate(white_crop, hsv_crop, orig_w // 2, orig_h // 2, int(min(orig_h, orig_w) * 0.28))
        if score > 0:
            return [(orig_w // 2, orig_h // 2, int(min(orig_h, orig_w) * 0.44), "RECORTE BOTON GIRO")]
        return []

    # Reescalado único a ancho 640 para minimizar el coste computacional (~9x más rápido)
    work_w = 640
    if orig_w > work_w:
        scale = work_w / float(orig_w)
        work_h = int(orig_h * scale)
        work_img = cv.resize(open_cv_image, (work_w, work_h), interpolation=cv.INTER_AREA)
    else:
        scale = 1.0
        work_w, work_h = orig_w, orig_h
        work_img = open_cv_image

    gray = cv.cvtColor(work_img, cv.COLOR_BGR2GRAY)
    hsv = cv.cvtColor(work_img, cv.COLOR_BGR2HSV)

    # Prioridad 1: Selección de calabazas
    actions = detect_pumpkins(hsv, work_w, work_h)
    # Prioridad 2: Botón dorado central de Bonus
    if not actions:
        actions = detect_golden_bonus_button(hsv, work_w, work_h)
    # Prioridad 3: Botón central '>' en pantalla de carga
    if not actions:
        actions = detect_center_loading_button(gray, work_w, work_h)
    # Prioridad 4: Botón circular verde "INICIAR JUEGO"
    if not actions:
        actions = detect_green_start_button(hsv, work_w, work_h)
    # Prioridad 5A: Botón de giro con flecha(s) circular(es) blanca(s)
    if not actions:
        actions = detect_white_arrow_spin(hsv, work_w, work_h)
    # Prioridad 5B: Botón de giro oscuro translúcido (ej. Big Bass Halloween)
    if not actions:
        actions = detect_dark_translucent_spin(hsv, gray, work_w, work_h)
    # Prioridad 5C: Botón de giro ultra-transparente (ej. Bamboo Pandits tenue)
    if not actions:
        actions = detect_transparent_bamboo_spin(hsv, work_w, work_h)
    # Prioridad 6: Pantalla de "Pulsa / Haga clic para continuar"
    if not actions:
        actions = detect_tap_anywhere_prompt(gray, work_w, work_h)

    # Reescalar coordenadas a la resolución original de la imagen
    inv_scale = 1.0 / scale
    return [(int(x * inv_scale), int(y * inv_scale), int(r * inv_scale), label) for (x, y, r, label) in actions]


def main():
    files = sorted(glob.glob('./examples/*.png') + glob.glob('./examples/*.jpg'))
    for fn in files:
        img = cv.imread(fn)
        if img is None:
            continue

        actions = find_game_action(img)
        for (x, y, r, label) in actions:
            cv.circle(img, (x, y), r, (0, 255, 0), 3)
            cv.circle(img, (x, y), 5, (0, 0, 255), -1)
            cv.putText(img, label, (max(10, x - r), max(25, y - r - 10)),
                       cv.FONT_HERSHEY_SIMPLEX, 0.65, (0, 255, 0), 2, cv.LINE_AA)

        cv.imshow('Accion Detectada', img)
        if cv.waitKey() == 27:
            break

    cv.destroyAllWindows()


if __name__ == '__main__':
    main()

class TooManyButtonsException(Exception):
    def __innit__(self,actions, msg="Too many buttons."):
        self.actions = actions
        self.msg = msg
        super().__init__(self.msg)

def img_to_action(img):
    action = find_game_action(img)
    if(len(action) > 1):
        raise TooManyButtonsException(action)
    return action