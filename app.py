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
    #st.image(image, caption="🖼️ Imagen cargada", use_container_width=True)
    st.image(image, caption="🖼️ Imagen cargada", width="stretch")



    # Botón de procesamiento
    if st.button("🚀 Procesar imagen"):
        with st.spinner("Analizando imagen..."):
            # OCR con estructura tipo tabla
            df = pytesseract.image_to_data(image, output_type=pytesseract.Output.DATAFRAME)
            df = df[df['text'].notnull() & (df['text'].str.strip() != '')]  # Filtrar celdas vacías

            if df.empty:
                st.warning("⚠️ No se detectó texto en la imagen.")
            else:
                st.success("✅ Texto extraído correctamente.")
                st.dataframe(df[['text', 'conf', 'left', 'top', 'width', 'height']].reset_index(drop=True))

                # Descargar Excel
                output = BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    df.to_excel(writer, sheet_name='OCR', index=False)
                output.seek(0)

                st.download_button(
                    label="📥 Descargar como Excel",
                    data=output,
                    file_name="resultado_ocr.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
