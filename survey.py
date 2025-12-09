import streamlit as st
import pandas as pd
import os
import glob
import random
import uuid

# ---------- CONFIG ----------
IMAGES_DIR = "dataset"   
DEMO_DIR = "demo"        
CSV_PATH = "responses.csv"     
RATING_MIN = 1
RATING_MAX = 5
PARTICIPANTS_CSV = "participants.csv"
# ----------------------------


st.set_page_config(page_title="Image Rating Survey", layout="wide")
hide_streamlit_style = """
    <style>
        /* Remove padding at the top of the main content */
        .block-container {padding-top: 0rem; padding-left: 1rem; padding-right: 2rem; padding-bottom: 1rem;}
        /* Hide the top hamburger menu */
        #MainMenu {visibility: hidden;}
        /* Hide the top header */
        header {visibility: hidden;}
        /* Hide the footer */
        footer {visibility: hidden;}
        img {
            max-width: 100% !important;
            height: auto !important;
            max-height: 95vh !important; /* fit vertically */
            }
    </style>
"""
st.markdown(hide_streamlit_style, unsafe_allow_html=True)

# ---------- Helpers ----------
def list_images(directory):
    patterns = ["*.jpg", "*.jpeg", "*.png", "*.gif", "*.bmp", "*.webp"]
    files = []
    for p in patterns:
        files.extend(glob.glob(os.path.join(directory, p)))
    files = sorted(files)
    return files


def ensure_csv_header(path):
    if not os.path.exists(path):
        df = pd.DataFrame(columns=[
            "participant_id",
            "image_filename",
            "image_index",
            "rating",
            "timestamp"
        ])
        df.to_csv(path, index=False)


def append_response(path, row: dict):
    df = pd.DataFrame([row])
    df.to_csv(path, mode="a", header=not os.path.exists(path), index=False)


def ensure_participants_csv(path):
    if not os.path.exists(path):
        df = pd.DataFrame(columns=[
            "participant_id",
            "age",
            "role",
            "gender",
            "social_activity",
            "consent",
            "timestamp_utc"
        ])
        df.to_csv(path, index=False)


def save_participant_row(path, row: dict):
    df = pd.DataFrame([row])
    df.to_csv(path, mode="a", header=not os.path.exists(path), index=False)


def generate_unique_id(csv_path=PARTICIPANTS_CSV):
    existing_ids = set()
    if os.path.exists(csv_path):
        try:
            df = pd.read_csv(csv_path)
            if "participant_id" in df.columns:
                existing_ids = set(df["participant_id"].astype(str))
        except Exception:
            pass 
    # Generate new IDs until one is not in the set
    while True:
        new_id = str(uuid.uuid4())[:8]
        if new_id not in existing_ids:
            return new_id




# ---------- Initialize session state ----------
if "page" not in st.session_state:
    st.session_state.page = "intro"   

if "participant_id" not in st.session_state:
    st.session_state.participant_id = generate_unique_id()

if "images_list" not in st.session_state:
    images = list_images(IMAGES_DIR)
    if images:
        random.shuffle(images)
    st.session_state.images_list = images or []
    st.session_state.current_index = 0
    st.session_state.session_responses = []

if "demo_list" not in st.session_state:
    demo_imgs = list_images(DEMO_DIR)
    if demo_imgs:
        random.shuffle(demo_imgs)
        demo_imgs = demo_imgs[:10]  # take first 10 after shuffle
    st.session_state.demo_list = demo_imgs or []
    st.session_state.demo_index = 0




# ---------- Page: INTRO ----------
def show_intro():
    _, col2, _ = st.columns([3,5,3])
    with col2:
        st.title("Image Quality Rating Survey")
        st.markdown(
            """
            **Welcome, and thank you for participating in this study.**

            ### **Instructions**

            - Your task is to evaluate a series of images based on their visual quality.  
            - For each image, please assign a rating from **1 (lowest quality)** to **5 (highest quality)**, then proceed to the next item. Once a rating is submitted, you will **not** be able to return to the previous image.  
            - Each evaluation should require only a short amount of time, although there is **no time limit** for your responses.  
            - Before beginning the main study, you will complete a brief tutorial to familiarize yourself with the task and interface. Tutorial responses will **not** be recorded.  
            - You will also be asked to provide some **accurate personal information** for research purposes.
            """)

        st.markdown("---")
        
        # Show basic info about images
        if not st.session_state.images_list:
            st.error(f"No images found in `{IMAGES_DIR}`. Add jpg/png files there and refresh.")
            return

        st.write("When you feel ready, click the **Start** button below.")
        st.markdown("")
        if st.button("Start"):
            st.session_state.page = "informations"
            st.rerun()




