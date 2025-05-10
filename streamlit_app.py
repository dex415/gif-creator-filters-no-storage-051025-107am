import streamlit as st
from PIL import Image, ImageEnhance, UnidentifiedImageError
import os
import tempfile
import imageio
import io
from moviepy.editor import ImageSequenceClip
from datetime import datetime
from streamlit_sortables import sort_items

st.set_page_config(page_title="🧢 TWNTY-TWO GIF Creator", layout="centered")

st.markdown("""
    <style>
    .main {background-color: #fff;}
    h1, h2, h3 {color: #111; font-family: 'Helvetica Neue', sans-serif;}
    .stButton>button {background-color: #111;color: white;border-radius: 8px;}
    </style>
""", unsafe_allow_html=True)

st.image("https://twnty-two-assets.s3.amazonaws.com/twnty-two-icon.png", width=100)
st.title("🧢 TWNTY-TWO GIF Creator")
st.markdown("""
### Level Up Your Drops
Create looping visuals for your Friday and 22nd drops in seconds.
""")

uploaded_files = st.file_uploader("Drag and drop or browse to upload images", accept_multiple_files=True, type=["png", "jpg", "jpeg"])
duration = st.slider("Frame display time (seconds)", min_value=0.5, max_value=5.0, value=1.5, step=0.1)
output_format = st.radio("Choose output format", ["GIF", "MP4 (video)"])

preset = st.selectbox("🎛️ Choose a preset", ["None", "Friday Drop", "Promo Loop"])
if preset == "Friday Drop":
    duration = 1.5
    output_format = "GIF"
elif preset == "Promo Loop":
    duration = 2.2
    output_format = "MP4 (video)"

add_watermark = st.checkbox("Add TWNTY-TWO logo watermark", value=True)
watermark_size = st.slider("Watermark size (% of image width)", 5, 30, 15)
watermark_margin = st.slider("Watermark margin (px)", 0, 50, 10)

apply_bw = st.checkbox("Apply black & white filter")
apply_contrast = st.checkbox("Boost contrast")

LOGO_PATH = "logo.png"

if uploaded_files:
    file_dict = {}
    for file in uploaded_files:
        try:
            img = Image.open(file)
            img.verify()
            file_dict[file.name] = file
        except Exception:
            st.warning(f"Skipping {file.name}: not a valid image.")

    if not file_dict:
        st.error("No valid images uploaded. Please check your files.")
        st.stop()

    st.markdown("**Drag images to sort their order:**")
    ordered_filenames = sort_items(list(file_dict.keys()))

    col1, col2 = st.columns([1, 4])
    with col1:
        if st.button("Reset Order"):
            ordered_filenames = list(file_dict.keys())
    with col2:
        st.caption("(Final preview shown below before export)")

    for i, fname in enumerate(ordered_filenames):
        try:
            st.image(Image.open(file_dict[fname]), width=150, caption=f"{i+1}. {fname}")
        except UnidentifiedImageError:
            st.warning(f"Could not display preview for: {fname}")

    if st.button("Create Output"):
        with tempfile.TemporaryDirectory() as tmpdir:
            images = []
            for fname in ordered_filenames:
                file = file_dict[fname]
                img_path = os.path.join(tmpdir, file.name)
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

                if add_watermark and os.path.exists(LOGO_PATH):
                    logo = Image.open(LOGO_PATH).convert("RGBA")
                    logo_size = int(min_side * (watermark_size / 100))
                    logo = logo.resize((logo_size, logo_size))
                    pos_x = img_cropped.size[0] - logo_size - watermark_margin
                    pos_y = img_cropped.size[1] - logo_size - watermark_margin
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
                clip = ImageSequenceClip([img for img in images], fps=1 / duration)
                clip.write_videofile(output_path, codec="libx264", audio=False, verbose=False, logger=None)
                mime = "video/mp4"

            st.success(f"{output_format} created!")
            with open(output_path, "rb") as f:
                st.download_button(f"Download {output_format}", f, file_name=os.path.basename(output_path), mime=mime)

st.markdown("---")
st.markdown("Want to publish this on social media? Copy your download and [head to Meta Creator Studio](https://business.facebook.com/creatorstudio) to share to Instagram or Threads.")
