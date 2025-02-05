import uuid
import streamlit as st
from elevenlabs import set_api_key
from pydub import AudioSegment
import openai

from prompts import (podcast_ads, podcast_intro, podcast_outro,
                     podcast_segment, podcast_segue)
from utils import date_stuff, eleven_labs_stuff, open_ai_stuff, string_stuff

_SECOND = 1000


def gencast(name, desc, topics, ads):
    current_date = date_stuff.get_tomorrows_date_for_file_names()
    unique_id = uuid.uuid4()

    # (CONTENT) Generate scripts for top 3 comments from FIRST pinned post
    script_segments = []
    for topic in topics:
        script_segment = open_ai_stuff.generate_response(podcast_segment.SYSTEM_PROMPT, podcast_segment.PROMPT.format(topic=topic))
        script_segments.append(script_segment)

    # (ADS) Generate scripts for top 2 comments from SECOND pinned post
    script_ads = []
    for ad in ads:
        script_ad = open_ai_stuff.generate_response(podcast_ads.SYSTEM_PROMPT, podcast_ads.PROMPT.format(product=ad))
        script_ads.append(script_ad)

    # Generate an intro for the generated material
    intro = open_ai_stuff.generate_response(
        podcast_intro.SYSTEM_PROMPT,
        podcast_intro.PROMPT.format(
            segment_1=script_segments[0],
            segment_2=script_segments[1],
            segment_3=script_segments[2],
            podcast_name=name,
            podcast_desc=desc,
        ),
    )

    segue_1 = open_ai_stuff.generate_response(
        podcast_segue.SYSTEM_PROMPT,
        podcast_segue.PROMPT.format(
            count_descriptor="first",
            segment=script_segments[0],
        ),
    )

    segue_2 = open_ai_stuff.generate_response(
        podcast_segue.SYSTEM_PROMPT,
        podcast_segue.PROMPT.format(
            count_descriptor="second",
            segment=script_segments[1],
        ),
    )

    segue_3 = open_ai_stuff.generate_response(
        podcast_segue.SYSTEM_PROMPT,
        podcast_segue.PROMPT.format(
            count_descriptor="third",
            segment=script_segments[2],
        ),
    )

    outro = open_ai_stuff.generate_response(
        podcast_outro.SYSTEM_PROMPT,
        podcast_outro.PROMPT.format(
            segment_1=script_segments[0],
            segment_2=script_segments[1],
            segment_3=script_segments[2],
            ad_1=script_ads[0],
            ad_2=script_ads[1],
            podcast_name=name,
            podcast_desc=desc,
        ),
    )

    # Write the script to a file
    output_dir = "src/generated_podcast_scripts/"
    output_file = f"{output_dir}{current_date}_{unique_id}.txt"
    with open(output_file, "w+") as script_file:
        script_file.write(
            "\n".join(
                [
                    string_stuff.script_header("Intro"),
                    intro,
                    string_stuff.script_header("Segue 1"),
                    segue_1,
                    string_stuff.script_header("Segment 1"),
                    script_segments[0],
                    string_stuff.script_header("Ad Break 1"),
                    script_ads[0],
                    string_stuff.script_header("Segue 2"),
                    segue_2,
                    string_stuff.script_header("Segment 2"),
                    script_segments[1],
                    string_stuff.script_header("Ad Break 2"),
                    script_ads[1],
                    string_stuff.script_header("Segue 3"),
                    segue_3,
                    string_stuff.script_header("Segment 3"),
                    script_segments[2],
                    string_stuff.script_header("Outro"),
                    outro,
                ]
            )
        )

    # Use elevenlabs to generate the MP3s
    intro_audio = eleven_labs_stuff.convert_text_to_mp3(text=intro, voice=eleven_labs_stuff.HOST_VOICE)
    segue_1_audio = eleven_labs_stuff.convert_text_to_mp3(text=segue_1, voice=eleven_labs_stuff.HOST_VOICE)
    segue_2_audio = eleven_labs_stuff.convert_text_to_mp3(text=segue_2, voice=eleven_labs_stuff.HOST_VOICE)
    segue_3_audio = eleven_labs_stuff.convert_text_to_mp3(text=segue_3, voice=eleven_labs_stuff.HOST_VOICE)
    segment_1_audio = eleven_labs_stuff.convert_text_to_mp3(text=script_segments[0], voice=eleven_labs_stuff.HOST_VOICE)
    segment_2_audio = eleven_labs_stuff.convert_text_to_mp3(text=script_segments[1], voice=eleven_labs_stuff.HOST_VOICE)
    segment_3_audio = eleven_labs_stuff.convert_text_to_mp3(text=script_segments[2], voice=eleven_labs_stuff.HOST_VOICE)
    ad_1_audio = eleven_labs_stuff.convert_text_to_mp3(text=script_ads[0], voice=eleven_labs_stuff.ADS_VOICE)
    ad_2_audio = eleven_labs_stuff.convert_text_to_mp3(text=script_ads[1], voice=eleven_labs_stuff.ADS_VOICE)
    outro_audio = eleven_labs_stuff.convert_text_to_mp3(text=outro, voice=eleven_labs_stuff.HOST_VOICE)

    # Load music segments
    music_forest = AudioSegment.from_mp3("src/music/whistle-vibes-172471.mp3")
    music_beachside = AudioSegment.from_mp3("src/music/lofi-chill-medium-version-159456.mp3")
    music_feriado = AudioSegment.from_mp3("src/music/bolero-161191.mp3")
    music_typewriter = AudioSegment.from_mp3("src/music/scandinavianz-thessaloniki-free-download-173689.mp3")

    # Trim and apply fade outs to music segments
    music_forest = music_forest[: 6 * _SECOND].fade_out(2 * _SECOND)
    music_beachside = music_beachside[: 6 * _SECOND].fade_out(2 * _SECOND)
    music_feriado = music_feriado[: 6 * _SECOND].fade_out(2 * _SECOND)
    music_typewriter = music_typewriter[: 6 * _SECOND].fade_out(2 * _SECOND)

    # Stitch together podcast
    podcast = music_forest.overlay(intro_audio[:_SECOND], position=5 * _SECOND)
    podcast += intro_audio[_SECOND:]  # Add remaining part of intro_audio
    podcast += AudioSegment.silent(duration=1 * _SECOND)
    podcast += segue_1_audio
    podcast += AudioSegment.silent(duration=1 * _SECOND)
    podcast += music_beachside.overlay(segment_1_audio[:_SECOND], position=5 * _SECOND)
    podcast += segment_1_audio[_SECOND:]  # Add remaining part of segment_1_audio
    podcast += AudioSegment.silent(duration=2 * _SECOND)
    podcast += ad_1_audio
    podcast += AudioSegment.silent(duration=2 * _SECOND)
    podcast += segue_2_audio
    podcast += AudioSegment.silent(duration=1 * _SECOND)
    podcast += music_feriado.overlay(segment_2_audio[:_SECOND], position=5 * _SECOND)
    podcast += segment_2_audio[_SECOND:]  # Add remaining part of segment_2_audio
    podcast += AudioSegment.silent(duration=2 * _SECOND)
    podcast += ad_2_audio
    podcast += AudioSegment.silent(duration=2 * _SECOND)
    podcast += segue_3_audio
    podcast += AudioSegment.silent(duration=1 * _SECOND)
    podcast += music_typewriter.overlay(segment_3_audio[:_SECOND], position=5 * _SECOND)
    podcast += segment_3_audio[_SECOND:]  # Add remaining part of segment_3_audio
    podcast += AudioSegment.silent(duration=2 * _SECOND)
    podcast += music_forest
    podcast += outro_audio

    # Export the final audio file
    output_dir = "src/generated_podcast_mp3s/"
    output_file = f"{output_dir}{current_date}_{unique_id}.mp3"
    podcast.export(output_file, format="mp3")