# ---------- Page: INFORMATIONS -----------
def show_personal_info():
    _, col2, _ = st.columns([3,5,3])
    with col2:        
        st.title("Participant Information")
        st.markdown("""
        <div style="max-width:800px; margin:auto;">
        <p>
            Before you begin rating the images, please provide a few non-sensitive details about yourself.  
            Your responses will be <strong>anonymized</strong> and used solely for aggregated analysis.
        </p>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("---")

        st.markdown("#### Personal information (required fields are marked *)")

        # Age: numeric input (required)
        if "age" not in st.session_state:
            st.session_state.age = None

        age_options = ["-", "<10"] + [str(i) for i in range(10, 91)] + [">90"]
        age = st.selectbox("Age *", options=age_options, index=0)
        if age != "-":
            st.session_state.age = age
        else:
            st.session_state.age = None

        sex_options = ["-", "Prefer not to say", "Female", "Male"]
        sex = st.selectbox("Sex *", options=sex_options, index=0)
        if sex != "-":
            st.session_state.sex = sex
        else:
            st.session_state.sex = None

        color_blind_options = ["-", "Yes", "No"]
        color_blind = st.selectbox("Do you have any form of color vision deficiency (color blindness)? *",
                                   options=color_blind_options, index=0) 
        if color_blind != "-":
            st.session_state.color_blind = color_blind
        else:
            st.session_state.color_blind = None

        expertise_options = ["-", "Yes", "No"]
        expertise = st.selectbox("Do you have professional or hobby-level experience in photography, computer graphics or other imaging form? *",
                                 options=expertise_options, index=0) 
        if expertise != "-":
            st.session_state.expertise = expertise
        else:
            st.session_state.expertise = None

        # Validation: disable start button unless required fields are present and consent given
        if (st.session_state.age is None or st.session_state.sex is None or
            st.session_state.color_blind is None or st.session_state.expertise is None):
            start_disabled = True 
        else:
            start_disabled = False
        
        st.markdown("---")

        consent = st.checkbox("I consent to my (anonymized) responses being used for research/analysis.", 
                              value=st.session_state.get("consent", False))
        
        st.session_state.consent = consent

        # Start button
        if st.button("Start demo", disabled=(start_disabled or not st.session_state.consent)):
            # write participant row to participants.csv
            ensure_participants_csv(PARTICIPANTS_CSV)
            row = {
                "participant_id": st.session_state.participant_id,
                "age": st.session_state.age,
                "sex": st.session_state.sex,
                "color_blind": st.session_state.color_blind,
                "expertise": st.session_state.expertise,
                "consent": st.session_state.consent,
            }
            save_participant_row(PARTICIPANTS_CSV, row)

            # move to rating page
            st.session_state.page = "demo_intro"
            st.rerun()

        if start_disabled and not st.session_state.consent:
            st.info("Please complete all required fields and give your consent to continue.")
        elif not st.session_state.consent:
            st.info("Please give your consent to continue.")
        elif start_disabled:
            st.info("Please complete all required fields to continue.")




# ---------- Page: DEMO_INTRO -----------
def show_demo_intro():
    _, col2, _ = st.columns([3,5,3])
    with col2: 
        st.title("Demo Introduction")

        st.write(
            """
            In this brief tutorial, you will be introduced to the image rating procedure.

            You will:
            - Become familiar with the interface.
            - Assign a rating from **1 to 5** for each presented image.
            - Proceed to the next image by selecting the designated button.
            - Practice the rating process using a small set of example images.

            This tutorial is intended solely to help you understand the task and interface; **no responses will be recorded**.  
            Your actual ratings will begin immediately afterward.
            """
        )

        st.markdown("---")

        st.write("When you feel ready, click the **Start demo** button below.")

        st.markdown("")  

        if st.button("Start demo"):
            st.session_state.page = "demo"
            st.rerun()




# ---------- Page: DEMO -----------
def show_demo():
    demo_imgs = st.session_state.demo_list
    idx = st.session_state.demo_index
    total = len(demo_imgs)
    
    image_path = demo_imgs[idx]

    if "show_info" not in st.session_state:
        st.session_state.show_info = 1

    left_col, right_col = st.columns([3, 2])
    with left_col:
        st.image(image_path)

    with right_col:
        st.markdown("""## [DEMO]""")

        if st.session_state.show_info == 1:
            st.info("This is the image you will rate", icon="⬅️")
            if st.button("Next"):
                st.session_state.show_info = 2
                st.rerun()

        col_1, col_2 = st.columns([4, 1])
        with col_1:
            progress = int((idx+1) / max(1, total) * 100)
            st.progress(progress)
        with col_2:
            st.write(f"{idx+1}/{total} done")
        if st.session_state.show_info == 2:
            st.info("This is the prorgess you've made", icon="⬆️")
            if st.button("Next"):
                st.session_state.show_info = 3
                st.rerun()
        
        key_rating = f"rating_{idx}"
        options = [None, 1, 2, 3, 4, 5]
        labels = {None: "—", 1:"1", 2:"2", 3:"3", 4:"4", 5:"5"}

        st.header("Rate the quality of the image")
        rating = st.radio(
            label = "Select a value",
            options=options,
            format_func=lambda x: labels[x],
            horizontal=True,
            key=key_rating,
            disabled=(st.session_state.show_info < 5),
            label_visibility="collapsed")
        
        st.markdown("""
            <div style="display: flex; justify-content: space-between; width: 100%;">
                <span>1 = lowest quality</span>
                <span>5 = best quality</span>
            </div>
            <p></p>
            """, unsafe_allow_html=True)

        if st.session_state.show_info == 3:
            st.info("Here you select the rating of the image. Please answer quickly.", icon="⬆️")
            if st.button("Next"):
                st.session_state.show_info = 4
                st.rerun()

        # Button is disabled if rating is None
        next_button = st.button("Finish demo" if idx + 1 == total else "Next image", 
                  disabled=(rating is None))

        if st.session_state.show_info == 4:
            st.info("And with this button you can go to the next image, after having selected a rating. Attention: you cannot go back once you submit the rating.", icon="⬆️")
            if st.button("Start demo"):
                st.session_state.show_info = 5
                st.rerun()

        if next_button:
            # advance or finish
            if idx + 1 < total:
                st.session_state.demo_index += 1
                st.rerun()
            else:
                st.session_state.page = "start"
                st.rerun()




# ---------- Page: START -----------
def show_start():
    _, col2, _ = st.columns([3,5,3])
    with col2:
        st.title("Start the survey")
        st.write("The tutorial is now complete, and you may proceed to the main survey.")
        st.write("The instructions are provided once more for your reference.")

        st.markdown(
            """
            ### **Instructions**
            - Your task is to evaluate images based on their visual quality.  
            - For each image, please assign a rating from **1 (lowest quality)** to **5 (highest quality)**.  
            - Once you submit a rating, you will **not** be able to return to the previous image.  
            - Each rating is expected to take only a **short amount of time**, but there is no time limit.
            - When you are confident in your assessment, proceed to the next image.
            """
        )

        st.markdown("---")

        st.write("When you feel ready, click the **Start survey** button below.")
        
        st.markdown("")

        if st.button("Start survey"):
            st.session_state.page = "rating"
            st.rerun()




# ---------- Page: RATING ----------
def show_rating():
    images = st.session_state.images_list
    idx = st.session_state.current_index
    total = len(images)

    image_path = images[idx]
    
    left_col, right_col = st.columns([3, 2])
    with left_col:
        st.image(image_path, width="content")
    
    with right_col:
        col_1, col_2 = st.columns([4, 1])
        with col_1:
            progress = int((idx+1) / max(1, total) * 100)
            st.progress(progress)
        with col_2:
            st.write(f"{idx+1}/{total} done")

        key_rating = f"rating_{idx}"
        options = [None, 1, 2, 3, 4, 5]
        labels = {None: "—", 1:"1", 2:"2", 3:"3", 4:"4", 5:"5"}

        st.header("Rate the quality of the image")
        rating = st.radio(
            label = "Select a value",
            options=options,
            format_func=lambda x: labels[x],
            horizontal=True,
            key=key_rating,
            label_visibility="collapsed")
        
        st.markdown("""
            <div style="display: flex; justify-content: space-between; width: 100%;">
                <span>1 = lowest quality</span>
                <span>5 = best quality</span>
            </div>
            <p></p>
            """, unsafe_allow_html=True)

        # Button is disabled if rating is None
        next_button = st.button("Finish survey" if idx + 1 == total else "Next image", 
                                disabled=(rating is None))
    
        if next_button:
            # save to CSV immediately
            ensure_csv_header(CSV_PATH)
            row = {
                "participant_id": st.session_state.participant_id,
                "image_filename": os.path.basename(image_path),
                "rating": int(rating),
            }
            append_response(CSV_PATH, row)
            # also keep in session
            st.session_state.session_responses.append(row)

            # advance or finish
            if idx + 1 < total:
                st.session_state.current_index += 1
                st.rerun()
            else:
                st.session_state.page = "done"
                st.rerun()




# ---------- Page: DONE ----------
def show_done():
    _, col2, _ = st.columns([3,5,3])
    with col2:
        st.title("Survey complete")
        st.write("Thank you!")
        st.write("You completed the survey and all answers have been saved.")
        st.write("You can now leave the site.")






# ---------- Router ----------
if st.session_state.page == "intro":
    show_intro()
elif st.session_state.page == "informations":
    show_personal_info()
elif st.session_state.page == "demo_intro":
    show_demo_intro()
elif st.session_state.page == "demo":
    show_demo()
elif st.session_state.page == "start":
    show_start()
elif st.session_state.page == "rating":
    show_rating()
elif st.session_state.page == "done":
    show_done()
else:
    st.error("Unknown page state. Resetting to intro.")
    st.session_state.page = "intro"
    st.rerun()

