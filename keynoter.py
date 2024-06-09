import streamlit as st
from pathlib import Path
import google.generativeai as genai
import os
import time
import tempfile
from pytube import YouTube
import re
import markdown
import pypandoc


#genai.configure(api_key='AIzaSyC6XZZpQZ2uGgmtYakbY2-1wP37r2Kq7WE')
states = st.session_state
if 'video_obj' not in states:
   states.video_obj = None 
if 'path' not in states:
   states.path = ""
if 'button' not in states:
   states.button = None
if 'submit_button' not in states:
   states.submit_button = None 
if 'video_url' not in states:
   states.video_url = ""
if 'note_button' not in states:
   states.note_button=None
if 'done_button' not in states:
   states.done_button= None
if 'responses' not in states:
   states.responses = None
if 'md_file_path' not in states:
   states.md_file_path = None
if 'pdf_file' not in states:
   states.pdf_file = None
if 'photos' not in states:
   states.photos = []
if 'parts' not in states:
   states.parts =[]
if 'photo_obj' not in states:
   states.photo_obj = []
if 'files' not in states:
   states.files = []
if 'photo_button' not in states:
   states.photo_button = None
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
      3. The header must be under ----------  
                                    HEADER 
                                  ---------- use hyphens until it covers whole header.
      4. Headers , subheaders and headlines should be slightly bigger and bold.    
      5. Write in different segments and under sub-headers. Every sub-header should include the detailed informations related to it.
      6. Use bullet points and numbering points where needed. Give detailed information about each point . Unnecessary using of bullet points and numbering points are prohibitted.
      7. Use latex formats to show a clear mathemetical equations and answers.
      8. Write every detail you need to satisfy the task. You can write upto 10000 words , so do not hesitate using more words.. 
      9. Act as a professional , do not include casual words.
      10. Take informations from visuals and audio when the visual is related the main topic. If the visuals are not related to the main lecture, ignore it.
      11. You can provide links (if there) and if it is important to provide the link using markdown [LINK_NAME](LINK)

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


model = genai.GenerativeModel(model_name="gemini-1.5-flash",
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
def converter(text):
    with tempfile.NamedTemporaryFile(delete=False, suffix='.md') as temp_md:
        states.md_file_path = temp_md.name
        temp_md.write(text.encode('utf-8')) 
    pdf_file = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
    pdf_file_path = pdf_file.name
    pdf_file.close()

    pypandoc.convert_file(states.md_file_path, 'pdf', outputfile=pdf_file_path,
                          extra_args=["-V", "geometry:margin=1in", "--pdf-engine=xelatex"])
    
    return pdf_file_path

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
    states.button = st.button("Submit API")
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

    if api!="" and states.button and is_valid_api(api=api):
        st.toast("**The API is valid**")
        st.session_state.api = api
        time.sleep(2)
        api_config.empty()
    elif api != "" and states.button and is_valid_api(api=api)==False :
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

  options = st.radio("**Select an Option**", ["Upload a Video File","Directly from Youtube Link" , 'Upload Notable Photos'])
  if options == "Directly from Youtube Link":
      if states.path=="" :
          states.video_url = st.text_input("**Enter your Youtube Video URL**")
          states.note_button = st.button("Get Notes")
          if states.video_url !=""  and states.note_button and (states.video_url.startswith("https://www.youtube.com/watch?v=") or states.video_url.startswith("https://youtu.be/")):
                try:
                    retrive = st.success("**Checking your video**")
                    yt = YouTube(states.video_url)
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
                except Exception as e:
                    retrive.empty()
                    st.error(e)
                    st.stop()


                if video:
                    video_title = yt.title 
                    sanitized_title = sanitize_title(video_title)
                    states.path = f"{sanitized_title}.mp4"
                    downloading = st.success("**Downloading on progress..**")
                    try:
                      video.download(filename=states.path)
                      res.empty()
                      downloading.empty()
                    except Exception as e:
                        res.empty()
                        downloading.empty()
                        st.error(e)
                        st.stop()
                    
                    st.sidebar.video(states.path)
                    states.files.append(states.path)

          else:
            st.stop()
      else:
         pass


  elif options == "Upload a Video File":
    if states.path=="" and states.submit_button != True:
      uploader = st.file_uploader('Upload the lecture video', type=['mp4', 'mkv'])
      if uploader:
          temp_dir = tempfile.mkdtemp(prefix="gemini_videos")
          states.path = os.path.join(temp_dir, uploader.name)
          with open(states.path, "wb") as f:
            f.write(uploader.getvalue())
          st.sidebar.video(states.path)
          states.files.append(states.path)
      else:
         st.stop()
    else:
        pass
    

  elif options == 'Upload Notable Photos':
     if len(states.parts) < 10 or states.photo_button == None:
      uploader = st.file_uploader('Upload Photos to be Noted',  accept_multiple_files=True, type=['png', 'jpg', 'jpeg'])
      if uploader:
          for photos_value in uploader:
            temp_dir = tempfile.mkdtemp(prefix="gemini_photos")
            photo_path = os.path.join(temp_dir, photos_value.name)
            with open(photo_path, 'wb') as f:
                f.write(photos_value.getvalue())
            st.sidebar.image(photo_path,use_column_width=True)
            states.files.append(photo_path)
            states.photos.append(photo_path)
          states.photo_button = st.button('Get Notes')
          if states.photo_button:
            pass
          else: 
            st.stop()
      else:
          st.stop()

     else:
      for photos_reserved in states.photos:
         st.sidebar.image(photos_reserved,use_column_width=True)
      pass 
  else:
     st.stop()
 

place.empty()
if states.parts == None:
   success = st.warning("**Wait a few moments to process**")
   for file in states.files:
      try:
        obj = upload_to_gemini(file)
        states.parts.append(obj)
        if states.photos == None:
          wait_for_files_active(obj)  
      except Exception as e:
         success.empty()
         st.error(e)
         st.stop()
   success.empty()
else:
   pass


if 'history' not in states:
   states.history= [{"role":"user", "parts":states.parts}]

chat_session = model.start_chat(history=states.history)

if states.responses == None:
  generating = st.info("**Your note is generating. Please be patient.**")
  try:
    states.responses = chat_session.send_message("Here is the video. Follow instructions you are given and give a detailed note of the whole lecture.")
    states.history.append({"role":"model", "parts":[states.responses.text]})
    generating.empty()
    text = states.responses.text
    st.write(text)
    states.pdf_file = converter(text)
    with open(states.pdf_file, "rb") as file:
      if st.sidebar.download_button(
          label="Download PDF",
          data=file,
          file_name="KeyNoter.pdf",
          mime="application/pdf"
      ):
         pass
      else:
         st.stop()
    
  except Exception as e:
    generating.empty()
    st.error(e)
    os.remove(states.path)
    genai.delete_file(states.video_obj.name)
else:
   pass

if states.responses != None:
  if len(states.photos) !=0:
     for photo_paths in states.photos:
        os.remove(photo_paths)
  else:
       os.remove(states.path)
  os.remove(states.pdf_file)
  os.remove(states.md_file_path)
  genai.delete_file(states.video_obj.name)
  st.write(states.responses.text)
else:
  os.remove(states.path)
  genai.delete_file(states.video_obj.name)
st.stop()