st.set_page_config(
    page_title="KeepYourMouthShut",
    page_icon="assets/kyms-logo.png",
    layout="centered",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': 'https://www.reddit.com/r/KeepYourMouthShut/',
        'Report a bug': "https://github.com/rajtilakjee/keepyourmouthshut/issues",
        'About': "https://www.keepyourmouthshut.net/"
    }
)

st.title("KeepYourMouthShut")
st.sidebar.image("assets/kyms-logo.png")

with st.sidebar:
    openai_api_key = st.text_input("OpenAI API Key", type="password")
    "[Get an OpenAI API key](https://platform.openai.com/account/api-keys)"
    eleven_labs_api_key = st.text_input("ElevenLabs API key", type="password")
    "[Get an ElevenLabs API key](https://elevenlabs.io)"
    set_api_key(eleven_labs_api_key)
    openai.api_key = openai_api_key

with st.form("main_form"):
    st.subheader("Basic Information")
    name = st.text_input("Podcast Name")
    desc = st.text_input("Description/Tagline")

    st.subheader("Segments")
    topic1 = st.text_area("Topic for First Segment")
    topic2 = st.text_area("Topic for Second Segment")
    topic3 = st.text_area("Topic for Third Segment")

    st.subheader("Advertisements")
    ad1 = st.text_area("First Advertisement")
    ad2 = st.text_area("Second Advertisement")

    submitted = st.form_submit_button("Submit")

    if not openai_api_key and not eleven_labs_api_key:
        st.info("Please add both your OpenAI API key and ElevenLabs API key to continue.")
    elif not openai_api_key:
        st.info("Please add your OpenAI API key to continue.")
    elif not eleven_labs_api_key:
        st.info("Please add your ElevenLabs API key to continue.")
    elif submitted:
        topics = [topic1, topic2, topic3]
        ads = [ad1, ad2]
        gencast(name, desc, topics, ads)
