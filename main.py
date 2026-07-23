# -*- coding: utf-8 -*-
"""
Área de Contabilidad - Lista de Compras
App tipo Excel hecha con Kivy (funciona en PC y Android).

Columnas: Producto | Coste del producto | Cantidad | Total por producto
Botón flotante "+" (abajo a la derecha) para agregar filas.
Celda final con la SUMA de todos los totales.
"""

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.graphics import Color, RoundedRectangle, Line
from kivy.core.window import Window
from kivy.metrics import dp
import sqlite3
import os

# ----------------------------------------------------------------------------
# PALETA DE COLORES (tomada de la imagen: cabecera azul-pizarra + fondo crema)
# ----------------------------------------------------------------------------
COL_FONDO      = (0.96, 0.94, 0.92, 1)   # crema de fondo
COL_CABECERA   = (0.38, 0.49, 0.53, 1)   # azul-pizarra de la cabecera
COL_TARJETA    = (0.99, 0.97, 0.97, 1)   # tarjeta rosada muy clara
COL_FILA_ENC   = (0.85, 0.83, 0.85, 1)   # fila de encabezados de columna
COL_CELDA      = (1, 1, 1, 1)            # celda de entrada blanca
COL_CELDA_ALT  = (0.97, 0.95, 0.95, 1)   # celda calculada (total por fila)
COL_TEXTO      = (0.20, 0.24, 0.27, 1)   # texto oscuro
COL_TEXTO_SUAVE = (0.45, 0.48, 0.50, 1)  # texto gris (números de fila)
COL_BORDE      = (0.80, 0.78, 0.80, 1)   # borde suave de celdas
COL_PRIMARIO   = (0.38, 0.49, 0.53, 1)   # botones principales
COL_PELIGRO    = (0.70, 0.35, 0.32, 1)   # botón borrar
COL_OK         = (0.36, 0.55, 0.44, 1)   # verde suave (guardar)

Window.clearcolor = COL_FONDO

# Anchos relativos de las columnas (deben sumar ~1.0)
ANCHO_NUM   = 0.08
ANCHO_PROD  = 0.34
ANCHO_COSTE = 0.19
ANCHO_CANT  = 0.15
ANCHO_TOTAL = 0.24


class CeldaTexto(TextInput):
    """Celda editable estilo Excel (fondo blanco, texto oscuro)."""

    def __init__(self, hint='', **kwargs):
        super().__init__(**kwargs)
        self.hint_text = hint
        self.multiline = False
        self.background_normal = ''
        self.background_active = ''
        self.background_color = COL_CELDA
        self.foreground_color = COL_TEXTO
        self.hint_text_color = COL_TEXTO_SUAVE
        self.cursor_color = COL_PRIMARIO
        self.font_size = dp(15)
        self.padding = [dp(8), dp(12), dp(8), dp(12)]
        self.write_tab = False
        self.halign = 'left'

        with self.canvas.after:
            Color(*COL_BORDE)
            self._borde = Line(width=1.1,
                               rounded_rectangle=(self.x, self.y,
                                                  self.width, self.height,
                                                  dp(4)))
        self.bind(size=self._act_borde, pos=self._act_borde)

    def _act_borde(self, *_):
        self._borde.rounded_rectangle = (self.x, self.y, self.width,
                                          self.height, dp(4))


class CeldaLabel(Label):
    """Celda de solo lectura con fondo redondeado."""

    def __init__(self, texto='', color_texto=COL_TEXTO,
                 color_fondo=COL_CELDA_ALT, negrita=False, **kwargs):
        super().__init__(**kwargs)
        self.text = texto
        self.color = color_texto
        self.bold = negrita
        self.font_size = dp(15)
        self.valign = 'center'
        self.halign = 'center'

        with self.canvas.before:
            Color(*color_fondo)
            self._rect = RoundedRectangle(size=self.size, pos=self.pos,
                                          radius=[dp(4)])
        self.bind(size=self._act_rect, pos=self._act_rect)
        self.text_size = self.size

    def _act_rect(self, *_):
        self._rect.pos = self.pos
        self._rect.size = self.size
        self.text_size = self.size


