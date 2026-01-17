import pyautogui
import time
import keyboard
import json
import os
import math
import random
from datetime import datetime
from pynput import mouse

# ==================== CONFIGURACION GLOBAL ====================
pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.1

# ==================== CLASE GRABADOR ====================

class GrabadorColor:
    def __init__(self):
        self.recording = False
        self.clicks = []

    def on_click(self, x, y, button, pressed):
        if pressed and button == mouse.Button.left and self.recording:
            color = pyautogui.pixel(x, y)
            self.clicks.append({'x': x, 'y': y, 'color_esperado': color})
            r, g, b = color
            print(f"Click #{len(self.clicks)}: ({x}, {y}) | RGB({r}, {g}, {b})")

    def start(self):
        self.recording = True
        self.clicks = []

    def stop(self):
        self.recording = False

# ==================== CLASE PRINCIPAL ====================

class AutoClicker:
    def __init__(self):
        self.paused = False
        self.recorder = GrabadorColor()

        # Constants
        self.MAX_WAIT_TIME = 30
        self.CHECK_INTERVAL = 0.05
        self.DEFAULT_TOLERANCE = 25
        self.CATEGORIES = {
            '1': 'Boss de Evento',
            '2': 'Mision Diaria',
            '3': 'Casa de Boss',
            '4': 'PvE General',
            '5': 'Farmeo de Recursos',
            '6': 'Otra'
        }

    # ==================== UTILIDADES ====================

    def clear_screen(self):
        os.system('cls' if os.name == 'nt' else 'clear')

    def pause(self):
        input("\nPresiona ENTER para continuar...")

    def load_json(self, path):
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def save_json(self, data, path):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)

    def compare_colors(self, color1, color2, tolerance):
        r1, g1, b1 = color1
        r2, g2, b2 = color2
        diff = math.sqrt((r1 - r2)**2 + (g1 - g2)**2 + (b1 - b2)**2)
        return diff <= tolerance

    def verify_controls(self):
        if keyboard.is_pressed('p'):
            self.paused = not self.paused
            if self.paused:
                print("\n[PAUSADO] Presiona 'P' para continuar")
                while self.paused:
                    if keyboard.is_pressed('p'):
                        self.paused = False
                        print("[REANUDANDO]\n")
                        time.sleep(0.5)
                    if keyboard.is_pressed('esc'):
                        return False
                    time.sleep(0.1)
            time.sleep(0.5)

        if keyboard.is_pressed('esc'):
            print("\n[DETENIENDO]")
            return False
        return True

    def countdown(self, seconds=3):
        print(f"\nIniciando en {seconds}s...")
        for i in range(seconds, 0, -1):
            print(f"   {i}...")
            time.sleep(1)

    def list_routines(self):
        routines = []
        if os.path.exists('grabaciones/rutinas'):
            for file in os.listdir('grabaciones/rutinas'):
                if file.endswith('.json'):
                    path = f'grabaciones/rutinas/{file}'
                    try:
                        data = self.load_json(path)
                        routines.append({'file': file, 'path': path, 'data': data})
                    except:
                        pass
        return routines

    def generate_filename(self, name):
        name = name.lower().replace(' ', '_')
        return ''.join(c for c in name if c.isalnum() or c == '_') + '.json'

    def display_header(self, title):
        self.clear_screen()
        print("=" * 70)
        print(title.upper())
        print("=" * 70)

    def get_choice(self, prompt, options, allow_cancel=True):
        while True:
            try:
                choice = input(prompt).strip()
                if allow_cancel and choice == '0':
                    return None
                if choice in options:
                    return choice
            except KeyboardInterrupt:
                return None

    def get_int_input(self, prompt, min_val=None, max_val=None, allow_cancel=True):
        while True:
            try:
                inp = input(prompt).strip()
                if allow_cancel and inp.lower() == 'cancelar':
                    return None
                val = int(inp)
                if (min_val is None or val >= min_val) and (max_val is None or val <= max_val):
                    return val
            except ValueError:
                pass

    def select_routine(self, routines, title="SELECCIONAR RUTINA"):
        if not routines:
            print("\n[ERROR] No hay rutinas guardadas")
            self.pause()
            return None

        self.display_header(title)
        print("\nRUTINAS DISPONIBLES:")
        print("=" * 70)
        for i, routine in enumerate(routines, 1):
            data = routine['data']
            print(f"{i}. {data['nombre']}")
            print(f"   Categoria: {data.get('categoria', 'N/A')}")
            print(f"   Clics: {data['total_clics']}")
            print()
        print("=" * 70)

        choice = self.get_int_input("\nSelecciona rutina (0 para cancelar): ", 0, len(routines))
        return routines[choice - 1] if choice and choice > 0 else None

    # ==================== FUNCIONES PRINCIPALES ====================

    def create_routine(self):
        self.display_header("CREAR NUEVA RUTINA")

        print("\nIngresa el nombre de la rutina:")
        print("Ejemplos: Boss Evento Navidad, Mision Diaria Oro, Casa Boss Akatsuki")
        name = input("\nNombre: ").strip()
        if not name:
            print("\n[ERROR] El nombre no puede estar vacío")
            self.pause()
            return

        filename = self.generate_filename(name)
        path = f'grabaciones/rutinas/{filename}'

        if os.path.exists(path):
            if input(f"\n[ADVERTENCIA] Ya existe '{name}'. Sobrescribir? (s/n): ").strip().lower() != 's':
                self.pause()
                return

        print("\n" + "=" * 70)
        print("CATEGORIA")
        print("=" * 70)
        for key, val in sorted(self.CATEGORIES.items()):
            print(f"{key}. {val}")
        print("=" * 70)

        cat_key = self.get_choice("\nSelecciona categoria (1-6): ", self.CATEGORIES.keys())
        category = self.CATEGORIES.get(cat_key, 'Otra')
        if category == 'Otra':
            category = input("Ingresa categoria personalizada: ").strip() or 'Otra'

        description = input("\nDescripcion (opcional, presiona ENTER para omitir): ").strip()

        print("\nDETECCION DE COLOR:")
        print("   - El programa capturara el RGB de cada coordenada")
        print("   - Esperara a que ese color aparezca antes de hacer clic")

        tolerance = self.get_int_input("\nTolerancia (10-50, recomendado 25): ", 10, 50) or 25

        self.pause()
        self.countdown()

        print("\n[GRABANDO] Presiona ESC cuando termines\n")

        self.recorder.start()
        listener = mouse.Listener(on_click=self.recorder.on_click)
        listener.start()
        keyboard.wait('esc')
        self.recorder.stop()
        listener.stop()

        if not self.recorder.clicks:
            print("\n[ERROR] No se grabaron clics")
            self.pause()
            return

        print(f"\n{len(self.recorder.clicks)} clics registrados")

        data = {
            'nombre': name,
            'categoria': category,
            'descripcion': description,
            'tipo': 'deteccion_color',
            'fecha_creacion': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'fecha_modificacion': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'total_clics': len(self.recorder.clicks),
            'tolerancia': tolerance,
            'clics': self.recorder.clicks,
            'estadisticas': {'total_ejecuciones': 0, 'tiempo_total': 0, 'ultima_ejecucion': None}
        }

        self.save_json(data, path)
        print(f"\n[GUARDADO] {path}")
        print(f"Nombre: {name} | Categoria: {category} | Clics: {len(self.recorder.clicks)}")
        self.pause()

    def edit_routine(self):
        routines = self.list_routines()
        selected = self.select_routine(routines, "EDITAR RUTINA EXISTENTE")
        if not selected:
            return

        data = selected['data']
        path = selected['path']

        self.display_header("QUE DESEAS EDITAR?")
        print("1. Nombre\n2. Categoria\n3. Descripcion\n4. Regrabar clics completo\n5. Ajustar tolerancia\n6. Volver")
        print("=" * 70)

        option = self.get_choice("\nSelecciona (1-6): ", ['1', '2', '3', '4', '5', '6'])

        if option == '1':
            new_name = input(f"\nNombre actual: {data['nombre']}\nNuevo nombre: ").strip()
            if new_name:
                data['nombre'] = new_name
                data['fecha_modificacion'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                self.save_json(data, path)
                print("\n[ACTUALIZADO] Nombre cambiado")

        elif option == '2':
            print(f"\nCategoria actual: {data.get('categoria', 'N/A')}")
            print("\n" + "=" * 70)
            for key, val in sorted(self.CATEGORIES.items()):
                print(f"{key}. {val}")
            print("=" * 70)
            cat_key = self.get_choice("\nSelecciona categoria (1-6): ", self.CATEGORIES.keys())
            category = self.CATEGORIES.get(cat_key, data.get('categoria', 'Otra'))
            if category == 'Otra':
                category = input("Categoria personalizada: ").strip() or data.get('categoria', 'Otra')
            data['categoria'] = category
            data['fecha_modificacion'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            self.save_json(data, path)
            print("\n[ACTUALIZADO] Categoria cambiada")

        elif option == '3':
            new_desc = input(f"\nDescripcion actual: {data.get('descripcion', 'N/A')}\nNueva descripcion: ").strip()
            data['descripcion'] = new_desc
            data['fecha_modificacion'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            self.save_json(data, path)
            print("\n[ACTUALIZADO] Descripcion cambiada")

        elif option == '4':
            if input("\n[ADVERTENCIA] Esto borrara todos los clics actuales. Continuar? (s/n): ").strip().lower() == 's':
                self.pause()
                self.countdown()
                print("\n[GRABANDO] Presiona ESC cuando termines\n")
                self.recorder.start()
                listener = mouse.Listener(on_click=self.recorder.on_click)
                listener.start()
                keyboard.wait('esc')
                self.recorder.stop()
                listener.stop()
                if self.recorder.clicks:
                    data['clics'] = self.recorder.clicks
                    data['total_clics'] = len(self.recorder.clicks)
                    data['fecha_modificacion'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    self.save_json(data, path)
                    print(f"\n[ACTUALIZADO] {len(self.recorder.clicks)} nuevos clics grabados")

        elif option == '5':
            current_tol = data.get('tolerancia', self.DEFAULT_TOLERANCE)
            new_tol = self.get_int_input(f"\nTolerancia actual: {current_tol}\nNueva tolerancia (10-50): ", 10, 50)
            if new_tol is not None:
                data['tolerancia'] = new_tol
                data['fecha_modificacion'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                self.save_json(data, path)
                print("\n[ACTUALIZADO] Tolerancia cambiada")

        self.pause()

    def delete_routine(self):
        routines = self.list_routines()
        selected = self.select_routine(routines, "ELIMINAR RUTINA")
        if not selected:
            return

        data = selected['data']
        if input(f"\n[ADVERTENCIA] Eliminar '{data['nombre']}'? (s/n): ").strip().lower() == 's':
            os.remove(selected['path'])
            print(f"\n[ELIMINADO] {data['nombre']}")
        else:
            print("\n[CANCELADO]")
        self.pause()

    def record_jutsus(self):
        self.display_header("GRABAR SECUENCIA DE JUTSUS")

        print("\nDETECCION DE COLOR EN JUTSUS:")
        print("   - Cada jutsu tiene colores unicos")
        print("   - El programa detectara cuando cada jutsu este listo")

        tolerance = self.get_int_input("\nTolerancia (10-50, recomendado 30): ", 10, 50) or 30

        self.pause()
        self.countdown()

        print("\n[GRABANDO] Presiona ESC cuando termines\n")

        self.recorder.start()
        listener = mouse.Listener(on_click=self.recorder.on_click)
        listener.start()
        keyboard.wait('esc')
        self.recorder.stop()
        listener.stop()

        print(f"\n{len(self.recorder.clicks)} clics registrados")

        if self.recorder.clicks:
            print(f"\n{'=' * 70}")
            print("COLORES REGISTRADOS:")
            print(f"{'=' * 70}")
            for i, click in enumerate(self.recorder.clicks, 1):
                r, g, b = click['color_esperado']
                print(f"Jutsu {i}: ({click['x']:4d}, {click['y']:4d}) | RGB({r:3d}, {g:3d}, {b:3d})")
            print(f"{'=' * 70}")

            data = {
                'nombre': 'jutsus_combo',
                'tipo': 'deteccion_color',
                'fecha': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'total_clics': len(self.recorder.clicks),
                'tolerancia': tolerance,
                'clics': self.recorder.clicks
            }

            self.save_json(data, 'grabaciones/combate/jutsus_combo.json')
            print(f"\n[GUARDADO] grabaciones/combate/jutsus_combo.json")

        self.pause()

    def record_scratch_and_win(self):
        while True:
            self.display_header("GRABAR RASCA Y GANA - SISTEMA MULTI-PUNTO")

            config_exists = os.path.exists('grabaciones/utilidades/rasca_y_gana.json')
            existing_slots = []
            existing_points = []

            if config_exists:
                try:
                    prev_data = self.load_json('grabaciones/utilidades/rasca_y_gana.json')
                    existing_slots = prev_data.get('ranuras', [])
                    existing_points = prev_data.get('puntos_deteccion', [])

                    print("\nCONFIGURACION EXISTENTE:")
                    print(f"   - Puntos de deteccion: {len(existing_points)}")
                    print(f"   - Ranuras grabadas: {len(existing_slots)}/3")
                    for slot in existing_slots:
                        print(f"      * Slot {slot.get('numero')}")
                except:
                    config_exists = False

            print("\n" + "=" * 70)
            print("MENU DE GRABACION")
            print("=" * 70)
            print("1. Grabar/Regrabar puntos de deteccion del scratch")
            print("2. Grabar un slot individual")
            print("3. Volver al menu principal")
            print("=" * 70)

            option = self.get_choice("\nSelecciona (1-3): ", ['1', '2', '3'])

            if option == '3':
                break
            elif option == '1':
                self.record_detection_points()
            elif option == '2':
                self.record_individual_slot()

    def record_detection_points(self):
        self.display_header("GRABAR PUNTOS DE DETECCION DEL SCRATCH")

        print("\nHAZ CLIC EN ESTOS PUNTOS (orden sugerido):")
        print("   1. Titulo 'DAILY SCRATCH CARD' (texto negro)")
        print("   2. Fondo amarillo brillante (zona superior)")
        print("   3. Area de las ranuras (zona gris)")
        print("   4. Boton 'Rewards' (opcional)")
        print("   5. Otro punto unico del pop-up")
        print("\nMinimo 3 puntos, maximo 5 puntos")
        print("Presiona ESC cuando termines")

        tolerance = self.get_int_input("\nTolerancia (20-50, recomendado 35): ", 20, 50) or 35

        self.pause()
        self.countdown()

        print("\n[GRABANDO] Haz clic en los puntos de deteccion\n")

        self.recorder.start()
        listener = mouse.Listener(on_click=self.recorder.on_click)
        listener.start()
        keyboard.wait('esc')
        self.recorder.stop()
        listener.stop()

        if len(self.recorder.clicks) < 3:
            print(f"\n[ERROR] Se necesitan minimo 3 puntos (solo grabaste {len(self.recorder.clicks)})")
            self.pause()
            return

        detection_points = self.recorder.clicks[:5]

        print(f"\n{len(detection_points)} puntos de deteccion capturados:")
        for i, point in enumerate(detection_points, 1):
            r, g, b = point['color_esperado']
            print(f"   {i}. ({point['x']}, {point['y']}) | RGB({r}, {g}, {b})")

        existing_slots = []
        if os.path.exists('grabaciones/utilidades/rasca_y_gana.json'):
            try:
                prev_data = self.load_json('grabaciones/utilidades/rasca_y_gana.json')
                existing_slots = prev_data.get('ranuras', [])
                print(f"\nSe mantienen {len(existing_slots)} ranuras ya grabadas")
            except:
                pass

        data = {
            'nombre': 'rasca_y_gana',
            'tipo': 'deteccion_multipunto',
            'fecha': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'puntos_deteccion': detection_points,
            'tolerancia_deteccion': tolerance,
            'ranuras': existing_slots,
            'tolerancia_ranuras': 30
        }

        self.save_json(data, 'grabaciones/utilidades/rasca_y_gana.json')
        print("\n[GUARDADO] grabaciones/utilidades/rasca_y_gana.json")
        self.pause()

    def record_individual_slot(self):
        self.display_header("GRABAR SLOT INDIVIDUAL")

        if not os.path.exists('grabaciones/utilidades/rasca_y_gana.json'):
            print("\n[ERROR] No hay puntos de deteccion grabados")
            print("Debes grabar los puntos de deteccion primero (Opcion 1)")
            self.pause()
            return

        prev_data = self.load_json('grabaciones/utilidades/rasca_y_gana.json')
        detection_points = prev_data.get('puntos_deteccion', [])
        detection_tol = prev_data.get('tolerancia_deteccion', 35)
        existing_slots = prev_data.get('ranuras', [])

        if not detection_points:
            print("\n[ERROR] Configuracion corrupta, no hay puntos de deteccion")
            print("Vuelve a grabar los puntos de deteccion (Opcion 1)")
            self.pause()
            return

        print(f"\nPuntos de deteccion: {len(detection_points)}")
        print(f"Slots ya grabados: {len(existing_slots)}/3")
        for slot in existing_slots:
            print(f"   - Slot {slot.get('numero')}")

        print("\nQUE SLOT QUIERES GRABAR?")
        print("=" * 70)
        print("1. Slot Izquierdo\n2. Slot Centro\n3. Slot Derecho")
        print("=" * 70)

        slot_num = self.get_choice("\nSelecciona (1-3): ", ['1', '2', '3'])
        if not slot_num:
            return
        slot_num = int(slot_num)

        if any(s.get('numero') == slot_num for s in existing_slots):
            if input(f"\n[ADVERTENCIA] El Slot {slot_num} ya esta grabado. Reemplazarlo? (s/n): ").strip().lower() != 's':
                self.pause()
                return
            existing_slots = [s for s in existing_slots if s.get('numero') != slot_num]

        print("\nIMPORTANTE - SECUENCIA DE 3 CLICS:")
        print("   1. Primer clic: RASCAR el slot")
        print("   2. Segundo clic: SALIR de la pantalla de recompensa")
        print("   3. Tercer clic: SALIR del scratch completamente")
        print("\nDebes hacer los 3 clics en orden")

        self.pause()
        self.countdown()

        print(f"\n[GRABANDO] Haz los 3 clics del Slot {slot_num}\n")

        self.recorder.start()
        listener = mouse.Listener(on_click=self.recorder.on_click)
        listener.start()
        keyboard.wait('esc')
        self.recorder.stop()
        listener.stop()

        captured_clicks = self.recorder.clicks[:3]

        print(f"\nSlot {slot_num} grabado con {len(captured_clicks)} clics:")
        click_names = ["Rascar", "Salir recompensa", "Salir scratch"]
        for i, click in enumerate(captured_clicks, 1):
            r, g, b = click['color_esperado']
            name = click_names[i - 1] if i <= 3 else f"Clic {i}"
            print(f"   {i}. {name}: ({click['x']}, {click['y']}) | RGB({r}, {g}, {b})")

        existing_slots.append({'numero': slot_num, 'clics': captured_clicks})
        existing_slots.sort(key=lambda x: x.get('numero', 0))

        print(f"\n{'=' * 70}")
        print("RESUMEN ACTUAL")
        print(f"{'=' * 70}")
        print(f"\nPuntos de deteccion: {len(detection_points)}")
        print(f"Slots grabados: {len(existing_slots)}/3")
        for slot in existing_slots:
            num_clicks = len(slot.get('clics', []))
            print(f"   Slot #{slot['numero']}: {num_clicks} clics")

        if len(existing_slots) < 3:
            print(f"\nFaltan {3 - len(existing_slots)} slots por grabar")
        else:
            print("\nTODOS LOS SLOTS GRABADOS")

        print(f"{'=' * 70}")

        data = {
            'nombre': 'rasca_y_gana',
            'tipo': 'deteccion_multipunto',
            'fecha': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'puntos_deteccion': detection_points,
            'tolerancia_deteccion': detection_tol,
            'ranuras': existing_slots,
            'tolerancia_ranuras': 30
        }

        self.save_json(data, 'grabaciones/utilidades/rasca_y_gana.json')
        print("\n[GUARDADO] grabaciones/utilidades/rasca_y_gana.json")
        self.pause()

    def check_and_scratch(self, scratch_data):
        detection_points = scratch_data.get('puntos_deteccion', [])
        det_tol = scratch_data.get('tolerancia_deteccion', 35)
        slots = scratch_data.get('ranuras', [])

        if not detection_points or not slots:
            return False

        matches = 0
        for point in detection_points:
            x, y = point['x'], point['y']
            expected = tuple(point['color_esperado'])
            actual = pyautogui.pixel(x, y)
            if self.compare_colors(actual, expected, det_tol):
                matches += 1

        required = max(3, int(len(detection_points) * 0.8))

        if matches >= required:
            print(f"\n   [SCRATCH DETECTADO] ({matches}/{len(detection_points)} puntos)")

            chosen_slot = random.choice(slots)
            num = chosen_slot.get('numero', slots.index(chosen_slot) + 1)
            slot_clicks = chosen_slot.get('clics', [])

            if not slot_clicks:
                return False

            print(f"   Ejecutando Ranura #{num} ({len(slot_clicks)} clics)")

            for click in slot_clicks:
                pyautogui.moveTo(click['x'], click['y'], duration=0.2)
                time.sleep(0.3)
                pyautogui.click()
                time.sleep(0.8)

            print(f"   [COMPLETADO] Ranura #{num}")
            time.sleep(1)
            return True

        return False

    def wait_and_click(self, click, index, total, tolerance, phase_name):
        x, y = click['x'], click['y']
        expected = tuple(click['color_esperado'])

        pyautogui.moveTo(x, y, duration=0.15)

        start_time = time.time()

        while True:
            if not self.verify_controls():
                return False

            if time.time() - start_time > self.MAX_WAIT_TIME:
                response = input(f"\n   [TIMEOUT] Clic {index}/{total}. Hacer clic? (s/n): ").strip().lower()
                if response != 's':
                    return False
                break

            actual = pyautogui.pixel(x, y)

            if self.compare_colors(actual, expected, tolerance):
                pyautogui.click()
                time.sleep(0.1)
                return True

            time.sleep(self.CHECK_INTERVAL)

    def play_sequence(self, data, phase_name):
        clicks = data.get('clics', [])
        tolerance = data.get('tolerancia', self.DEFAULT_TOLERANCE)

        if not clicks:
            return False

        print(f"\n{'=' * 70}")
        print(f"[EJECUTANDO] {phase_name}")
        print(f"{'=' * 70}")
        print(f"Acciones: {len(clicks)} | Tolerancia: +/-{tolerance}")

        for i, click in enumerate(clicks, 1):
            if not self.wait_and_click(click, i, len(clicks), tolerance, phase_name):
                return False

        print(f"[COMPLETADO] {phase_name}")
        return True

    def start_farming(self):
        self.paused = False

        self.display_header("INICIAR FARMEO")

        routines = self.list_routines()

        if not routines:
            print("\n[ERROR] No hay rutinas grabadas")
            print("Crea una rutina primero (Opcion 1)")
            self.pause()
            return

        print("\nRUTINAS DISPONIBLES:")
        print("=" * 70)
        for i, routine in enumerate(routines, 1):
            data = routine['data']
            print(f"{i}. {data['nombre']}")
            print(f"   Categoria: {data.get('categoria', 'N/A')}")
            print(f"   Clics: {data['total_clics']}")
            stats = data.get('estadisticas', {})
            if stats.get('total_ejecuciones', 0) > 0:
                avg_time = stats['tiempo_total'] / stats['total_ejecuciones']
                print(f"   Ejecutada: {stats['total_ejecuciones']} veces | Promedio: {round(avg_time / 60, 1)} min")
            print()
        print("=" * 70)

        choice = self.get_int_input("\nSelecciona rutina (0 para cancelar): ", 0, len(routines))
        if not choice:
            return
        selected_routine = routines[choice - 1]

        routine_data = selected_routine['data']

        if not os.path.exists('grabaciones/combate/jutsus_combo.json'):
            print("\n[ERROR] No hay jutsus grabados")
            print("Graba los jutsus primero (Opcion 4)")
            self.pause()
            return

        jutsus = self.load_json('grabaciones/combate/jutsus_combo.json')

        has_scratch = os.path.exists('grabaciones/utilidades/rasca_y_gana.json')
        scratch_data = None

        if has_scratch:
            scratch_data = self.load_json('grabaciones/utilidades/rasca_y_gana.json')
            num_slots = len(scratch_data.get('ranuras', []))
            if num_slots < 3:
                print(f"\n[ADVERTENCIA] Solo {num_slots}/3 slots grabados en scratch")

        print(f"\nCONFIGURACION")
        print("=" * 70)
        print(f"Rutina: {routine_data['nombre']}")
        print(f"Categoria: {routine_data.get('categoria', 'N/A')}")
        print(f"Jutsus: {jutsus['total_clics']} clics")
        if has_scratch:
            print("Scratch: Activado")
        print("=" * 70)

        self.pause()
        self.countdown()

        cycle = 1
        total_start = time.time()

        try:
            while True:
                print(f"\n{'=' * 70}")
                print(f"[CICLO #{cycle}]")
                print(f"{'=' * 70}")

                if not self.play_sequence(routine_data, routine_data['nombre'].upper()):
                    break

                if not self.play_sequence(jutsus, "COMBATE"):
                    break

                if has_scratch and scratch_data:
                    time.sleep(2)
                    self.check_and_scratch(scratch_data)

                print(f"\n[COMPLETADO] Ciclo #{cycle}")

                cycle += 1
                time.sleep(2)

        except KeyboardInterrupt:
            print("\n[INTERRUMPIDO]")
        except pyautogui.FailSafeException:
            print("\n[FAILSAFE ACTIVADO]")

        total_time = time.time() - total_start

        # Update stats
        stats = routine_data.get('estadisticas', {})
        stats['total_ejecuciones'] = stats.get('total_ejecuciones', 0) + (cycle - 1)
        stats['tiempo_total'] = stats.get('tiempo_total', 0) + total_time
        stats['ultima_ejecucion'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        routine_data['estadisticas'] = stats

        self.save_json(routine_data, selected_routine['path'])

        print(f"\nRESUMEN")
        print("=" * 70)
        print(f"Rutina: {routine_data['nombre']}")
        print(f"Ciclos completados: {cycle - 1}")
        print(f"Tiempo total: {round(total_time / 60, 1)} minutos")
        print(f"Tiempo promedio por ciclo: {round(total_time / max(cycle - 1, 1), 1)} segundos")
        print("=" * 70)

        self.pause()

    def view_routines(self):
        self.display_header("RUTINAS GUARDADAS")

        routines = self.list_routines()

        if not routines:
            print("\n[INFO] No hay rutinas guardadas")
            self.pause()
            return

        print(f"\nTotal de rutinas: {len(routines)}\n")

        for routine in routines:
            data = routine['data']
            print("=" * 70)
            print(f"NOMBRE: {data['nombre']}")
            print(f"Categoria: {data.get('categoria', 'N/A')}")
            print(f"Descripcion: {data.get('descripcion', 'N/A')}")
            print(f"Clics grabados: {data['total_clics']}")
            print(f"Tolerancia: +/-{data.get('tolerancia', self.DEFAULT_TOLERANCE)}")
            print(f"Creada: {data.get('fecha_creacion', 'N/A')}")

            stats = data.get('estadisticas', {})
            if stats:
                print(f"\nESTADISTICAS:")
                print(f"   - Veces ejecutada: {stats.get('total_ejecuciones', 0)}")
                if stats.get('total_ejecuciones', 0) > 0:
                    total_hrs = stats['tiempo_total'] / 3600
                    avg_time = stats['tiempo_total'] / stats['total_ejecuciones']
                    print(f"   - Tiempo total: {round(total_hrs, 2)} horas")
                    print(f"   - Tiempo promedio: {round(avg_time, 1)} segundos por ciclo")
                if stats.get('ultima_ejecucion'):
                    print(f"   - Ultima ejecucion: {stats['ultima_ejecucion']}")
            print()

        print("=" * 70)
        self.pause()

    def migrate_old_data(self):
        migrated = 0

        if os.path.exists('grabaciones/jefes'):
            for file in os.listdir('grabaciones/jefes'):
                if file.endswith('.json'):
                    old_path = f'grabaciones/jefes/{file}'
                    try:
                        old_data = self.load_json(old_path)

                        new_routine = {
                            'nombre': old_data.get('nombre', file.replace('.json', '')).replace('_', ' ').title(),
                            'categoria': 'Boss de Evento',
                            'descripcion': f'Migrado automaticamente desde {file}',
                            'tipo': 'deteccion_color',
                            'fecha_creacion': old_data.get('fecha', datetime.now().strftime('%Y-%m-%d %H:%M:%S')),
                            'fecha_modificacion': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                            'total_clics': old_data.get('total_clics', len(old_data.get('clics', []))),
                            'tolerancia': old_data.get('tolerancia', self.DEFAULT_TOLERANCE),
                            'clics': old_data.get('clics', []),
                            'estadisticas': {'total_ejecuciones': 0, 'tiempo_total': 0, 'ultima_ejecucion': None}
                        }

                        if not os.path.exists('grabaciones/rutinas'):
                            os.makedirs('grabaciones/rutinas')

                        filename = self.generate_filename(new_routine['nombre'])
                        new_path = f'grabaciones/rutinas/{filename}'

                        if not os.path.exists(new_path):
                            self.save_json(new_routine, new_path)
                            migrated += 1
                            print(f"   [MIGRADO] {new_routine['nombre']}")
                    except Exception as e:
                        print(f"   [ERROR] No se pudo migrar {file}: {e}")

        return migrated

    def check_initial_migration(self):
        has_old_bosses = False
        if os.path.exists('grabaciones/jefes'):
            files = [f for f in os.listdir('grabaciones/jefes') if f.endswith('.json')]
            if files:
                has_old_bosses = True

        has_new_routines = False
        if os.path.exists('grabaciones/rutinas'):
            files = [f for f in os.listdir('grabaciones/rutinas') if f.endswith('.json')]
            if files:
                has_new_routines = True

        if has_old_bosses and not has_new_routines:
            self.clear_screen()
            print("=" * 70)
            print("MIGRACION DE DATOS DETECTADA")
            print("=" * 70)
            print("\nSe detectaron grabaciones antiguas de jefes.")
            print("El sistema ahora usa RUTINAS PERSONALIZABLES.")
            print("\nDeseas migrar tus jefes antiguos al nuevo formato?")
            print("(Tus archivos antiguos NO se eliminaran)")

            if input("\nMigrar ahora? (s/n): ").strip().lower() == 's':
                print("\n[INICIANDO MIGRACION]")
                migrated = self.migrate_old_data()
                print(f"\n[COMPLETADO] {migrated} jefes migrados a rutinas")
                print("\nTus archivos antiguos siguen en: grabaciones/jefes/")
                print("Las nuevas rutinas estan en: grabaciones/rutinas/")
                self.pause()

    def migration_menu(self):
        self.display_header("MIGRACION DE DATOS ANTIGUOS")

        has_old = False
        if os.path.exists('grabaciones/jefes'):
            old_files = [f for f in os.listdir('grabaciones/jefes') if f.endswith('.json')]
            if old_files:
                has_old = True
                print(f"\nJefes antiguos detectados: {len(old_files)}")
                for f in old_files:
                    print(f"   - {f}")

        if not has_old:
            print("\n[INFO] No hay jefes antiguos para migrar")
            self.pause()
            return

        print("\n" + "=" * 70)
        print("OPCIONES")
        print("=" * 70)
        print("1. Migrar todos los jefes a rutinas")
        print("2. Cancelar")
        print("=" * 70)

        if self.get_choice("\nSelecciona (1-2): ", ['1', '2']) == '1':
            print("\n[INICIANDO MIGRACION]")
            migrated = self.migrate_old_data()
            print(f"\n[COMPLETADO] {migrated} jefes migrados")
            print("\nLos jefes antiguos siguen en: grabaciones/jefes/")
            print("Las nuevas rutinas estan en: grabaciones/rutinas/")

        self.pause()

    def main_menu(self):
        self.check_initial_migration()

        while True:
            self.clear_screen()
            print("=" * 70)
            print("SISTEMA DE FARMEO AUTOMATICO")
            print("=" * 70)

            print("\nMENU PRINCIPAL")
            print("=" * 70)
            print("1. Crear nueva rutina")
            print("2. Editar rutina existente")
            print("3. Eliminar rutina")
            print("4. Grabar secuencia de jutsus")
            print("5. Grabar rasca y gana")
            print("6. INICIAR FARMEO")
            print("7. Ver rutinas guardadas")
            print("8. Migrar jefes antiguos")
            print("9. Salir")
            print("=" * 70)

            print("\nSistema de rutinas personalizables | Deteccion multi-punto")

            choice = self.get_choice("\nSelecciona (1-9): ", [str(i) for i in range(1, 10)])

            if choice == '1':
                self.create_routine()
            elif choice == '2':
                self.edit_routine()
            elif choice == '3':
                self.delete_routine()
            elif choice == '4':
                self.record_jutsus()
            elif choice == '5':
                self.record_scratch_and_win()
            elif choice == '6':
                self.start_farming()
            elif choice == '7':
                self.view_routines()
            elif choice == '8':
                self.migration_menu()
            elif choice == '9':
                print("\nHasta luego")
                break

# ==================== EJECUTAR ====================

if __name__ == "__main__":
    try:
        autoclicker = AutoClicker()
        autoclicker.main_menu()
    except Exception as e:
        print(f"\n[ERROR CRITICO] {e}")
        import traceback
        traceback.print_exc()