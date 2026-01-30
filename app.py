# file: app.py

import streamlit as st
import pytesseract
from PIL import Image
import pandas as pd
from io import BytesIO

# Configuración de página
st.set_page_config(page_title="OCR App", layout="centered")
st.title("🧠 OCR - Extraer texto desde imagen")

# Subir imagen
uploaded_file = st.file_uploader("📤 Sube una imagen", type=["png", "jpg", "jpeg", "bmp", "tiff"])

if uploaded_file is not None:
    image = Image.open(uploaded_file)
    st.image(image, caption="🖼️ Imagen cargada", width="stretch")

    # Botón de procesamiento
    if st.button("🚀 Procesar imagen"):
        with st.spinner("Analizando imagen..."):
            # OCR con estructura tipo tabla
            df_raw = pytesseract.image_to_data(image, output_type=pytesseract.Output.DATAFRAME)
            df_raw = df_raw[df_raw['text'].notnull() & (df_raw['text'].str.strip() != '')]

            if df_raw.empty:
                st.warning("⚠️ No se detectó texto en la imagen.")
            else:
                # Agrupar por línea para reconstruir filas
                grouped = df_raw.groupby(['block_num', 'par_num', 'line_num'])
                lines = []
                for _, group in grouped:
                    line_text = ' '.join(group.sort_values('left')['text'].tolist())
                    lines.append(line_text)

                # Construir DataFrame limpio con filas de texto
                df_lines = pd.DataFrame({'Fila': lines})
                st.success("✅ Texto extraído y estructurado por filas.")
                st.dataframe(df_lines)

                # Descargar como Excel
                output = BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    df_lines.to_excel(writer, sheet_name='OCR', index=False)
                output.seek(0)

                st.download_button(
                    label="📥 Descargar como Excel",
                    data=output,
                    file_name="resultado_ocr_tabla.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
