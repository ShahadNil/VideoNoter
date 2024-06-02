import streamlit as st
from pathlib import Path
import google.generativeai as genai
import os
import time
import tempfile
from pytube import YouTube
import re

os.environ["GEMINI_API_KEY"] = 'AIzaSyC6XZZpQZ2uGgmtYakbY2-1wP37r2Kq7WE'
genai.configure(api_key=os.environ["GEMINI_API_KEY"] )
responses = None
file_name = None
video = None
generation_config = {
  "temperature": 0.2,
  "top_p": 0.95,
  "top_k": 0,
  "max_output_tokens": 20000,
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
      4. Use bullet points and numbering points where needed. Give detailed information about each point . Unnecessary using of bullet points and numbering points should be prohibitted.
      5. Use mathemetical markdown formats to show a clear mathemetical equations and answers.
      6. Write every detail you need to satisfy the task. You can write upto 10000 words , so do not hesitate using more words.. 
      7. Act as a professional , do not include casual words.
      8. Take informations from visuals and audio when the visual is related the main topic. If the visuals are not related to the main lecture, ignore it
      
      DO NOT:
      1. Do not use your words, don't add any information yourself. Use informations covered in the lecture.
      2. Do not respond if the video is not related to any lecture or educational.
      3. Do not use bullet or numbering point everywhere. Like a single informative point must be written using bullet point. Otherwise, a information which is needed to be written in detail, that should be written in a short detailed paragraph.

      Key Responsibilites:
      1. Provide a detailed summary of the whole lecture at first.
      2. Find out the topics covered in the lecture.
      3. Write down important key notes of each topic. It should be detailed.
      4. If the lecture covers different parts , divide them into different segments.
      5. Your main responsibility is to provide a note of the long lecture , which note contains every detail covered in the lecture .
    """
]


model = genai.GenerativeModel(model_name="gemini-1.5-pro-latest",
                              generation_config=generation_config,
                              safety_settings=safety_settings,
                              system_instruction=prompts[0])
def upload_to_gemini(path, mime_type=None):
  file =genai.upload_file(path, mime_type=mime_type)
  print(f"Uploaded file '{file.name}' as: {file.uri}")
  return file


def wait_for_files_active(file):
  file_need = genai.get_file(file.name)
  while file_need.state.name == "PROCESSING":
    print(".", end="", flush=True)
    time.sleep(10)
    file_need = genai.get_file(file.name)
  if file_need.state.name != "ACTIVE":
    st.error(f"File {file.name} failed to process")

def sanitize_title(title):
    return re.sub(r'[\\/*?:"<>|]', "", title)

st.set_page_config(page_title="Keynoter", page_icon='📝',layout="wide" )
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
  options = st.radio("**Select an Option**", ["Upload a video file", "Directly from youtube link"])
  if options == "Upload a video file":
     uploader = st.file_uploader('Upload the lecture video', type=['mp4', 'mkv'])
     if uploader:
        temp_dir = tempfile.mkdtemp(prefix="gemini")
        path = os.path.join(temp_dir, uploader.name)
        with open(path, "wb") as f:
          f.write(uploader.getvalue())
        st.sidebar.video(path)
        pass
     else:
        st.stop()




  elif options == "Directly from youtube link":
      video_url = st.text_input("**Enter your Youtube Video URL**")
      if video_url !="" and video_url.startswith("https://www.youtube.com/watch?v="):
            try:
                yt = YouTube(video_url)
                if yt.streams.filter(res="720p", progressive=True).first() is not None:
                    video = yt.streams.filter(res="720p", progressive=True).first()
                    res = st.success("**720p stream found!**")
                elif yt.streams.filter(res="480p", progressive=True).first() is not None:
                    video = yt.streams.filter(res="480p", progressive=True).first()
                    res = st.success("**480p stream found!**")
                elif yt.streams.filter(res="360p", progressive=True).first() is not None:
                    video = yt.streams.filter(res="360p", progressive=True).first()
                    res = st.success("**360p stream found!**")
                else:
                    st.error("**No suitable video resolution found.**")
                    st.stop()
                        
                if video:
                    try:
                      video_title = yt.title 
                      sanitized_title = sanitize_title(video_title)
                      path = f"{sanitized_title}.mp4"
                      downloading = st.success("**Downloading on progress..**")
                      video.download(filename=path)
                      res.empty()
                      downloading.empty()
                      st.sidebar.video(path)
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
     st.stop()
 

  submit_button = st.button("Done")
  if submit_button:
        pass
  else:
      st.stop()

place.empty()




success = st.warning("**Wait a few moments to process the video**")

try:
  video_obj =  upload_to_gemini(path)
  wait_for_files_active(video_obj)
except Exception as e:
  st.error(e)

success.empty()

chat_session = model.start_chat(
  history=[
    {
      "role": "user",
      "parts": [
        video_obj,
      ],
    },
  ]
)
while responses == None:
  generating = st.info("**Your note is generating. Please be patient.**")
  try:
    responses = chat_session.send_message("Here is the video. Follow instructions you are given and give a detailed note of the whole lecture.")
  except Exception as e:
      st.error(e)
generating.empty()
st.write(responses.text)
os.remove(path)

genai.delete_file(video_obj.name)
