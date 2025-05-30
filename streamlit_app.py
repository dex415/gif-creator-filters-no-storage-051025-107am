import streamlit as st
from PIL import Image, ImageEnhance, ImageFilter, UnidentifiedImageError
import os
import tempfile
import imageio
import io
from moviepy.editor import ImageSequenceClip
from datetime import datetime
from streamlit_sortables import sort_items

st.set_page_config(page_title="🧢 TWNTY-TWO GIF Creator", layout="centered", page_icon="https://twnty-two-assets.s3.amazonaws.com/twnty-two-logo-header.png")

st.markdown("""
    <style>
    .main {background-color: #fff;}
    h1, h2, h3 {color: #111; font-family: 'Helvetica Neue', sans-serif;}
    .stButton>button {background-color: #111;color: white;border-radius: 8px;}
    </style>
""", unsafe_allow_html=True)

st.title("🧢 TWNTY-TWO GIF Creator")

preset = st.selectbox("🎛️ Choose a preset", ["GIF (Short Reel)", "MP4 (Longer Reel)", "Custom"])

st.subheader("Upload Images")
uploaded_files = st.file_uploader("Drag and drop or browse to upload images", accept_multiple_files=True, type=["png", "jpg", "jpeg"], label_visibility="visible", key="uploader")
st.markdown("---")

if preset == "Custom":
    duration = st.slider("Frame display time (seconds)", min_value=0.5, max_value=5.0, value=1.5, step=0.1)
    output_format = st.radio("Choose output format", ["GIF", "MP4 (video)"], index=0)
else:
    if preset == "GIF (Short Reel)":
        duration = 1.5
        output_format = "GIF"
    elif preset == "MP4 (Longer Reel)":
        duration = 2.2
        output_format = "MP4 (video)"


st.subheader("Filters and Image Edits")
add_watermark = st.checkbox("Add TWNTY-TWO logo watermark", value=True)
if preset == "Custom":
    watermark_size = st.slider("Watermark size (% of image width)", 5, 30, 15)
else:
    watermark_size = 15

watermark_margin = 4  # fixed margin that looks good by default

apply_bw = st.checkbox("Apply black & white filter")
apply_contrast = st.checkbox("Boost contrast")
apply_blur = st.checkbox("Apply soft blur")
apply_sepia = st.checkbox("Apply sepia tone")

LOGO_PATH = "logo.png"

if uploaded_files:
    file_dict = {}
    for file in uploaded_files:
        try:
            img = Image.open(file)
            img.load()
            file.seek(0)
            file_dict[file.name] = file
        except Exception:
            st.warning(f"Skipping {file.name}: not a valid image.")

    if not file_dict:
        st.error("No valid images uploaded. Please check your files.")
        st.stop()

    st.markdown("**Drag images to sort their order:**")
    ordered_filenames = sort_items(list(file_dict.keys()))
    

    if st.button("Create Output"):
        with tempfile.TemporaryDirectory() as tmpdir:
            images = []
            for fname in ordered_filenames:
                if st.session_state.get(f"confirm_remove_{ordered_filenames.index(fname)}"):
                    continue
                file = file_dict[fname]
                img_path = os.path.join(tmpdir, file.name)
                file.seek(0)
                with open(img_path, "wb") as f:
                    f.write(file.read())
                try:
                    img = Image.open(img_path).convert("RGB")
                except UnidentifiedImageError:
                    st.error(f"Unable to open image: {file.name}. Please make sure it's a valid PNG or JPG.")
                    continue

                min_side = min(img.size)
                img_cropped = img.crop(((img.width - min_side) // 2,
                                        (img.height - min_side) // 2,
                                        (img.width + min_side) // 2,
                                        (img.height + min_side) // 2))

                if apply_bw:
                    img_cropped = img_cropped.convert("L").convert("RGB")
                if apply_contrast:
                    enhancer = ImageEnhance.Contrast(img_cropped)
                    img_cropped = enhancer.enhance(1.5)
                if apply_blur:
                    img_cropped = img_cropped.filter(ImageFilter.GaussianBlur(radius=2))
                if apply_sepia:
                    sepia = Image.new("RGB", img_cropped.size)
                    pixels = img_cropped.load()
                    for y in range(img_cropped.size[1]):
                        for x in range(img_cropped.size[0]):
                            r, g, b = pixels[x, y]
                            tr = int(0.393 * r + 0.769 * g + 0.189 * b)
                            tg = int(0.349 * r + 0.686 * g + 0.168 * b)
                            tb = int(0.272 * r + 0.534 * g + 0.131 * b)
                            sepia.putpixel((x, y), (min(tr, 255), min(tg, 255), min(tb, 255)))
                    img_cropped = sepia

                if add_watermark and os.path.exists(LOGO_PATH):
                    logo = Image.open(LOGO_PATH).convert("RGBA")
                    base_width = img_cropped.width
                    logo_width = int(base_width * (watermark_size / 100))
                    w_percent = logo_width / float(logo.size[0])
                    logo_height = int(float(logo.size[1]) * w_percent)
                    logo = logo.resize((logo_width, logo_height), Image.LANCZOS)
                    pos_x = img_cropped.width - logo_width - watermark_margin
                    pos_y = img_cropped.height - logo_height - (watermark_margin // 2)
                    img_cropped.paste(logo, (pos_x, pos_y), logo)

                images.append(img_cropped)

            if not images:
                st.error("No valid images were processed. Please upload at least one supported file.")
                st.stop()

            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            if output_format == "GIF":
                output_path = os.path.join(tmpdir, f"twnty_two_hat_{timestamp}.gif")
                images[0].save(output_path, save_all=True, append_images=images[1:], duration=int(duration * 1000), loop=0)
                mime = "image/gif"
            else:
                output_path = os.path.join(tmpdir, f"twnty_two_hat_{timestamp}.mp4")
                import numpy as np
                clip = ImageSequenceClip([np.array(img) for img in images], fps=1 / duration)
                clip.write_videofile(output_path, codec="libx264", audio=False, verbose=False, logger=None)
                mime = "video/mp4"

            st.success(f"{output_format} created!")
            if output_format == "GIF":
                st.image(output_path, caption="Preview", use_container_width=True)
            else:
                st.video(output_path)
                

            with open(output_path, "rb") as f:
                st.download_button(f"Download {output_format}", f, file_name=os.path.basename(output_path), mime=mime)

st.markdown("---")
st.markdown("<div style='text-align: center; font-size: 0.9rem; color: #777;'>Made by <a href='https://masvida.agency' target='_blank' style='color: #777; text-decoration: none;'>🏵 Más Vida Agency 🏵 for TWNTY-TWO®️ </a></div>", unsafe_allow_html=True)
