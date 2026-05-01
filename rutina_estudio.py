"""
Sistema de Recomendación de Rutinas de Estudio — Con Interfaz Gráfica en
Tkinter + historial de sesiones en JSON local 
Instituto Tecnológico de Ensenada — Inteligencia Artificial
Daniela Guadalupe Hernández Guzmán (21760148)
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import json
import os
from datetime import datetime, timedelta

#  CONSTANTES

HISTORIAL_FILE = "historial_rutinas.json"

COLORES = {
    "fondo":        "#0f1117",
    "panel":        "#1a1d27",
    "panel2":       "#22253a",
    "acento":       "#6c63ff",
    "acento2":      "#a78bfa",
    "texto":        "#e8e8f0",
    "texto_suave":  "#8888aa",
    "estudio":      "#6c63ff",
    "descanso":     "#22c55e",
    "repaso":       "#f59e0b",
    "advertencia":  "#ef4444",
    "borde":        "#2e3150",
}

ETIQUETAS_DIF = {1: "Fácil", 2: "Moderada", 3: "Media", 4: "Alta", 5: "Muy alta"}
COLOR_DIF = {1: "#22c55e", 2: "#84cc16", 3: "#f59e0b", 4: "#f97316", 5: "#ef4444"}

FUENTE_TITULO  = ("Segoe UI", 15, "bold")
FUENTE_SUB     = ("Segoe UI", 11, "bold")
FUENTE_NORMAL  = ("Segoe UI", 10)
FUENTE_SMALL   = ("Segoe UI", 9)
FUENTE_MONO    = ("Consolas", 10)



#  MOTOR DE REGLAS (reutilizado del CLI)

def calcular_pesos(materias):
    total_dif = sum(m["dificultad"] for m in materias)
    for m in materias:
        m["peso"] = m["dificultad"] / total_dif
    return materias

def generar_rutina(materias, tiempo_total, duracion_descanso, repaso_final):
    n = len(materias)
    materias = calcular_pesos(materias)

    num_descansos = n - 1
    tiempo_descansos = num_descansos * duracion_descanso
    tiempo_repaso = max(5, int(tiempo_total * 0.10)) if repaso_final else 0
    tiempo_estudio = tiempo_total - tiempo_descansos - tiempo_repaso

    advertencias = []
    if tiempo_estudio <= 0:
        tiempo_descansos = 0
        num_descansos = 0
        tiempo_estudio = tiempo_total - tiempo_repaso
        advertencias.append("Tiempo muy corto — se omitieron descansos intermedios.")

    minimo = 5
    if tiempo_estudio < n * minimo:
        advertencias.append(
            f"Solo {tiempo_estudio} min de estudio para {n} materia(s). "
            "Considera reducir materias o aumentar el tiempo."
        )

    bloques = []
    asignado = 0
    for i, m in enumerate(materias):
        if i < n - 1:
            mins = max(minimo, round(m["peso"] * tiempo_estudio))
        else:
            mins = max(minimo, tiempo_estudio - asignado)
        asignado += mins
        bloques.append({"tipo": "estudio", "materia": m["nombre"],
                        "dificultad": m["dificultad"], "duracion": mins})
        if i < n - 1 and num_descansos > 0:
            bloques.append({"tipo": "descanso", "materia": None,
                            "duracion": duracion_descanso})

    if repaso_final and tiempo_repaso > 0:
        bloques.append({"tipo": "repaso", "materia": "Repaso general",
                        "duracion": tiempo_repaso})

    return bloques, advertencias



#  HISTORIAL


def cargar_historial():
    if os.path.exists(HISTORIAL_FILE):
        try:
            with open(HISTORIAL_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return []

def guardar_en_historial(materias, tiempo_total, duracion_descanso, repaso_final, bloques):
    historial = cargar_historial()
    entrada = {
        "fecha": datetime.now().strftime("%d/%m/%Y %H:%M"),
        "tiempo_total": tiempo_total,
        "duracion_descanso": duracion_descanso,
        "repaso_final": repaso_final,
        "materias": materias,
        "bloques": bloques,
    }
    historial.insert(0, entrada)
    historial = historial[:50]  # Máximo 50 sesiones guardadas
    with open(HISTORIAL_FILE, "w", encoding="utf-8") as f:
        json.dump(historial, f, ensure_ascii=False, indent=2)



#  WIDGETS REUTILIZABLES


def entry_style(parent, **kwargs):
    """Entry con estilo oscuro."""
    e = tk.Entry(
        parent,
        bg=COLORES["panel2"], fg=COLORES["texto"],
        insertbackground=COLORES["acento"],
        relief="flat", bd=0,
        font=FUENTE_NORMAL,
        highlightthickness=1,
        highlightcolor=COLORES["acento"],
        highlightbackground=COLORES["borde"],
        **kwargs
    )
    return e

def btn_style(parent, texto, comando, color=None, **kwargs):
    color = color or COLORES["acento"]
    b = tk.Button(
        parent, text=texto, command=comando,
        bg=color, fg="white",
        activebackground=COLORES["acento2"],
        activeforeground="white",
        relief="flat", bd=0,
        font=("Segoe UI", 10, "bold"),
        cursor="hand2",
        padx=14, pady=7,
        **kwargs
    )
    return b

def label(parent, texto, fuente=None, color=None, **kwargs):
    return tk.Label(
        parent, text=texto,
        bg=COLORES["fondo"],
        fg=color or COLORES["texto"],
        font=fuente or FUENTE_NORMAL,
        **kwargs
    )



#  VENTANA: FILA DE MATERIA


class FilaMateria(tk.Frame):
    """Una fila con nombre + slider de dificultad + botón eliminar."""

    def __init__(self, parent, numero, on_delete, **kwargs):
        super().__init__(parent, bg=COLORES["panel2"], pady=6, padx=8, **kwargs)
        self.on_delete = on_delete

        # Número
        tk.Label(self, text=f"{numero}.", bg=COLORES["panel2"],
                 fg=COLORES["texto_suave"], font=FUENTE_SMALL, width=2).pack(side="left")

        # Nombre
        self.entry_nombre = tk.Entry(
            self, bg=COLORES["fondo"], fg=COLORES["texto"],
            insertbackground=COLORES["acento"],
            relief="flat", font=FUENTE_NORMAL,
            highlightthickness=1,
            highlightcolor=COLORES["acento"],
            highlightbackground=COLORES["borde"],
            width=22
        )
        self.entry_nombre.pack(side="left", padx=(4, 10))
        self.entry_nombre.insert(0, "")

        # Slider dificultad
        tk.Label(self, text="Dificultad:", bg=COLORES["panel2"],
                 fg=COLORES["texto_suave"], font=FUENTE_SMALL).pack(side="left")

        self.var_dif = tk.IntVar(value=3)
        self.slider = tk.Scale(
            self, from_=1, to=5, orient="horizontal",
            variable=self.var_dif, length=100,
            bg=COLORES["panel2"], fg=COLORES["texto"],
            troughcolor=COLORES["borde"],
            highlightthickness=0, showvalue=False,
            command=self._update_label
        )
        self.slider.pack(side="left", padx=(4, 4))

        self.lbl_dif = tk.Label(
            self, text="Media", bg=COLORES["panel2"],
            fg=COLOR_DIF[3], font=("Segoe UI", 9, "bold"), width=8
        )
        self.lbl_dif.pack(side="left")

        # Botón eliminar
        tk.Button(
            self, text="✕", command=self._eliminar,
            bg=COLORES["panel2"], fg="#ef4444",
            activebackground=COLORES["panel2"],
            relief="flat", font=("Segoe UI", 11, "bold"),
            cursor="hand2", bd=0
        ).pack(side="left", padx=(6, 0))

    def _update_label(self, _=None):
        v = self.var_dif.get()
        self.lbl_dif.config(text=ETIQUETAS_DIF[v], fg=COLOR_DIF[v])

    def _eliminar(self):
        self.on_delete(self)

    def obtener(self):
        nombre = self.entry_nombre.get().strip()
        return {"nombre": nombre, "dificultad": self.var_dif.get()}



#  VENTANA PRINCIPAL


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Rutinas de Estudio — IA")
        self.geometry("860x680")
        self.minsize(820, 600)
        self.configure(bg=COLORES["fondo"])

        self._filas_materias = []
        self._bloques_actuales = []
        self._materias_actuales = []

        self._build_ui()

    # ── Construcción de la interfaz ──

    def _build_ui(self):
        # Notebook (pestañas)
        style = ttk.Style(self)
        style.theme_use("default")
        style.configure("TNotebook", background=COLORES["fondo"], borderwidth=0)
        style.configure("TNotebook.Tab",
                        background=COLORES["panel"], foreground=COLORES["texto_suave"],
                        padding=[16, 8], font=FUENTE_NORMAL)
        style.map("TNotebook.Tab",
                  background=[("selected", COLORES["panel2"])],
                  foreground=[("selected", COLORES["acento2"])])

        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True, padx=0, pady=0)

        self.tab_nueva   = tk.Frame(self.notebook, bg=COLORES["fondo"])
        self.tab_rutina  = tk.Frame(self.notebook, bg=COLORES["fondo"])
        self.tab_hist    = tk.Frame(self.notebook, bg=COLORES["fondo"])

        self.notebook.add(self.tab_nueva,  text="  ✏️  Nueva sesión  ")
        self.notebook.add(self.tab_rutina, text="  📋  Rutina generada  ")
        self.notebook.add(self.tab_hist,   text="  🕓  Historial  ")

        self._build_tab_nueva()
        self._build_tab_rutina()
        self._build_tab_historial()

    # ── Tab 1: Nueva sesión ──

    def _build_tab_nueva(self):
        p = self.tab_nueva
        pad = {"padx": 24, "pady": 6}

        # Título
        tk.Label(p, text="Sistema de Recomendación de Rutinas de Estudio",
                 bg=COLORES["fondo"], fg=COLORES["acento2"],
                 font=("Segoe UI", 14, "bold")).pack(pady=(20, 2))
        tk.Label(p, text="Instituto Tecnológico de Ensenada · Inteligencia Artificial",
                 bg=COLORES["fondo"], fg=COLORES["texto_suave"],
                 font=FUENTE_SMALL).pack(pady=(0, 14))

        # ── Panel materias ──
        frm_mat = tk.LabelFrame(
            p, text="  Materias a estudiar  ",
            bg=COLORES["panel"], fg=COLORES["acento2"],
            font=FUENTE_SUB, bd=0, relief="flat",
            highlightthickness=1, highlightbackground=COLORES["borde"]
        )
        frm_mat.pack(fill="x", **pad)

        # Área scrollable de materias
        self.canvas_mat = tk.Canvas(frm_mat, bg=COLORES["panel"],
                                    highlightthickness=0, height=180)
        scrollbar = tk.Scrollbar(frm_mat, orient="vertical",
                                 command=self.canvas_mat.yview)
        self.canvas_mat.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        self.canvas_mat.pack(side="left", fill="both", expand=True)

        self.frm_filas = tk.Frame(self.canvas_mat, bg=COLORES["panel"])
        self.canvas_mat.create_window((0, 0), window=self.frm_filas, anchor="nw")
        self.frm_filas.bind("<Configure>",
            lambda e: self.canvas_mat.configure(
                scrollregion=self.canvas_mat.bbox("all")))

        # Botón agregar materia
        btn_style(frm_mat, "+ Agregar materia", self._agregar_fila,
                  color="#22253a").pack(anchor="w", padx=10, pady=8)

        # Agregar 2 filas por defecto
        self._agregar_fila()
        self._agregar_fila()

        # ── Panel preferencias ──
        frm_pref = tk.LabelFrame(
            p, text="  Preferencias de sesión  ",
            bg=COLORES["panel"], fg=COLORES["acento2"],
            font=FUENTE_SUB, bd=0, relief="flat",
            highlightthickness=1, highlightbackground=COLORES["borde"]
        )
        frm_pref.pack(fill="x", **pad)

        fila1 = tk.Frame(frm_pref, bg=COLORES["panel"])
        fila1.pack(fill="x", padx=10, pady=8)

        # Tiempo disponible
        tk.Label(fila1, text="Tiempo disponible (min):",
                 bg=COLORES["panel"], fg=COLORES["texto"],
                 font=FUENTE_NORMAL).pack(side="left")
        self.var_tiempo = tk.IntVar(value=60)
        spin = tk.Spinbox(
            fila1, from_=10, to=480, textvariable=self.var_tiempo,
            width=5, font=FUENTE_NORMAL,
            bg=COLORES["panel2"], fg=COLORES["texto"],
            buttonbackground=COLORES["borde"],
            relief="flat", insertbackground=COLORES["acento"]
        )
        spin.pack(side="left", padx=(8, 30))

        # Descanso
        tk.Label(fila1, text="Descanso entre materias:",
                 bg=COLORES["panel"], fg=COLORES["texto"],
                 font=FUENTE_NORMAL).pack(side="left")
        self.var_descanso = tk.IntVar(value=10)
        for val, txt in [(5, "5 min"), (10, "10 min"), (15, "15 min")]:
            tk.Radiobutton(
                fila1, text=txt, variable=self.var_descanso, value=val,
                bg=COLORES["panel"], fg=COLORES["texto"],
                selectcolor=COLORES["panel2"],
                activebackground=COLORES["panel"],
                font=FUENTE_NORMAL
            ).pack(side="left", padx=4)

        fila2 = tk.Frame(frm_pref, bg=COLORES["panel"])
        fila2.pack(fill="x", padx=10, pady=(0, 8))

        self.var_repaso = tk.BooleanVar(value=True)
        tk.Checkbutton(
            fila2, text="Incluir bloque de repaso general al final",
            variable=self.var_repaso,
            bg=COLORES["panel"], fg=COLORES["texto"],
            selectcolor=COLORES["panel2"],
            activebackground=COLORES["panel"],
            font=FUENTE_NORMAL
        ).pack(side="left")

        # Botón generar
        btn_style(p, " Generar Rutina", self._generar).pack(pady=16)

    def _agregar_fila(self):
        n = len(self._filas_materias) + 1
        fila = FilaMateria(self.frm_filas, n, self._eliminar_fila)
        fila.pack(fill="x", pady=2, padx=4)
        self._filas_materias.append(fila)

    def _eliminar_fila(self, fila):
        if len(self._filas_materias) <= 1:
            messagebox.showwarning("Atención", "Necesitas al menos una materia.")
            return
        self._filas_materias.remove(fila)
        fila.destroy()
        # Renumerar
        for i, f in enumerate(self._filas_materias):
            f.winfo_children()[0].config(text=f"{i+1}.")

    def _generar(self):
        # Recopilar materias
        materias = []
        for fila in self._filas_materias:
            d = fila.obtener()
            if d["nombre"]:
                materias.append(d)

        if not materias:
            messagebox.showwarning("Sin materias", "Agrega al menos una materia con nombre.")
            return

        try:
            tiempo = int(self.var_tiempo.get())
            if not (10 <= tiempo <= 480):
                raise ValueError
        except (ValueError, tk.TclError):
            messagebox.showwarning("Tiempo inválido", "El tiempo debe ser entre 10 y 480 minutos.")
            return

        descanso = self.var_descanso.get()
        repaso = self.var_repaso.get()

        bloques, advertencias = generar_rutina(materias, tiempo, descanso, repaso)

        self._bloques_actuales  = bloques
        self._materias_actuales = materias
        self._tiempo_actual     = tiempo
        self._descanso_actual   = descanso
        self._repaso_actual     = repaso

        guardar_en_historial(materias, tiempo, descanso, repaso, bloques)

        self._mostrar_rutina(bloques, advertencias, materias, tiempo)
        self.notebook.select(self.tab_rutina)
        self._refrescar_historial()

    # ── Tab 2: Rutina generada ──

    def _build_tab_rutina(self):
        p = self.tab_rutina

        tk.Label(p, text="Rutina generada", bg=COLORES["fondo"],
                 fg=COLORES["acento2"], font=FUENTE_TITULO).pack(pady=(18, 4))

        self.lbl_resumen = tk.Label(p, text="", bg=COLORES["fondo"],
                                    fg=COLORES["texto_suave"], font=FUENTE_SMALL)
        self.lbl_resumen.pack()

        # Área scrollable para bloques
        contenedor = tk.Frame(p, bg=COLORES["fondo"])
        contenedor.pack(fill="both", expand=True, padx=20, pady=10)

        self.canvas_rutina = tk.Canvas(contenedor, bg=COLORES["fondo"],
                                       highlightthickness=0)
        sb = tk.Scrollbar(contenedor, orient="vertical",
                          command=self.canvas_rutina.yview)
        self.canvas_rutina.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        self.canvas_rutina.pack(side="left", fill="both", expand=True)

        self.frm_bloques = tk.Frame(self.canvas_rutina, bg=COLORES["fondo"])
        self.canvas_rutina.create_window((0, 0), window=self.frm_bloques, anchor="nw")
        self.frm_bloques.bind("<Configure>",
            lambda e: self.canvas_rutina.configure(
                scrollregion=self.canvas_rutina.bbox("all")))

        # Botones de acción
        frm_btn = tk.Frame(p, bg=COLORES["fondo"])
        frm_btn.pack(pady=10)
        btn_style(frm_btn, "💾 Guardar .txt", self._exportar_txt).pack(side="left", padx=6)
        btn_style(frm_btn, "↩ Nueva sesión",
                  lambda: self.notebook.select(self.tab_nueva),
                  color="#374151").pack(side="left", padx=6)

    def _mostrar_rutina(self, bloques, advertencias, materias, tiempo_total):
        # Limpiar
        for w in self.frm_bloques.winfo_children():
            w.destroy()

        total = sum(b["duracion"] for b in bloques)
        self.lbl_resumen.config(
            text=f"Duración total: {total} min  ·  {len(materias)} materia(s)  ·  "
                 f"Generada: {datetime.now().strftime('%H:%M')}"
        )

        # Advertencias
        if advertencias:
            for a in advertencias:
                tk.Label(self.frm_bloques, text=f"⚠  {a}",
                         bg="#3b1a1a", fg=COLORES["advertencia"],
                         font=FUENTE_SMALL, wraplength=760,
                         justify="left", padx=10, pady=4).pack(
                    fill="x", pady=2)

        cursor = datetime.now().replace(second=0, microsecond=0)

        for bloque in bloques:
            hora_str = cursor.strftime("%H:%M")
            tipo = bloque["tipo"]

            color_borde = {
                "estudio": COLORES["estudio"],
                "descanso": COLORES["descanso"],
                "repaso": COLORES["repaso"]
            }[tipo]

            card = tk.Frame(self.frm_bloques, bg=COLORES["panel"],
                            highlightthickness=2,
                            highlightbackground=color_borde)
            card.pack(fill="x", pady=4, padx=2)

            # Barra lateral de color
            barra = tk.Frame(card, bg=color_borde, width=6)
            barra.pack(side="left", fill="y")

            contenido = tk.Frame(card, bg=COLORES["panel"], padx=12, pady=8)
            contenido.pack(side="left", fill="both", expand=True)

            if tipo == "estudio":
                dif = bloque["dificultad"]
                icono = "📚"
                titulo_txt = f"{icono}  {bloque['materia']}"
                tk.Label(contenido, text=titulo_txt,
                         bg=COLORES["panel"], fg=COLORES["texto"],
                         font=FUENTE_SUB).pack(anchor="w")
                tk.Label(contenido,
                         text=f"Dificultad: {ETIQUETAS_DIF[dif]}  ·  {bloque['duracion']} min",
                         bg=COLORES["panel"], fg=COLOR_DIF[dif],
                         font=FUENTE_SMALL).pack(anchor="w")

            elif tipo == "descanso":
                tk.Label(contenido, text="☕  Descanso",
                         bg=COLORES["panel"], fg=COLORES["descanso"],
                         font=FUENTE_SUB).pack(anchor="w")
                tk.Label(contenido, text=f"{bloque['duracion']} min — Descansa, estira, hidratate",
                         bg=COLORES["panel"], fg=COLORES["texto_suave"],
                         font=FUENTE_SMALL).pack(anchor="w")

            elif tipo == "repaso":
                tk.Label(contenido, text="🔁  Repaso general",
                         bg=COLORES["panel"], fg=COLORES["repaso"],
                         font=FUENTE_SUB).pack(anchor="w")
                tk.Label(contenido, text=f"{bloque['duracion']} min — Revisa apuntes clave",
                         bg=COLORES["panel"], fg=COLORES["texto_suave"],
                         font=FUENTE_SMALL).pack(anchor="w")

            # Hora
            tk.Label(card, text=hora_str,
                     bg=COLORES["panel"], fg=COLORES["texto_suave"],
                     font=("Consolas", 11), padx=14).pack(side="right", anchor="center")

            cursor += timedelta(minutes=bloque["duracion"])

        # Fin
        tk.Label(self.frm_bloques,
                 text=f"🏁  Fin estimado: {cursor.strftime('%H:%M')}",
                 bg=COLORES["fondo"], fg=COLORES["acento2"],
                 font=FUENTE_SUB).pack(pady=(10, 4))

    def _exportar_txt(self):
        if not self._bloques_actuales:
            messagebox.showinfo("Sin rutina", "Primero genera una rutina.")
            return

        ruta = filedialog.asksaveasfilename(
            defaultextension=".txt",
            initialfile=f"rutina_{datetime.now().strftime('%Y%m%d_%H%M')}.txt",
            filetypes=[("Texto", "*.txt"), ("Todos", "*.*")]
        )
        if not ruta:
            return

        cursor = datetime.now().replace(second=0, microsecond=0)
        lineas = [
            "=" * 54,
            "  SISTEMA DE RECOMENDACIÓN DE RUTINAS DE ESTUDIO",
            "  Instituto Tecnológico de Ensenada — IA",
            f"  Generado: {datetime.now().strftime('%d/%m/%Y %H:%M')}",
            "=" * 54, ""
        ]
        for i, b in enumerate(self._bloques_actuales, 1):
            h = cursor.strftime("%H:%M")
            if b["tipo"] == "estudio":
                lineas.append(f"  {i:>2}. [{h}] ESTUDIO: {b['materia']}")
                lineas.append(f"       Dificultad: {ETIQUETAS_DIF[b['dificultad']]} | {b['duracion']} min")
            elif b["tipo"] == "descanso":
                lineas.append(f"  {i:>2}. [{h}] DESCANSO: {b['duracion']} min")
            else:
                lineas.append(f"  {i:>2}. [{h}] REPASO GENERAL: {b['duracion']} min")
            cursor += timedelta(minutes=b["duracion"])
        lineas += ["", f"  Fin estimado: {cursor.strftime('%H:%M')}", "=" * 54]

        with open(ruta, "w", encoding="utf-8") as f:
            f.write("\n".join(lineas))

        messagebox.showinfo("Guardado", f"Rutina guardada en:\n{ruta}")

    # ── Tab 3: Historial ──

    def _build_tab_historial(self):
        p = self.tab_hist

        tk.Label(p, text="Historial de sesiones", bg=COLORES["fondo"],
                 fg=COLORES["acento2"], font=FUENTE_TITULO).pack(pady=(18, 4))
        tk.Label(p, text="Últimas 50 rutinas generadas (se guarda automáticamente)",
                 bg=COLORES["fondo"], fg=COLORES["texto_suave"],
                 font=FUENTE_SMALL).pack()

        frm_btn = tk.Frame(p, bg=COLORES["fondo"])
        frm_btn.pack(pady=8)
        btn_style(frm_btn, "🔄 Refrescar", self._refrescar_historial,
                  color="#374151").pack(side="left", padx=4)
        btn_style(frm_btn, "🗑 Limpiar historial", self._limpiar_historial,
                  color="#7f1d1d").pack(side="left", padx=4)

        # Lista scrollable
        contenedor = tk.Frame(p, bg=COLORES["fondo"])
        contenedor.pack(fill="both", expand=True, padx=20, pady=8)

        self.canvas_hist = tk.Canvas(contenedor, bg=COLORES["fondo"],
                                     highlightthickness=0)
        sb = tk.Scrollbar(contenedor, orient="vertical",
                          command=self.canvas_hist.yview)
        self.canvas_hist.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        self.canvas_hist.pack(side="left", fill="both", expand=True)

        self.frm_hist_items = tk.Frame(self.canvas_hist, bg=COLORES["fondo"])
        self.canvas_hist.create_window((0, 0), window=self.frm_hist_items, anchor="nw")
        self.frm_hist_items.bind("<Configure>",
            lambda e: self.canvas_hist.configure(
                scrollregion=self.canvas_hist.bbox("all")))

        self._refrescar_historial()

    def _refrescar_historial(self):
        for w in self.frm_hist_items.winfo_children():
            w.destroy()

        historial = cargar_historial()
        if not historial:
            tk.Label(self.frm_hist_items,
                     text="No hay sesiones guardadas aún.\nGenera tu primera rutina.",
                     bg=COLORES["fondo"], fg=COLORES["texto_suave"],
                     font=FUENTE_NORMAL).pack(pady=40)
            return

        for entrada in historial:
            card = tk.Frame(self.frm_hist_items, bg=COLORES["panel"],
                            highlightthickness=1,
                            highlightbackground=COLORES["borde"])
            card.pack(fill="x", pady=3, padx=2)

            nombres = ", ".join(m["nombre"] for m in entrada.get("materias", []))
            mins = entrada.get("tiempo_total", "?")
            fecha = entrada.get("fecha", "?")

            fila = tk.Frame(card, bg=COLORES["panel"], padx=12, pady=8)
            fila.pack(fill="x")

            tk.Label(fila, text=f"📅  {fecha}",
                     bg=COLORES["panel"], fg=COLORES["acento2"],
                     font=("Segoe UI", 9, "bold")).pack(side="left")

            tk.Label(fila, text=f"  ·  {mins} min  ·  {nombres}",
                     bg=COLORES["panel"], fg=COLORES["texto"],
                     font=FUENTE_SMALL).pack(side="left")

            # Botón ver detalle
            tk.Button(
                fila, text="Ver",
                command=lambda e=entrada: self._ver_detalle(e),
                bg=COLORES["acento"], fg="white",
                relief="flat", font=FUENTE_SMALL,
                cursor="hand2", padx=8, pady=2
            ).pack(side="right")

    def _ver_detalle(self, entrada):
        ventana = tk.Toplevel(self)
        ventana.title(f"Sesión — {entrada.get('fecha', '')}")
        ventana.geometry("500x420")
        ventana.configure(bg=COLORES["fondo"])

        tk.Label(ventana, text=f"Sesión del {entrada.get('fecha','')}",
                 bg=COLORES["fondo"], fg=COLORES["acento2"],
                 font=FUENTE_SUB).pack(pady=12)

        txt = tk.Text(ventana, bg=COLORES["panel"], fg=COLORES["texto"],
                      font=FUENTE_MONO, relief="flat", padx=10, pady=8,
                      wrap="word", state="normal")
        txt.pack(fill="both", expand=True, padx=16, pady=(0, 12))

        cursor = datetime.now().replace(second=0, microsecond=0)
        for i, b in enumerate(entrada.get("bloques", []), 1):
            h = cursor.strftime("%H:%M")
            if b["tipo"] == "estudio":
                txt.insert("end",
                    f"  {i:>2}. [{h}] 📚 {b['materia']} — "
                    f"{ETIQUETAS_DIF.get(b['dificultad'], '')} · {b['duracion']} min\n")
            elif b["tipo"] == "descanso":
                txt.insert("end", f"  {i:>2}. [{h}] ☕  Descanso · {b['duracion']} min\n")
            else:
                txt.insert("end", f"  {i:>2}. [{h}] 🔁  Repaso · {b['duracion']} min\n")
            cursor += timedelta(minutes=b["duracion"])

        txt.config(state="disabled")

    def _limpiar_historial(self):
        if messagebox.askyesno("Confirmar", "¿Borrar todo el historial?"):
            if os.path.exists(HISTORIAL_FILE):
                os.remove(HISTORIAL_FILE)
            self._refrescar_historial()



#  INICIO

if __name__ == "__main__":
    app = App()
    app.mainloop()
