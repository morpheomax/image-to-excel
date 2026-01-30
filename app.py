import streamlit as st
import pytesseract
from PIL import Image
import pandas as pd
from io import BytesIO

# Configurar página
st.set_page_config(page_title="OCR App", layout="centered")
st.title("🧠 OCR - Extraer tabla desde imagen")

# Subir imagen
uploaded_file = st.file_uploader("📤 Sube una imagen", type=["png", "jpg", "jpeg", "bmp", "tiff"])

if uploaded_file is not None:
    image = Image.open(uploaded_file)
    st.image(image, caption="🖼️ Imagen cargada", width="stretch")

    if st.button("🚀 Procesar imagen"):
        with st.spinner("Analizando imagen y reconstruyendo tabla..."):
            df_raw = pytesseract.image_to_data(image, output_type=pytesseract.Output.DATAFRAME)
            df_raw = df_raw[df_raw['text'].notnull() & (df_raw['text'].str.strip() != '')]

            if df_raw.empty:
                st.warning("⚠️ No se detectó texto en la imagen.")
            else:
                # Agrupar por línea
                lines = []
                grouped = df_raw.groupby(['block_num', 'par_num', 'line_num'])
                for _, group in grouped:
                    group_sorted = group.sort_values('left')
                    line = []
                    for _, word in group_sorted.iterrows():
                        line.append((word['left'], word['text']))
                    lines.append(line)

                # Detectar columnas por posición
                # Paso 1: juntar todas las posiciones 'left'
                all_lefts = [left for line in lines for (left, _) in line]
                all_lefts = sorted(all_lefts)

                # Paso 2: agrupar por cercanía (tolerancia de 30 px)
                col_positions = []
                tolerance = 30
                for pos in all_lefts:
                    if not col_positions or abs(pos - col_positions[-1]) > tolerance:
                        col_positions.append(pos)

                # Paso 3: para cada línea, asignar palabras a columnas por cercanía
                structured_rows = []
                for line in lines:
                    row = [''] * len(col_positions)
                    for left, word in line:
                        # Buscar columna más cercana
                        distances = [abs(left - col) for col in col_positions]
                        col_idx = distances.index(min(distances))
                        if row[col_idx]:
                            row[col_idx] += ' ' + word  # concatenar si ya hay algo
                        else:
                            row[col_idx] = word
                    structured_rows.append(row)

                # Crear DataFrame
                df_structured = pd.DataFrame(structured_rows)
                st.success("✅ Tabla reconstruida correctamente.")
                st.dataframe(df_structured)

                # Descargar Excel
                output = BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    df_structured.to_excel(writer, sheet_name='OCR_Table', index=False, header=False)
                output.seek(0)

                st.download_button(
                    label="📥 Descargar como Excel",
                    data=output,
                    file_name="tabla_ocr.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
