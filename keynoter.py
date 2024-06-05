import streamlit as st
from pathlib import Path
import google.generativeai as genai
import os
import time
import tempfile
from pytube import YouTube
import re

#genai.configure(api_key='AIzaSyC6XZZpQZ2uGgmtYakbY2-1wP37r2Kq7WE')
state = st.session_state
if 'video_obj' not in state:
   state.video_obj = None 
if 'path' not in state:
   state.path = ""
if 'button' not in state:
   state.button = None
if 'submit_button' not in state:
   state.submit_button = None 
if 'video_url' not in state:
   state.video_url = ""
if 'button' not in state:
   state.button=None
if 'done_button' not in state:
   state.done_button= None
if 'options' not in state:
   state.options= None

if 'temp_dir' not in state:
   state.temp_dir = None
if 'responses' not in state:
   state.responses = None
if 'regen_responses' not in state:
   state.regen_responses = None

file_name= None
video = None
generation_config = {
  "temperature": 0.2,
  "top_p": 0.95,
  "top_k": 0,
  "max_output_tokens": 8192,
}

safety_settings = [
  {
    "category": "HARM_CATEGORY_HARASSMENT",
    "threshold": "BLOCK_MEDIUM_AND_ABOVE"
  },
  {
    "category": "HARM_CATEGORY_HATE_SPEECH",
    "threshold": "BLOCK_MEDIUM_AND_ABOVE"
  },
  {
    "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
    "threshold": "BLOCK_MEDIUM_AND_ABOVE"
  },
  {
    "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
    "threshold": "BLOCK_MEDIUM_AND_ABOVE"
  },
]

prompts = [
    """You are a domain expert to note and summarize a lecture or any educational video. Educational videos are one kind of lecture. So allover your task is to note any lecture.
      You will be tasked with a video lecture on any topic. Your expertise will help in noting whole lecture. 
      Some key responsibilites and instructions are given to you, follow them to provide your best.

      Instructions include:
      1. Use MARKDOWN format to show a clean and beautiful response, and it will help users to achieve a great experience with you.
      2. Always provide a HEADLINE based on the whole lecture. Carefully choose the headline , because it represents the whole lecture in very brief.
      3. Write in different segments and under sub-headers. Every sub-header should include the detailed informations related to it.
      4. Use bullet points and numbering points where needed. Give detailed information about each point . Unnecessary using of bullet points and numbering points are prohibitted.
      5. Use latex formats to show a clear mathemetical equations and answers.
      6. Write every detail you need to satisfy the task. You can write upto 10000 words , so do not hesitate using more words.. 
      7. Act as a professional , do not include casual words.
      8. Take informations from visuals and audio when the visual is related the main topic. If the visuals are not related to the main lecture, ignore it.
      9. You can provide links (if there) and if it is important to provide the link using markdown [LINK_NAME](LINK)

      Key Responsibilites:
      1. Provide a detailed summary of the whole lecture at first.
      2. Find out the topics covered in the lecture.
      3. Write down important key notes of each topic. It should be detailed.
      4. If the lecture covers different parts , divide them into different segments.
      5. Your main responsibility is to provide a note of the long lecture , which note contains every detail covered in the lecture .

      DO NOT:
      1. Do not use your words, don't add any information yourself. Use informations covered in the lecture.
      2. Do not use HTML code to show texts beautiful , you can use MARKDOWN or LATEX .
      2. Do not respond if the video is not related to any lecture or educational.
      3. Do not miss any important detail. 
    """
]

#      3. Do not use bullet or numbering point everywhere. Like a single informative point must be written using bullet point. Otherwise, a information which is needed to be written in detail, that should be written in a short detailed paragraph.
model = genai.GenerativeModel(model_name="gemini-1.5-pro-latest",
                              generation_config=generation_config,
                              safety_settings=safety_settings,
                              system_instruction=prompts[0])
def upload_to_gemini(path, mime_type=None):
  file =genai.upload_file(path, mime_type=mime_type)
  print(f"Uploaded file '{file.name}' as: {file.uri}")
  return file


def wait_for_files_active(file):
  file_need= genai.get_file(file.name)
  while file_need.state.name == "PROCESSING":
    print(".", end="", flush=True)
    time.sleep(10)
    file_need = genai.get_file(file.name)
  if file_need.state.name != "ACTIVE":
    st.error(f"File {file.name} failed to process")

def sanitize_title(title):
    return re.sub(r'[\\/*?:"<>|]', "", title)

def is_valid_api(api: str):
  genai.configure(api_key=api)
  try:
    list(genai.list_models())
  except:
    return False
  else:
    return True


