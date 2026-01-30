import streamlit as st
import pytesseract
from PIL import Image
import pandas as pd
from io import BytesIO

# Configuración de la página
st.set_page_config(page_title="OCR Tablas", layout="centered")
st.title("📊 OCR - Detectar y reconstruir tablas desde imagen")

# Subir imagen
uploaded_file = st.file_uploader("📤 Sube una imagen (tabla tipo Excel/Power BI)", type=["png", "jpg", "jpeg", "bmp", "tiff"])

if uploaded_file is not None:
    image = Image.open(uploaded_file)
    st.image(image, caption="🖼️ Imagen cargada", width="stretch")

    if st.button("🚀 Procesar como tabla"):
        with st.spinner("🔎 Extrayendo texto y detectando estructura de tabla..."):
            df_raw = pytesseract.image_to_data(image, output_type=pytesseract.Output.DATAFRAME)
            df_raw = df_raw[df_raw['text'].notnull() & (df_raw['text'].str.strip() != '')]

            if df_raw.empty:
                st.warning("⚠️ No se detectó texto en la imagen.")
            else:
                # Agrupar por líneas
                lines = []
                grouped = df_raw.groupby(['block_num', 'par_num', 'line_num'])
                for _, group in grouped:
                    group_sorted = group.sort_values('left')
                    line = [(word['left'], word['text']) for _, word in group_sorted.iterrows()]
                    lines.append(line)

                # 1. Detectar posiciones de columnas
                all_lefts = [left for line in lines for (left, _) in line]
                all_lefts = sorted(all_lefts)

                col_positions = []
                tolerance = 40  # tolerancia para agrupar columnas
                for pos in all_lefts:
                    if not col_positions or abs(pos - col_positions[-1]) > tolerance:
                        col_positions.append(pos)

                # 2. Mapear texto a columnas
                structured_rows = []
                for line in lines:
                    row = [''] * len(col_positions)
                    for left, word in line:
                        distances = [abs(left - col) for col in col_positions]
                        col_idx = distances.index(min(distances))
                        if row[col_idx]:
                            row[col_idx] += ' ' + word
                        else:
                            row[col_idx] = word
                    structured_rows.append(row)

                # 3. Crear DataFrame limpio
                df_table = pd.DataFrame(structured_rows)
                df_table = df_table.dropna(how='all')  # eliminar filas vacías
                df_table = df_table.loc[:, (df_table != '').any()]  # eliminar columnas vacías

                # Mostrar en pantalla
                st.success("✅ Tabla detectada correctamente.")
                st.dataframe(df_table)

                # Descargar como Excel
                output = BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    df_table.to_excel(writer, sheet_name='Tabla OCR', index=False, header=False)
                output.seek(0)

                st.download_button(
                    label="📥 Descargar tabla como Excel",
                    data=output,
                    file_name="tabla_ocr.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
