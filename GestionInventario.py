import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog, messagebox
import pandas as pd
import numpy as np
import mplcursors
import matplotlib.pyplot as plt
from openpyxl import Workbook
from openpyxl.drawing.image import Image
import io
import csv
from pathlib import Path

class InventoryManager(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Sistema de Gestión de Inventario")
        self.geometry("1000x500")
        
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.csv_data = None
        self.excedente_data = None
        self.excel_writer = None
        self.separated_df = None  
        self.faltantes_df = None
        self.faltantes_en_proveedor_df = None
        self.create_sidebar()
        self.create_main_frame()
        self.create_notebook()

    def create_sidebar(self):
        self.sidebar_frame = ctk.CTkFrame(self, width=200, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, rowspan=4, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(4, weight=1)
        
        # App logo/title
        self.logo_label = ctk.CTkLabel(
            self.sidebar_frame, 
            text="Sistema de\nGestión de\nInventario", 
            font=ctk.CTkFont(size=20, weight="bold")
        )
        self.logo_label.grid(row=0, column=0, padx=20, pady=(20, 10))
        
        # Mode switch
        self.appearance_mode_label = ctk.CTkLabel(
            self.sidebar_frame, text="Apariencia:", anchor="w")
        self.appearance_mode_label.grid(row=5, column=0, padx=20, pady=(10, 0))
        self.appearance_mode_menu = ctk.CTkOptionMenu(
            self.sidebar_frame,
            values=["System", "Dark", "Light"],
            command=self.change_appearance_mode)
        self.appearance_mode_menu.grid(row=6, column=0, padx=20, pady=(10, 10))
        
        # Status section
        self.status_label = ctk.CTkLabel(
            self.sidebar_frame,
            text="Estado: Listo",
            font=ctk.CTkFont(size=12)
        )
        self.status_label.grid(row=5, column=0, pady=7)

    def create_main_frame(self):
        self.main_frame = ctk.CTkFrame(self)
        self.main_frame.grid(row=0, column=1, padx=20, pady=20, sticky="nsew")
        self.main_frame.grid_columnconfigure(0, weight=1)
        self.main_frame.grid_rowconfigure(0, weight=1)

    def create_notebook(self):
        # Create notebook tabs
        self.tabview = ctk.CTkTabview(self.main_frame)
        self.tabview.grid(row=0, column=0, padx=20, pady=20, sticky="nsew")
        
        # Add tabs
        self.tab_separator = self.tabview.add("Separador de Códigos")
        self.tab_analyzer = self.tabview.add("Análisis de Inventario")
        
        # Configure Separator tab
        self.create_separator_tab()
        
        # Configure Analyzer tab
        self.create_analyzer_tab()

    def create_separator_tab(self):
        # Frame for file selection
        file_frame = ctk.CTkFrame(self.tab_separator)
        file_frame.pack(fill="x", padx=20, pady=10)
        
        # Selector de archivo original  
        self.select_file_button = ctk.CTkButton(
            file_frame,
            text="Seleccionar Archivo Excel",
            command=self.process_separator_file
        )
        self.select_file_button.pack(pady=10)
        
        # Preview button
        self.preview_button = ctk.CTkButton(
            file_frame,
            text="Previsualizar Datos",
            command=self.show_preview
        )
        self.preview_button.pack(pady=10)
        
        # Save button
        self.save_button = ctk.CTkButton(
            file_frame,
            text="Guardar Archivo Separado",
            command=self.save_separated_file
        )
        self.save_button.pack(pady=10)
        
        # Continue button
        self.continue_button = ctk.CTkButton(
            file_frame,
            text="Continuar con Análisis",
            command=self.continue_to_analysis
        )
        self.continue_button.pack(pady=10)

    def create_analyzer_tab(self):
        # File selection frame
        files_frame = ctk.CTkFrame(self.tab_analyzer)
        files_frame.pack(fill="x", padx=20, pady=10)
        
        # File entries
        self.file_entries = {}
        file_types = ["proveedor", "simulador"]
        
        for file_type in file_types:
            frame = ctk.CTkFrame(files_frame)
            frame.pack(fill="x", pady=5)
            
            label = ctk.CTkLabel(frame, text=f"Archivo {file_type.capitalize()}:")
            label.pack(side="left", padx=10)
            
            entry = ctk.CTkEntry(frame, width=400)
            entry.pack(side="left", padx=10, fill="x", expand=True)
            
            button = ctk.CTkButton(
                frame,
                text="Seleccionar",
                command=lambda t=file_type: self.load_file(t),
                width=100
            )
            button.pack(side="right", padx=10)
            
            self.file_entries[file_type] = entry
        
        # Analysis buttons frame
        analysis_frame = ctk.CTkFrame(self.tab_analyzer)
        analysis_frame.pack(fill="x", padx=20, pady=10)
        
        # Analysis buttons
        buttons = [
            #("Procesar Archivos", self.process_files),
            ("Incorporaciones y Discontinuados", self.products_faltantes),
            ("Análisis Códigos", self.analyze_eanPpal),
            ("Informe Stock", self.analyze_sin_stock),
        ]
        
        for text, command in buttons:
            btn = ctk.CTkButton(analysis_frame, text=text, command=command)
            btn.pack(pady=5)

    def dividir_codigos(self, codigos):
        if pd.isna(codigos) or codigos == '':
            return [np.nan]
        if isinstance(codigos, int):
            return [codigos]
        if "-" in codigos:
            codigos_divididos = codigos.split("-")
            codigos_divididos = [int(c) if c.isdigit() else np.nan for c in codigos_divididos]
            return codigos_divididos
        else:
            codigos = codigos.split()
            codigos_divididos = [int(c) if c.isdigit() else np.nan for c in codigos]
            return codigos_divididos

    def process_separator_file(self):
        archivo = filedialog.askopenfilename(filetypes=[("CSV files", "*.csv")])
        if archivo:
            try:
                # Intentamos leer el archivo con UTF-8
                try:
                    datos_csv = pd.read_csv(archivo, sep=';', encoding='utf-8', skiprows=10)

                except UnicodeDecodeError:
                    # Si falla, intentamos con Latin-1
                    datos_csv = pd.read_csv(archivo, sep=';', encoding='latin1',skiprows=10)
                
            

                # Continuamos con el procesamiento
                codigos_extraidos = datos_csv['Codebar'].apply(self.dividir_codigos)
                max_codigo_length = codigos_extraidos.apply(len).max()
                codigos_extraidos = pd.DataFrame(
                    codigos_extraidos.tolist(),
                    columns=[f"Codigo_{i+1}" for i in range(max_codigo_length)]
                )
                codigos_extraidos = codigos_extraidos.map(lambda x: f"{x:0.0f}" if not pd.isna(x) else "")
                datos_csv['codebar1'] = pd.to_numeric(datos_csv['codebar1'], errors='coerce')
                datos_csv['codebar1'] = datos_csv['codebar1'].map(lambda x: f"{x:0.0f}" if not pd.isna(x) else "")

                self.separated_df = pd.concat([datos_csv[['Cod.Producto', 'Producto', 'Visible', 'Fec. Precio', 
                                'Costo', 'Precio', 'codebar1']],  codigos_extraidos], axis=1)
                self.status_label.configure(text="Estado: Archivo separado procesado")
                messagebox.showinfo("Éxito", "Archivo procesado correctamente")
            except Exception as e:
                messagebox.showerror("Error", f"Error al procesar archivo: {str(e)}")

    def show_preview(self):
        if self.separated_df is None:
            messagebox.showerror("Error", "No hay datos para mostrar")
            return
        
        preview_window = tk.Toplevel(self)
        preview_window.title("Previsualización de Datos")
        preview_window.geometry("800x600")
        
        # Create text widget with scrollbars
        text_frame = tk.Frame(preview_window)
        text_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        text = tk.Text(text_frame, wrap='none')
        scrollbar_y = tk.Scrollbar(text_frame, orient="vertical", command=text.yview)
        scrollbar_x = tk.Scrollbar(text_frame, orient="horizontal", command=text.xview)
        text.configure(yscrollcommand=scrollbar_y.set, xscrollcommand=scrollbar_x.set)
        
        text.grid(row=0, column=0, sticky="nsew")
        scrollbar_y.grid(row=0, column=1, sticky="ns")
        scrollbar_x.grid(row=1, column=0, sticky="ew")
        
        text_frame.grid_rowconfigure(0, weight=1)
        text_frame.grid_columnconfigure(0, weight=1)
        
        text.insert(tk.END, self.separated_df.to_string())
        text.config(state=tk.DISABLED)

    def save_separated_file(self):
        print('Hecho por Jordi Van Norden')
        if self.separated_df is None:
            messagebox.showerror("Error", "No hay datos para guardar")
            return
            
        filename = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            filetypes=[("Excel files", "*.xlsx")]
        )
        if filename:
            try:
                self.separated_df.to_excel(filename, index=False)
                messagebox.showinfo("Éxito", "Archivo guardado correctamente")
            except Exception as e:
                messagebox.showerror("Error", f"Error al guardar: {str(e)}")

    def continue_to_analysis(self):
        if self.separated_df is None:
            messagebox.showerror("Error", "Primero procese el archivo de códigos")
            return
        
        self.tabview.set("Análisis de Inventario")
        self.status_label.configure(text="Estado: Listo para análisis")

    def change_appearance_mode(self, new_appearance_mode: str):
        ctk.set_appearance_mode(new_appearance_mode)

    # Métodos del analizador (implementar según el código original)
    def load_file(self, file_type):
        filename = filedialog.askopenfilename(
            filetypes=[("Excel files", "*.xlsx; *.xls"), ("CSV files", "*.csv")]
        )
        if filename:
            self.file_entries[file_type].delete(0, tk.END)
            self.file_entries[file_type].insert(0, filename)

            if file_type == "proveedor":
                try:
                    self.proveedor_df = pd.read_excel(filename, header=None)
                except Exception as e:
                    messagebox.showerror("Error", f"Error al cargar archivo Excel: {str(e)}")
            elif file_type == "simulador":
                try:
                    # self.simulador_df = pd.read_csv(filename, sep=';', encoding='iso-8859-1')
                    self.simulador_df = pd.read_csv(filename, sep=';', encoding='utf-8')
                except UnicodeDecodeError:
                    messagebox.showerror("Error de codificación", "El archivo CSV tiene una codificación de caracteres no soportada. Intenta abrir el archivo en un editor de texto y guardarlo con codificación UTF-8.")
                except Exception as e:
                    messagebox.showerror("Error", f"Error al cargar archivo CSV: {str(e)}")


    def products_faltantes(self):
       
        columnas_codigos = ['codebar1'] + [col for col in self.separated_df.columns if col.startswith('Codigo_')]
        
        # Convertir códigos del proveedor a str y limpiar - ahora usando toda la columna sin excluir la primera fila
        proveedor_codigos = set(str(codigo).strip() for codigo in self.proveedor_df.iloc[:, 0] if pd.notna(codigo))
        
        # Recolectar todos los códigos del archivo separado
        separados_codigos = set()
        for columna in columnas_codigos:
            codigos = self.separated_df[columna].astype(str)
            separados_codigos.update(cod.strip() for cod in codigos if cod and cod.strip() != '' and cod != 'nan')
        
        # Encontrar códigos que están en proveedor pero no en separados (posibles incorporaciones)
        posibles_incorporaciones = proveedor_codigos - separados_codigos
        
        # Crear DataFrame con las posibles incorporaciones, ahora incluyendo todas las filas
        self.faltantes_df = self.proveedor_df[
            self.proveedor_df.iloc[:, 0].astype(str).apply(lambda x: x.strip() in posibles_incorporaciones)
        ]
        
        # Encontrar códigos que están en separados pero no en proveedor (faltantes en proveedor)
        faltantes_en_proveedor = separados_codigos - proveedor_codigos
        
        # Crear DataFrame con los faltantes en el proveedor
        self.faltantes_en_proveedor_df = self.separated_df[
            self.separated_df['codebar1'].astype(str).apply(lambda x: x.strip() in faltantes_en_proveedor)
        ]
        
        # Mostrar resultados
        self.show_preview_df(self.faltantes_df, title="Posibles incorporaciones")
        self.show_preview_df(self.faltantes_en_proveedor_df, title="Faltantes en Proveedor")
    def analyze_eanPpal(self):
        """
        Analiza los códigos del proveedor para determinar si son códigos principales o necesitan rotación de EAN.
        Un código es principal si aparece en Codigo_1, necesita rotación si aparece en otras columnas Codigo_X.
        """
        try:
            # Verificar que tenemos los DataFrames necesarios
            if self.proveedor_df is None or self.separated_df is None:
                messagebox.showerror("Error", "Primero cargue los archivos del proveedor y separado")
                return
                
            # Obtener todas las columnas de códigos
            columnas_codigos = [col for col in self.separated_df.columns if col.startswith('Codigo_')]
            
            # Crear un DataFrame de análisis a partir del DataFrame del proveedor
            df_analisis = self.proveedor_df.copy()
            
            def analizar_tipo_codigo(codigo):
                codigo = str(codigo).strip()
                # Verificar si está en Codigo_1
                codigos_principales = set(self.separated_df['Codigo_1'].astype(str).apply(str.strip))
                if codigo in codigos_principales:
                    return "ES PRINCIPAL"
                
                # Verificar si está en alguna otra columna de código
                for col in columnas_codigos[1:]:  # Empezamos desde Codigo_2
                    codigos_secundarios = set(self.separated_df[col].astype(str).apply(str.strip))
                    if codigo in codigos_secundarios:
                        return "ROTAR EAN"
                
                return "NUEVO PRODUCTO"
            
            # Aplicar el análisis a la primera columna del DataFrame del proveedor
            df_analisis['Tipo_Codigo'] = df_analisis.iloc[:, 0].apply(analizar_tipo_codigo)
            
            # Agregar columna con el conteo por tipo
            tipo_counts = df_analisis['Tipo_Codigo'].value_counts()
            
            # Mostrar resumen en messagebox
            resumen = "\n".join([f"{tipo}: {count}" for tipo, count in tipo_counts.items()])
            messagebox.showinfo("Resumen de Análisis", 
                            f"Resultados del análisis:\n\n{resumen}")
            
            # Mostrar resultados detallados
            self.show_preview_df(df_analisis, title="Análisis de EANs")
            
            # Opcionalmente, guardar los diferentes tipos en DataFrames separados
            self.ean_principal_df = df_analisis[df_analisis['Tipo_Codigo'] == "ES PRINCIPAL"]
            self.ean_rotar_df = df_analisis[df_analisis['Tipo_Codigo'] == "ROTAR EAN"]
            self.ean_nuevo_df = df_analisis[df_analisis['Tipo_Codigo'] == "NUEVO PRODUCTO"]
            
            return df_analisis
            
        except Exception as e:
            messagebox.showerror("Error", f"Error durante el análisis: {str(e)}")
            print(str(e))
            return None

    def analyze_sin_stock(self):
        """
        Analiza diferentes casos de stock y ventas en el DataFrame del simulador.
        Crea DataFrames específicos para cada caso y permite exportar todos a un Excel.
        """
        try:
            if self.simulador_df is None:
                messagebox.showerror("Error", "Primero cargue el archivo del simulador")
                return

            # Asegurar que las columnas numéricas sean de tipo float
            columnas_numericas = ["Máximo 3 meses", "Surtido Total", "Stock Sucursales", 
                                "Stock Actual C.D.", "Comprar"]
            
            for columna in columnas_numericas:
                self.simulador_df[columna] = pd.to_numeric(self.simulador_df[columna], errors='coerce')

            # Columnas a mantener en todos los casos
            columnas_base = ["Codigo", "C.Barra", "Descripcion", "Máximo 3 meses", 
                            "Surtido Total", "Stock Sucursales", "Stock Actual C.D.", "Comprar"]

            # Crear DataFrames para cada caso
            # 1. CEROSTOCK_CONVENTA
            self.df_cerostock_conventa = self.simulador_df[
                (self.simulador_df["Stock Sucursales"].fillna(0) == 0) & 
                (self.simulador_df["Stock Actual C.D."].fillna(0) == 0) & 
                (self.simulador_df["Máximo 3 meses"] > 0)
            ][columnas_base].copy()

            # 2. CEROSTOCK_SINVENTA
            self.df_cerostock_sinventa = self.simulador_df[
                (self.simulador_df["Stock Sucursales"].fillna(0) == 0) & 
                (self.simulador_df["Stock Actual C.D."].fillna(0) == 0) & 
                (self.simulador_df["Máximo 3 meses"].fillna(0) == 0)
            ][columnas_base].copy()

            # 3. CONSTOCK_SINSURTIDO
            self.df_constock_sinsurtido = self.simulador_df[
                (self.simulador_df["Stock Sucursales"].fillna(0) == 0) & 
                (self.simulador_df["Surtido Total"].isna())
            ][columnas_base].copy()

            # 4. BAJOSTOCKSUCURSAL
            self.df_bajostocksucursal = self.simulador_df[
                (self.simulador_df["Stock Sucursales"].fillna(0) < self.simulador_df["Surtido Total"]) &
                (self.simulador_df["Surtido Total"].notna())
            ][columnas_base].copy()

            # 5. MENOSVENTAS_VSSTOCK
            self.df_menosventas_vsstock = self.simulador_df[
                self.simulador_df["Comprar"].fillna(0) < 0
            ][columnas_base].copy()

            # 6. MayoresVentas
            self.df_mayoresventas = self.simulador_df[
                self.simulador_df["Máximo 3 meses"].fillna(0) > 0
            ][columnas_base].copy().sort_values(by="Máximo 3 meses", ascending=False)

            # El resto del código permanece igual...
            resumen = f"""Resultados del análisis:
            - Cero stock con venta: {len(self.df_cerostock_conventa)} productos
            - Cero stock sin venta: {len(self.df_cerostock_sinventa)} productos
            - Con stock sin surtido: {len(self.df_constock_sinsurtido)} productos
            - Bajo stock en sucursal: {len(self.df_bajostocksucursal)} productos
            - Menos ventas vs stock: {len(self.df_menosventas_vsstock)} productos
            - Productos con ventas: {len(self.df_mayoresventas)} productos"""

            messagebox.showinfo("Resumen de Análisis", resumen)
            self.show_preview_df(self.df_cerostock_conventa, title="Cero stock con venta")
            self.show_preview_df(self.df_cerostock_sinventa, title="Cero stock sin venta")
            #self.show_preview_df(self.df_constock_sinsurtido, title="Con stock sin surtido")
            self.show_preview_df(self.df_bajostocksucursal, title="Bajo stock en sucursal")
            self.show_preview_df(self.df_menosventas_vsstock, title="Menos ventas vs stock")
            #self.show_preview_df(self.df_mayoresventas, title="Productos con ventas")

            # El resto de las funciones (guardar_excel, crear_pestaña, etc.) permanecen igual...

        except Exception as e:
            messagebox.showerror("Error", f"Error durante el análisis: {str(e)}")
    def analyze_secondary_barcodes(self):
        # Obtener los códigos de barra que aparecen en más de una columna de separated_df
        secundarios_codigos = self.separated_df.iloc[:, 1:].apply(lambda x: x.unique(), axis=1)
        secundarios_codigos = secundarios_codigos[secundarios_codigos.apply(lambda x: len(x) > 1)]

        # Crear un DataFrame con los productos que tienen códigos secundarios
        self.secundarios_df = self.separated_df.loc[secundarios_codigos.index]
    

        # Mostrar los resultados
        self.show_preview_df(self.secundarios_df)
        

    def analyze_stock(self):
        # Filtrar los productos con ambos stocks en 0
        self.sin_stock = self.simulador_df[(self.simulador_df['Stock Actual C.D.'] == 0) & (self.simulador_df['Stock Sucursales'] == 0)]

        # Filtrar los productos con uno de los stocks en 0
        self.stock_parcial = self.simulador_df[((self.simulador_df['Stock Actual C.D.'] == 0) | (self.simulador_df['Stock Sucursales'] == 0)) &
                                 ((self.simulador_df['Stock Actual C.D.'] != 0) | (self.simulador_df['Stock Sucursales'] != 0))]

        # Mostrar los resultados
        self.show_preview_df(self.sin_stock)
        self.show_preview_df(self.stock_parcial)

    def show_preview_df(self, df, title="Previsualización"):
        if df.empty:
            messagebox.showinfo("Previsualización", "No hay datos para mostrar.")
            return
        
        # Crear la ventana emergente con el título que se pasa
        preview_window = ctk.CTkToplevel(self)
        preview_window.title(f"Previsualización: {title}")
        preview_window.geometry("800x600")
        
        # Crear widget de texto con barras de desplazamiento
        text_frame = ctk.CTkFrame(preview_window)
        text_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        text = tk.Text(text_frame, wrap='none')
        scrollbar_y = tk.Scrollbar(text_frame, orient="vertical", command=text.yview)
        scrollbar_x = tk.Scrollbar(text_frame, orient="horizontal", command=text.xview)
        text.configure(yscrollcommand=scrollbar_y.set, xscrollcommand=scrollbar_x.set)
        
        text.grid(row=0, column=0, sticky="nsew")    
        scrollbar_y.grid(row=0, column=1, sticky="ns")
        scrollbar_x.grid(row=1, column=0, sticky="ew")
        
        text_frame.grid_rowconfigure(0, weight=1)
        text_frame.grid_columnconfigure(0, weight=1)
        
        # Insertar el contenido del DataFrame en el widget de texto
        text.insert(tk.END, df.to_string())
        text.config(state=tk.DISABLED)
        
        # Crear el botón de descarga en la ventana emergente
        def download_excel():
            file_path = filedialog.asksaveasfilename(defaultextension=".xlsx", filetypes=[("Excel files", "*.xlsx")])
            if file_path:
                df.to_excel(file_path, index=False)
                messagebox.showinfo("Descarga completada", f"El archivo se guardó en {file_path}")

        download_button = ctk.CTkButton(preview_window, text="Descargar como Excel", command=download_excel)
        download_button.pack(pady=10)



if __name__ == "__main__":
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")
    app = InventoryManager()
    app.mainloop()