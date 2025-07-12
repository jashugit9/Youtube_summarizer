import streamlit as st #For Back-end
from youtube_transcript_api import YouTubeTranscriptApi
from urllib.parse import urlparse, parse_qs
from transformers import pipeline

# 1. This below function extract video ID from URL
def extract_video_id(url):
    query = urlparse(url)
    if query.hostname == 'youtu.be':
        return query.path[1:]
    if query.hostname in ('www.youtube.com', 'youtube.com'):
        if query.path == '/watch':
            return parse_qs(query.query).get('v', [None])[0]
    return None

# 2. This below function will fetch transcript
def fetch_transcript(video_id):
    try:
        return YouTubeTranscriptApi.get_transcript(video_id)
    except Exception as e:
        st.error(f"❌ Transcript fetch failed: {e}")
        return None

# 3. Split text into safe chunks
def split_text(text, max_words=400):
    words = text.split()
    return [' '.join(words[i:i+max_words]) for i in range(0, len(words), max_words)]

# 4. Our replacement of OpenAI - Load Hugging Face summarizer
summarizer = pipeline("summarization", model="facebook/bart-large-cnn")

# 5. Summarize the transcript in chunks
def summarize_transcript(full_text):
    summaries = []
    chunks = split_text(full_text)

    if not chunks:
        return "⚠️ Transcript too short to summarize."

    for i, chunk in enumerate(chunks):
        if len(chunk.split()) < 30:
            continue  # Skip tiny chunks

        with st.spinner(f"🧠 Summarizing chunk {i+1}... please wait."):
            try:
                result = summarizer(chunk, max_length=200, min_length=60, do_sample=False)
                summaries.append(result[0]['summary_text'])
            except Exception as e:
                st.warning(f"❌ Chunk {i+1} failed: {e}")

    if not summaries:
        return "⚠️ No summary could be generated."

    return "\n\n".join(summaries)

# 6. Streamlit Userface 
st.title("🎬 YouTube Transcript Summarizer")
st.write("Paste a YouTube video link, and get a summarized version of its transcript.")

youtube_url = st.text_input("🔗 Enter YouTube video URL")

if youtube_url:
    video_id = extract_video_id(youtube_url)

    if not video_id:
        st.error("❌ Invalid YouTube URL.")
    else:
        st.success(f"✅ Video ID: {video_id}")

        with st.spinner("📥 Fetching transcript..."):
            transcript = fetch_transcript(video_id)

        if transcript:
            full_text = " ".join([entry['text'] for entry in transcript])
            st.subheader("📜 Full Transcript")
            st.write(full_text)

            st.subheader("🧠 Summary")
            summary = summarize_transcript(full_text)
            st.success("✅ Done summarizing!")
            st.write(summary)