st.set_page_config(page_title="Keynoter", page_icon='📝',layout="wide" )
api_config = st.empty()
with api_config.container():
  st.markdown(
      '<style> \
          .centered-title { \
              text-align: center; \
              color: #f8f8ff;  \
              weight: bold;\
          } \
      </style>', 
      unsafe_allow_html=True
  )

  st.markdown('<h2 class="centered-title">Note Your Lecture</h2>', unsafe_allow_html=True) 

  if 'api' not in st.session_state:
    api = st.text_input("**Enter your Google API**")
    state.button = st.button("Submit API")
    st.write("**Don't have an API?**")
    st.write("1. Sign in to your Google account on Chrome.")
    st.write("2. Go to [Google AI Studio](https://aistudio.google.com/app/apikey).")
    st.write("3. Follow the screenshots:")
    col1, col2, col3 = st.columns(3)
    with col1:
       st.image("ss1.png")
       st.write("*Click on the Create API key*")
    with col2:
       st.image("ss2.png")
       st.write("*Click on the Create API key for a new project*")
    with col3:
       st.image("ss3.png")
       st.write("*Copy the generated key*")

    if api!="" and state.button and is_valid_api(api=api):
        st.toast("**The API is valid**")
        st.session_state.api = api
        time.sleep(2)
        api_config.empty()
    elif api != "" and state.button and is_valid_api(api=api)==False :
        st.toast("**Invalid API**")
        st.stop()
    else:
        st.stop()
  else:
     api_config.empty()

place = st.empty()

with place.container():
  st.markdown(
      '<style> \
          .centered-title { \
              text-align: center; \
              color: #f8f8ff;  \
              weight: bold;\
          } \
      </style>', 
      unsafe_allow_html=True
  )

  st.markdown('<h2 class="centered-title">Note Your Lecture</h2>', unsafe_allow_html=True) 

  state.options = st.radio("**Select an Option**", ["Upload a video file", "Directly from youtube link"])
  if state.options == "Upload a video file":
    if state.path=="" and state.submit_button != True:
      uploader = st.file_uploader('Upload the lecture video', type=['mp4', 'mkv'])
      if uploader:
          temp_dir = tempfile.mkdtemp(prefix="gemini")
          state.path = os.path.join(temp_dir, uploader.name)
          with open(state.path, "wb") as f:
            f.write(uploader.getvalue())
          st.sidebar.video(state.path)
          state.submit_button = st.button("Get Notes")
          if state.submit_button:
            state.submit_button = True
            pass
          else:
            st.stop()
      else:
         st.stop()
    else:
        pass


  elif state.options == "Directly from youtube link":
      if state.path == "" and state.button != True:
          state.video_url = st.text_input("**Enter your Youtube Video URL**")
          state.button = st.button("Get Notes")
          if state.video_url !=""  and state.button and (state.video_url.startswith("https://www.youtube.com/watch?v=") or state.video_url.startswith("https://youtu.be/")):
                state.button = True
                try:
                    retrive = st.success("**Checking your video**")
                    yt = YouTube(state.video_url)
                    if yt.streams.filter(res="720p", progressive=True).first() is not None:
                        video = yt.streams.filter(res="720p", progressive=True).first()
                        retrive.empty()
                        res = st.success("**720p stream found!**")
                    elif yt.streams.filter(res="480p", progressive=True).first() is not None:
                        video = yt.streams.filter(res="480p", progressive=True).first()
                        retrive.empty()
                        res = st.success("**480p stream found!**")
                    elif yt.streams.filter(res="360p", progressive=True).first() is not None:
                        video = yt.streams.filter(res="360p", progressive=True).first()
                        retrive.empty()
                        res = st.success("**360p stream found!**")
                    else:
                        retrive.empty()
                        st.error("**No suitable video resolution found.**")
                        st.stop()
                            
                    if video:
                        try:
                          video_title = yt.title 
                          sanitized_title = sanitize_title(video_title)
                          state.path = f"{sanitized_title}.mp4"
                          downloading = st.success("**Downloading on progress..**")
                          video.download(filename=state.path)
                          res.empty()
                          downloading.empty()
                          st.sidebar.video(state.path)
                          pass
                        except Exception as e:
                          st.error(e)
                          st.stop()
                except Exception as e:
                    st.error(e)
                    st.stop()
                
          else:
            st.stop()

      else:
         pass


  else:
     st.stop()
 

place.empty()

if state.video_obj == None:
  try:
    success = st.warning("**Wait a few moments to process the video**")
    state.video_obj =  upload_to_gemini(state.path)
    wait_for_files_active(state.video_obj)  
    success.empty()
  except Exception as e:
    st.error(e)
else:
    pass


if 'history' not in state:
   state.history= [{"role":"user", "parts":[state.video_obj]}]

chat_session = model.start_chat(history=state.history)
while state.responses == None:
  generating = st.info("**Your note is generating. Please be patient.**")
  try:
    state.responses = chat_session.send_message("Here is the video. Follow instructions you are given and give a detailed note of the whole lecture.")
    state.history.append({"role":"model", "parts":[state.responses.text]})
  except Exception as e:
    st.error(e)

generating.empty()
generation_place = st.empty()
with generation_place.container():
  st.write(state.responses.text)

while state.regen_responses == None:
  feedback = st.sidebar.text_area("**Regenerate with Feedback**")
  regen= st.sidebar.button("Regenerate")
  if regen and feedback!="":
    regenerating = st.info("**Your note is regenerating..**")
    try:
        state.regen_responses = chat_session.send_message(f"Regenerate the note obeying the feedback from user. Feedback : {feedback}")
        state.history.append({"role":"model", "parts":[state.regen_responses.text]})
        generation_place.empty()
        generation_place = st.empty()
        with generation_place.container():
          st.write(state.regen_responses)
        state.regen_responses = None
    except Exception as e:
        st.error(e)
  else:
    st.stop()

state.done_button =st.button("Done")
if state.done_button:
  os.remove(state.path)
  genai.delete_file(state.video_obj.name)
  st.stop()