class BotonRedondo(Button):
    """Botón con fondo redondeado de color plano."""

    def __init__(self, color_fondo=COL_PRIMARIO, radio=8, **kwargs):
        super().__init__(**kwargs)
        self.background_normal = ''
        self.background_down = ''
        self.background_color = (0, 0, 0, 0)  # transparente: pintamos nosotros
        self._color_fondo = color_fondo
        self._radio = radio
        with self.canvas.before:
            self._col = Color(*color_fondo)
            self._rect = RoundedRectangle(size=self.size, pos=self.pos,
                                          radius=[dp(radio)])
        self.bind(size=self._act, pos=self._act,
                  state=self._act_estado)

    def _act(self, *_):
        self._rect.pos = self.pos
        self._rect.size = self.size

    def _act_estado(self, _inst, estado):
        # oscurece un poco al presionar
        r, g, b, a = self._color_fondo
        if estado == 'down':
            self._col.rgba = (r * 0.8, g * 0.8, b * 0.8, a)
        else:
            self._col.rgba = self._color_fondo


class FilaProducto(BoxLayout):
    """Una fila del 'Excel': #, Producto, Coste, Cantidad, Total."""

    def __init__(self, app_ref, fila_num, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'horizontal'
        self.size_hint_y = None
        self.height = dp(50)
        self.spacing = dp(3)
        self.app_ref = app_ref
        self.fila_num = fila_num

        self.lbl_num = CeldaLabel(texto=str(fila_num),
                                  color_texto=COL_TEXTO_SUAVE,
                                  color_fondo=COL_FILA_ENC)
        self.lbl_num.size_hint_x = ANCHO_NUM
        self.add_widget(self.lbl_num)

        self.txt_producto = CeldaTexto(hint='Producto')
        self.txt_producto.size_hint_x = ANCHO_PROD
        self.add_widget(self.txt_producto)

        self.txt_coste = CeldaTexto(hint='0.00')
        self.txt_coste.size_hint_x = ANCHO_COSTE
        self.txt_coste.input_filter = 'float'
        self.add_widget(self.txt_coste)

        self.txt_cantidad = CeldaTexto(hint='0')
        self.txt_cantidad.size_hint_x = ANCHO_CANT
        self.txt_cantidad.input_filter = 'float'
        self.add_widget(self.txt_cantidad)

        self.lbl_total = CeldaLabel(texto='$0.00',
                                    color_texto=COL_PRIMARIO,
                                    color_fondo=COL_CELDA_ALT,
                                    negrita=True)
        self.lbl_total.size_hint_x = ANCHO_TOTAL
        self.add_widget(self.lbl_total)

        self.txt_coste.bind(text=self.on_text_change)
        self.txt_cantidad.bind(text=self.on_text_change)

    def on_text_change(self, *_):
        self.calcular()
        if self.app_ref:
            self.app_ref.calcular_total_general()

    def calcular(self):
        coste, cant, total = self._valores()
        self.lbl_total.text = f'${total:.2f}'

    def _valores(self):
        try:
            coste = float(self.txt_coste.text) if self.txt_coste.text else 0.0
        except ValueError:
            coste = 0.0
        try:
            cant = float(self.txt_cantidad.text) if self.txt_cantidad.text else 0.0
        except ValueError:
            cant = 0.0
        return coste, cant, coste * cant

    def obtener_datos(self):
        prod = self.txt_producto.text.strip()
        coste, cant, total = self._valores()
        return prod, coste, cant, total

    def actualizar_numero(self, num):
        self.fila_num = num
        self.lbl_num.text = str(num)


class ComprasApp(App):

    def build(self):
        self.title = 'Área de Contabilidad'

        # Base de datos junto al ejecutable / directorio de la app
        db_path = os.path.join(self.user_data_dir if self._android()
                               else os.path.dirname(os.path.abspath(__file__)),
                               'compras.db')
        self.conn = sqlite3.connect(db_path)
        self.cursor = self.conn.cursor()
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS compras (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                producto TEXT,
                coste REAL,
                cantidad REAL,
                total REAL
            )
        ''')
        self.conn.commit()

        # Raiz flotante para poder poner el boton "+" encima de todo
        raiz = FloatLayout()

        main = BoxLayout(orientation='vertical', padding=dp(8), spacing=dp(6),
                         size_hint=(1, 1))

        # ---- Cabecera ----
        header = BoxLayout(size_hint_y=None, height=dp(70), padding=dp(8))
        with header.canvas.before:
            Color(*COL_CABECERA)
            header.rect = RoundedRectangle(size=header.size, pos=header.pos,
                                           radius=[dp(14)])
        header.bind(size=lambda i, v: setattr(header.rect, 'size', v),
                    pos=lambda i, v: setattr(header.rect, 'pos', v))
        titulo = Label(text='[b]Área de Contabilidad[/b]', markup=True,
                       font_size=dp(24), color=(1, 1, 1, 1))
        header.add_widget(titulo)
        main.add_widget(header)

        # ---- Barra de herramientas ----
        barra = BoxLayout(size_hint_y=None, height=dp(44), spacing=dp(6))

        btn_guardar = BotonRedondo(text='Guardar', color_fondo=COL_OK,
                                   font_size=dp(13), color=(1, 1, 1, 1))
        btn_guardar.bind(on_release=self.guardar_todo)

        btn_cargar = BotonRedondo(text='Cargar', color_fondo=COL_PRIMARIO,
                                  font_size=dp(13), color=(1, 1, 1, 1))
        btn_cargar.bind(on_release=self.ver_guardados)

        btn_limpiar = BotonRedondo(text='Limpiar', color_fondo=COL_TEXTO_SUAVE,
                                   font_size=dp(13), color=(1, 1, 1, 1))
        btn_limpiar.bind(on_release=self.limpiar_tabla)

        btn_borrar = BotonRedondo(text='Borrar BD', color_fondo=COL_PELIGRO,
                                  font_size=dp(13), color=(1, 1, 1, 1))
        btn_borrar.bind(on_release=self.borrar_bd)

        for b in (btn_guardar, btn_cargar, btn_limpiar, btn_borrar):
            barra.add_widget(b)
        main.add_widget(barra)

        # ---- Encabezado de columnas ----
        header_cols = BoxLayout(size_hint_y=None, height=dp(40), spacing=dp(3))
        cols = [('#', ANCHO_NUM), ('PRODUCTO', ANCHO_PROD),
                ('COSTE', ANCHO_COSTE), ('CANT.', ANCHO_CANT),
                ('TOTAL', ANCHO_TOTAL)]
        for nombre, ancho in cols:
            lbl = CeldaLabel(texto=nombre, color_texto=COL_TEXTO,
                             color_fondo=COL_FILA_ENC, negrita=True)
            lbl.size_hint_x = ancho
            header_cols.add_widget(lbl)
        main.add_widget(header_cols)

        # ---- Area de filas con scroll ----
        self.scroll = ScrollView()
        self.contenedor = GridLayout(cols=1, spacing=dp(3), size_hint_y=None,
                                     padding=[0, dp(2)])
        self.contenedor.bind(minimum_height=self.contenedor.setter('height'))
        self.scroll.add_widget(self.contenedor)
        main.add_widget(self.scroll)

        # ---- Total general (celda de suma) ----
        footer = BoxLayout(size_hint_y=None, height=dp(58), padding=dp(10))
        with footer.canvas.before:
            Color(*COL_CABECERA)
            footer.rect = RoundedRectangle(size=footer.size, pos=footer.pos,
                                           radius=[dp(14)])
        footer.bind(size=lambda i, v: setattr(footer.rect, 'size', v),
                    pos=lambda i, v: setattr(footer.rect, 'pos', v))
        self.lbl_total_general = Label(text='[b]TOTAL GENERAL:  $0.00[/b]',
                                       markup=True, font_size=dp(20),
                                       color=(1, 1, 1, 1))
        footer.add_widget(self.lbl_total_general)
        main.add_widget(footer)

        raiz.add_widget(main)

        # ---- Boton flotante "+" (abajo a la derecha) ----
        self.btn_add = BotonRedondo(text='+', color_fondo=COL_PRIMARIO,
                                    radio=32, font_size=dp(34),
                                    color=(1, 1, 1, 1),
                                    size_hint=(None, None),
                                    size=(dp(64), dp(64)),
                                    pos_hint={'right': 0.98, 'y': 0.11})
        self.btn_add.bind(on_release=self.agregar_nueva_fila)
        raiz.add_widget(self.btn_add)

        self.filas = []
        for _ in range(5):
            self.agregar_fila()

        return raiz

    # ---------- utilidades ----------
    def _android(self):
        return 'ANDROID_ARGUMENT' in os.environ

    def agregar_fila(self):
        num = len(self.filas) + 1
        fila = FilaProducto(self, num)
        self.filas.append(fila)
        self.contenedor.add_widget(fila)
        return fila

    def agregar_nueva_fila(self, *_):
        self.agregar_fila()
        self.scroll.scroll_y = 0

    def calcular_total_general(self):
        total = 0.0
        for fila in self.filas:
            _, _, t = fila._valores()
            total += t
        self.lbl_total_general.text = f'[b]TOTAL GENERAL:  ${total:.2f}[/b]'
        self.lbl_total_general.color = (1, 1, 1, 1)

    def guardar_todo(self, *_):
        guardados = 0
        for fila in self.filas:
            prod, coste, cant, total = fila.obtener_datos()
            if prod and cant > 0 and coste > 0:
                self.cursor.execute(
                    'INSERT INTO compras (producto, coste, cantidad, total) '
                    'VALUES (?, ?, ?, ?)', (prod, coste, cant, total))
                guardados += 1
        if guardados > 0:
            self.conn.commit()
            self.lbl_total_general.text = f'[b]GUARDADOS: {guardados} productos[/b]'
            self.lbl_total_general.color = (1, 0.93, 0.6, 1)
        else:
            self.lbl_total_general.text = '[b]NO HAY DATOS VALIDOS[/b]'
            self.lbl_total_general.color = (1, 0.8, 0.8, 1)

    def ver_guardados(self, *_):
        self.limpiar_tabla()
        datos = self.cursor.execute(
            'SELECT producto, coste, cantidad, total FROM compras').fetchall()
        while len(self.filas) < len(datos):
            self.agregar_fila()
        for i, (prod, coste, cant, total) in enumerate(datos):
            fila = self.filas[i]
            fila.txt_producto.text = prod or ''
            fila.txt_coste.text = str(coste)
            fila.txt_cantidad.text = str(cant)
            fila.lbl_total.text = f'${total:.2f}'
        self.calcular_total_general()

    def limpiar_tabla(self, *_):
        for fila in self.filas:
            fila.txt_producto.text = ''
            fila.txt_coste.text = ''
            fila.txt_cantidad.text = ''
            fila.lbl_total.text = '$0.00'
        self.lbl_total_general.text = '[b]TOTAL GENERAL:  $0.00[/b]'
        self.lbl_total_general.color = (1, 1, 1, 1)

    def borrar_bd(self, *_):
        self.cursor.execute('DELETE FROM compras')
        self.conn.commit()
        self.limpiar_tabla()
        self.lbl_total_general.text = '[b]BASE DE DATOS BORRADA[/b]'
        self.lbl_total_general.color = (1, 0.8, 0.8, 1)

    def on_stop(self):
        try:
            self.conn.close()
        except Exception:
            pass


if __name__ == '__main__':
    ComprasApp().run()
