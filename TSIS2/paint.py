import sys
from datetime import datetime
from math import sqrt
import pygame


class Paint:
    def __init__(self):
        pygame.init()  # Инициализация всех модулей Pygame

        # Тулбар делаем выше (135 px), чтобы текст статуса и ряды кнопок не накладывались друг на друга
        self.window_width = 960
        self.window_height = 700
        self.toolbar_height = 135
        self.canvas_width = self.window_width
        self.canvas_height = self.window_height - self.toolbar_height

        self.screen = pygame.display.set_mode(
            (self.window_width, self.window_height)
        )  # Создаём главное окно приложения
        pygame.display.set_caption("Paint Application")
        self.clock = pygame.time.Clock()

        self.font = pygame.font.SysFont("Verdana", 13)
        self.btn_font = pygame.font.SysFont("Verdana", 12, bold=True)
        self.text_font = pygame.font.SysFont("Verdana", 20)  # Отдельный шрифт для текста на холсте

        # Текущие настройки рисования
        self.radius = 5  # Толщина кисти / линий / фигур (2, 5 или 10 px)
        self.mode = "blue"  # Активный цвет: "red", "green" или "blue"
        self.tool = "brush"  # Активный инструмент: "brush", "pencil", "shape", "fill", "text"
        self.is_erace = False  # Флаг режима ластика

        # Отдельный холст (Surface) нужен, чтобы рисунки сохранялись, а временные превью их не портили
        self.canvas = pygame.Surface(
            (self.canvas_width, self.canvas_height)
        )
        self.canvas.fill((0, 0, 0))  # Заливаем холст чёрным фоном

        # Точки текущего штриха для кисти, карандаша и ластика
        self.cur_points = []

        # Состояние рисования фигур и прямой линии
        self.draw_shape = False  # Включён ли режим фигур/линии
        self.shape_type = 0  # 0..5 — фигуры, 6 — прямая линия
        self.start_pos = (0, 0)  # Координаты нажатия ЛКМ (начало фигуры)
        self.is_drawing_shape = False  # Идёт ли перетаскивание фигуры прямо сейчас
        self.current_mouse_pos = (0, 0)

        # Состояние инструмента «Текст»
        self.text = ""
        self.text_pos = (0, 0)
        self.is_typing = False  # True, когда курсор поставлен и пользователь вводит текст

        # Список словарей с описанием кнопок тулбара
        self.buttons = []
        self._build_buttons()

    def _build_buttons(self):
        #Создаёт прямоугольники (pygame.Rect) и действия для кнопок тулбара
        self.buttons.clear()
        y_row1 = 58
        y_row2 = 92
        h = 26

        # Первый ряд: цвета, ластик, толщина (2 / 5 / 10 px) и сохранение PNG
        row1_items = [
            (12, 68, "Red", "color_red", (170, 45, 45)),
            (86, 76, "Green", "color_green", (45, 145, 65)),
            (168, 68, "Blue", "color_blue", (45, 85, 175)),
            (252, 82, "Eraser", "toggle_eraser", (90, 90, 105)),
            (354, 62, "2 px", "size_2", (70, 70, 82)),
            (422, 62, "5 px", "size_5", (70, 70, 82)),
            (490, 66, "10 px", "size_10", (70, 70, 82)),
            (576, 92, "Save PNG", "save", (55, 110, 140)),
        ]
        for x, w, label, action, col in row1_items:
            self.buttons.append({
                "rect": pygame.Rect(x, y_row1, w, h),
                "label": label,
                "action": action,
                "color": col,
            })

        # Второй ряд: инструменты рисования и переключение фигур
        row2_items = [
            (12, 74, "Brush", "tool_brush", (70, 70, 82)),
            (92, 74, "Pencil", "tool_pencil", (70, 70, 82)),
            (172, 70, "Line", "tool_line", (70, 70, 82)),
            (248, 66, "Fill", "tool_fill", (70, 70, 82)),
            (320, 68, "Text", "tool_text", (70, 70, 82)),
            (394, 118, "Next Shape", "next_shape", (85, 75, 115)),
        ]
        for x, w, label, action, col in row2_items:
            self.buttons.append({
                "rect": pygame.Rect(x, y_row2, w, h),
                "label": label,
                "action": action,
                "color": col,
            })

    def _is_button_active(self, action):
        #Определяет, нужно ли подсветить кнопку как активную
        if action == "color_red" and self.mode == "red" and not self.is_erace:
            return True
        if action == "color_green" and self.mode == "green" and not self.is_erace:
            return True
        if action == "color_blue" and self.mode == "blue" and not self.is_erace:
            return True
        if action == "toggle_eraser" and self.is_erace:
            return True
        if action == "size_2" and self.radius == 2:
            return True
        if action == "size_5" and self.radius == 5:
            return True
        if action == "size_10" and self.radius == 10:
            return True
        if action == "tool_brush" and self.tool == "brush" and not self.is_erace:
            return True
        if action == "tool_pencil" and self.tool == "pencil" and not self.is_erace:
            return True
        if action == "tool_line" and self.draw_shape and self.shape_type == 6:
            return True
        if action == "tool_fill" and self.tool == "fill":
            return True
        if action == "tool_text" and self.tool == "text":
            return True
        if action == "next_shape" and self.draw_shape and self.shape_type != 6:
            return True
        return False

    def _handle_button_action(self, action):
        #Обрабатывает клик по кнопке и переключает соответствующее состояние
        if self.is_typing and action != "tool_text":
            self.is_typing = False
            self.text = ""

        if action == "color_red":
            self.mode = "red"
            self.is_erace = False
        elif action == "color_green":
            self.mode = "green"
            self.is_erace = False
        elif action == "color_blue":
            self.mode = "blue"
            self.is_erace = False
        elif action == "toggle_eraser":
            self.is_erace = not self.is_erace
            if self.is_erace:
                self.draw_shape = False
        elif action == "size_2":
            self.radius = 2
        elif action == "size_5":
            self.radius = 5
        elif action == "size_10":
            self.radius = 10
        elif action == "save":
            self.save_canvas()
        elif action == "tool_brush":
            self.tool = "brush"
            self.draw_shape = False
            self.is_erace = False
        elif action == "tool_pencil":
            self.tool = "pencil"
            self.draw_shape = False
            self.is_erace = False
        elif action == "tool_line":
            self.tool = "shape"
            self.draw_shape = True
            self.shape_type = 6  # Индекс 6 соответствует прямой линии
            self.is_erace = False
        elif action == "tool_fill":
            self.tool = "fill"
            self.draw_shape = False
            self.is_erace = False
        elif action == "tool_text":
            self.tool = "text"
            self.draw_shape = False
            self.is_erace = False
            self.is_typing = False
            self.text = ""
        elif action == "next_shape":
            self.tool = "shape"
            self.is_erace = False
            # Переключаем фигуры по кругу (0..5), пропуская прямую линию (6)
            if not self.draw_shape or self.shape_type == 6:
                self.draw_shape = True
                self.shape_type = 0
            else:
                self.shape_type = (self.shape_type + 1) % 6

    def get_color(self):
        #Возвращает RGB-кортеж активного цвета
        if self.mode == "blue":
            return (0, 0, 255)
        elif self.mode == "red":
            return (255, 0, 0)
        return (0, 255, 0)

    def to_canvas_pos(self, screen_pos):
        #Сдвигает координату Y на высоту тулбара: (0, 0) холста — левый верхний угол под панелью
        return (
            screen_pos[0],
            screen_pos[1] - self.toolbar_height
        )

    def is_on_canvas(self, screen_pos):
        #Проверяет, что курсор находится в области холста, а не на тулбаре
        x, y = screen_pos
        return (
            0 <= x < self.canvas_width
            and self.toolbar_height <= y < self.window_height
        )

    def drawLineBetween(self, start, end, radius):
        #Интерполирует точки между start и end и рисует круги, чтобы штрих не рвался при быстром движении
        color = self.get_color()
        dx = start[0] - end[0]
        dy = start[1] - end[1]
        iterations = max(abs(dx), abs(dy))

        if iterations == 0:
            pygame.draw.circle(self.canvas, color, start, radius)
            return

        for i in range(iterations + 1):
            progress = float(i) / iterations
            x = int(start[0] + progress * (end[0] - start[0]))
            y = int(start[1] + progress * (end[1] - start[1]))
            pygame.draw.circle(self.canvas, color, (x, y), radius)

    def drawPencil(self, start, end, radius):
        #Рисует прямой отрезок карандашом между двумя соседними позициями курсора
        pygame.draw.line(
            self.canvas, self.get_color(), start, end, max(1, radius)
        )

    def eraser(self, start, end, radius):
        #Стирает штрих, рисуя поверх него цветом фона (0, 0, 0)
        dx = start[0] - end[0]
        dy = start[1] - end[1]
        iterations = max(abs(dx), abs(dy))

        if iterations == 0:
            pygame.draw.circle(self.canvas, (0, 0, 0), start, radius)
            return

        for i in range(iterations + 1):
            progress = float(i) / iterations
            x = int(start[0] + progress * (end[0] - start[0]))
            y = int(start[1] + progress * (end[1] - start[1]))
            pygame.draw.circle(self.canvas, (0, 0, 0), (x, y), radius)

    def flood_fill(self, x, y, new_color):
        #Заливает замкнутую область пикселей одного цвета с помощью итеративного обхода в глубину (стек)
        if not (0 <= x < self.canvas_width and 0 <= y < self.canvas_height):
            return

        target_rgb = self.canvas.get_at((x, y))[:3]  # Берём только RGB без альфа-канала
        if target_rgb == new_color:
            return  # Не заливаем, если кликнули по уже нужному цвету

        visited = set()  # Защита от повторной обработки одних и тех же пикселей
        stack = [(x, y)]

        while stack:
            cx, cy = stack.pop()
            if (cx, cy) in visited:
                continue
            if not (0 <= cx < self.canvas_width and 0 <= cy < self.canvas_height):
                continue

            if self.canvas.get_at((cx, cy))[:3] == target_rgb:
                visited.add((cx, cy))
                self.canvas.set_at((cx, cy), new_color)

                # Добавляем 4 соседних пикселя (вверх, вниз, влево, вправо)
                stack.append((cx + 1, cy))
                stack.append((cx - 1, cy))
                stack.append((cx, cy + 1))
                stack.append((cx, cy - 1))

    def render_text_to_canvas(self):
        #Фиксирует введённый текст на постоянном холсте и сбрасывает режим ввода
        if self.text:
            text_surface = self.text_font.render(
                self.text, True, self.get_color()
            )
            self.canvas.blit(text_surface, self.text_pos)

        self.is_typing = False
        self.text = ""

    def draw_figure(
        self, surface, figure_type, start, end, color, thickness,
        offset=(0, 0)
    ):
        #Рисует выбранную фигуру или линию на указанной поверхности (холст или экран для превью)
        x1, y1 = start
        x2, y2 = end

        left = min(x1, x2)
        right = max(x1, x2)
        top = min(y1, y2)
        bottom = max(y1, y2)

        width = right - left
        height = bottom - top
        ox, oy = offset  # Смещение нужно при рисовании превью прямо на self.screen

        def point(x, y):
            return (x + ox, y + oy)

        line_width = max(1, thickness)

        if figure_type == 0:  # Прямоугольник
            pygame.draw.rect(
                surface, color,
                (left + ox, top + oy, width, height),
                line_width
            )
        elif figure_type == 1:  # Прямоугольный треугольник
            pygame.draw.polygon(
                surface, color,
                [point(left, top), point(left, bottom), point(right, bottom)],
                line_width
            )
        elif figure_type == 2:  # Равнобедренный треугольник
            pygame.draw.polygon(
                surface, color,
                [point((left + right) // 2, top), point(left, bottom), point(right, bottom)],
                line_width
            )
        elif figure_type == 3:  # Ромб
            pygame.draw.polygon(
                surface, color,
                [
                    point((left + right) // 2, top),
                    point(right, (top + bottom) // 2),
                    point((left + right) // 2, bottom),
                    point(left, (top + bottom) // 2)
                ],
                line_width
            )
        elif figure_type == 4:  # Окружность
            center_x = (x1 + x2) // 2
            center_y = (y1 + y2) // 2
            circle_radius = int(sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2) / 2)
            if circle_radius > 0:
                pygame.draw.circle(
                    surface, color, point(center_x, center_y),
                    circle_radius, line_width
                )
        elif figure_type == 5:  # Квадрат (сторона равна меньшей из ширины/высоты)
            side = min(width, height)
            square_left = x1 - side if x2 < x1 else x1
            square_top = y1 - side if y2 < y1 else y1
            pygame.draw.rect(
                surface, color,
                (square_left + ox, square_top + oy, side, side),
                line_width
            )
        elif figure_type == 6:  # Прямая линия
            pygame.draw.line(
                surface, color, point(x1, y1), point(x2, y2),
                line_width
            )

    def save_canvas(self):
        #Сохраняет только холст (без тулбара) в PNG с уникальной меткой времени
        now = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        filename = f"paint_{now}.png"
        pygame.image.save(self.canvas, filename)
        print("Canvas saved as:", filename)

    def draw_toolbar(self):
        #Отрисовывает верхнюю панель: подсказки, статус и интерактивные кнопки
        pygame.draw.rect(
            self.screen, (36, 36, 44),
            (0, 0, self.window_width, self.toolbar_height)
        )
        pygame.draw.line(
            self.screen, (95, 95, 110),
            (0, self.toolbar_height - 1),
            (self.window_width, self.toolbar_height - 1), 2
        )

        hints = (
            "Keys: R/G/B Color | F Brush | P Pencil | L Line | N Fill | "
            "T Text | D Shape | 1/2/3 Size | W Eraser | Ctrl+S Save | RMB Cancel"
        )
        self.screen.blit(self.font.render(hints, True, (225, 225, 235)), (12, 8))

        tool_name = self.tool.upper()
        if self.draw_shape:
            shape_names = [
                "Rectangle", "Right triangle", "Triangle",
                "Rhombus", "Circle", "Square", "Straight line"
            ]
            tool_name = shape_names[self.shape_type]

        status = (
            f"Current: {tool_name}  |  Color: {self.mode.upper()}  |  "
            f"Size: {self.radius} px  |  Eraser: {'ON' if self.is_erace else 'OFF'}"
        )
        self.screen.blit(self.font.render(status, True, (255, 220, 120)), (12, 30))

        # Рисуем каждую кнопку с учётом активного состояния и наведения курсора
        mouse_pos = self.current_mouse_pos
        for btn in self.buttons:
            rect = btn["rect"]
            active = self._is_button_active(btn["action"])
            hovered = rect.collidepoint(mouse_pos)

            if active:
                fill_col = (240, 185, 50)
                text_col = (20, 20, 25)
                border_col = (255, 240, 170)
            elif hovered:
                fill_col = tuple(min(255, c + 30) for c in btn["color"])
                text_col = (255, 255, 255)
                border_col = (190, 190, 210)
            else:
                fill_col = btn["color"]
                text_col = (245, 245, 250)
                border_col = (120, 120, 140)

            pygame.draw.rect(self.screen, fill_col, rect, border_radius=5)
            pygame.draw.rect(self.screen, border_col, rect, width=1, border_radius=5)

            lbl = self.btn_font.render(btn["label"], True, text_col)
            lbl_rect = lbl.get_rect(center=rect.center)
            self.screen.blit(lbl, lbl_rect)

    def run(self):
        while True:
            self.current_mouse_pos = pygame.mouse.get_pos()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()

                # Пока активен ввод текста, клавиши идут в строку текста, а не в горячие клавиши инструментов
                if event.type == pygame.KEYDOWN and self.is_typing:
                    if event.key == pygame.K_RETURN:
                        self.render_text_to_canvas()
                    elif event.key == pygame.K_ESCAPE:
                        self.is_typing = False
                        self.text = ""
                    elif event.key == pygame.K_BACKSPACE:
                        self.text = self.text[:-1]
                    elif event.unicode and event.unicode.isprintable():
                        self.text += event.unicode
                    continue

                if event.type == pygame.KEYDOWN:
                    if (
                        event.key == pygame.K_s
                        and (event.mod & (pygame.KMOD_CTRL | pygame.KMOD_LCTRL | pygame.KMOD_RCTRL))
                    ):
                        self.save_canvas()  # Сохранение по Ctrl+S
                    elif event.key == pygame.K_r:
                        self.mode = "red"
                        self.is_erace = False
                    elif event.key == pygame.K_g:
                        self.mode = "green"
                        self.is_erace = False
                    elif event.key == pygame.K_b:
                        self.mode = "blue"
                        self.is_erace = False
                    elif event.key == pygame.K_w:
                        self.is_erace = not self.is_erace
                    elif event.key == pygame.K_p:
                        self.tool = "pencil"
                        self.draw_shape = False
                        self.is_erace = False
                    elif event.key == pygame.K_f:
                        self.tool = "brush"
                        self.draw_shape = False
                        self.is_erace = False
                    elif event.key == pygame.K_n:
                        self.tool = "fill"
                        self.draw_shape = False
                        self.is_erace = False
                    elif event.key == pygame.K_t:
                        self.tool = "text"
                        self.draw_shape = False
                        self.is_erace = False
                        self.is_typing = False
                        self.text = ""
                    elif event.key == pygame.K_l:
                        self.tool = "shape"
                        self.draw_shape = True
                        self.shape_type = 6
                        self.is_erace = False
                    elif event.key == pygame.K_d:
                        self.tool = "shape"
                        self.is_erace = False
                        if not self.draw_shape or self.shape_type == 6:
                            self.draw_shape = True
                            self.shape_type = 0
                        else:
                            self.shape_type = (self.shape_type + 1) % 6
                    elif event.key == pygame.K_1:
                        self.radius = 2
                    elif event.key == pygame.K_2:
                        self.radius = 5
                    elif event.key == pygame.K_3:
                        self.radius = 10

                if event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 3:  # Правая кнопка мыши отменяет фигуру или ввод текста
                        self.draw_shape = False
                        self.is_drawing_shape = False
                        self.is_typing = False
                        self.text = ""

                    elif event.button == 1:  # Левая кнопка мыши
                        clicked_button = False
                        for btn in self.buttons:
                            if btn["rect"].collidepoint(event.pos):
                                self._handle_button_action(btn["action"])
                                clicked_button = True
                                break

                        # Рисуем на холсте только если клик был не по кнопке тулбара
                        if not clicked_button and self.is_on_canvas(event.pos):
                            canvas_pos = self.to_canvas_pos(event.pos)

                            if self.tool == "fill":
                                self.flood_fill(
                                    canvas_pos[0], canvas_pos[1],
                                    self.get_color()
                                )
                            elif self.tool == "text":
                                if self.is_typing and self.text:
                                    self.render_text_to_canvas()
                                self.text_pos = canvas_pos
                                self.text = ""
                                self.is_typing = True
                            elif self.draw_shape:
                                self.start_pos = canvas_pos
                                self.current_mouse_pos = canvas_pos
                                self.is_drawing_shape = True
                            elif self.tool in ("brush", "pencil"):
                                self.cur_points = [canvas_pos]

                if event.type == pygame.MOUSEBUTTONUP:
                    if event.button == 1:
                        # При отпускании ЛКМ фиксируем фигуру окончательно на self.canvas
                        if self.is_drawing_shape:
                            if self.is_on_canvas(event.pos):
                                end_pos = self.to_canvas_pos(event.pos)
                                self.draw_figure(
                                    self.canvas, self.shape_type,
                                    self.start_pos, end_pos,
                                    self.get_color(), self.radius
                                )
                            self.is_drawing_shape = False
                        self.cur_points = []

                if event.type == pygame.MOUSEMOTION:
                    if event.buttons[0] and self.cur_points:
                        if self.is_on_canvas(event.pos):
                            position = self.to_canvas_pos(event.pos)
                            previous = self.cur_points[-1]

                            if self.is_erace:
                                self.eraser(previous, position, self.radius)
                            elif self.tool == "pencil":
                                self.drawPencil(previous, position, self.radius)
                            elif self.tool == "brush":
                                self.drawLineBetween(previous, position, self.radius)

                            self.cur_points.append(position)

                    if self.is_drawing_shape and self.is_on_canvas(event.pos):
                        self.current_mouse_pos = self.to_canvas_pos(event.pos)

            # Порядок отрисовки важен: сначала холст, сверху тулбар, затем временные превью
            self.screen.fill((0, 0, 0))
            self.screen.blit(self.canvas, (0, self.toolbar_height))
            self.draw_toolbar()

            # Живое превью фигуры/линии рисуется на self.screen, не пачкая self.canvas до отпускания мыши
            if self.is_drawing_shape:
                self.draw_figure(
                    self.screen, self.shape_type,
                    self.start_pos, self.current_mouse_pos,
                    self.get_color(), self.radius,
                    offset=(0, self.toolbar_height)
                )

            # Превью набираемого текста с мигающим/статичным курсором "|"
            if self.is_typing:
                preview = self.text_font.render(
                    self.text + "|", True, self.get_color()
                )
                text_screen_pos = (
                    self.text_pos[0],
                    self.text_pos[1] + self.toolbar_height
                )
                self.screen.blit(preview, text_screen_pos)

            pygame.display.flip()  # Обновляем экран целиком
            self.clock.tick(60)  # Ограничиваем частоту кадров до 60 FPS


if __name__ == "__main__":
    game = Paint()
    game.run()