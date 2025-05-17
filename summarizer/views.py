from django.shortcuts import render
from youtube_transcript_api import YouTubeTranscriptApi
from transformers import pipeline
from langdetect import detect
from deep_translator import GoogleTranslator

# HuggingFace summarizer pipeline
summarizer = pipeline("summarization")

# Get video ID from YouTube URL
def get_video_id(url):
    if "v=" in url:
        return url.split("v=")[1].split("&")[0]
    return None

# Break large transcript into smaller parts
def split_text(text, max_tokens=1000):
    sentences = text.split('. ')
    chunks = []
    current_chunk = ''
    for sentence in sentences:
        if len(current_chunk) + len(sentence) <= max_tokens:
            current_chunk += sentence + '. '
        else:
            chunks.append(current_chunk.strip())
            current_chunk = sentence + '. '
    chunks.append(current_chunk.strip())
    return chunks

# Perform summarization
def summarize_text(text):
    chunks = split_text(text)
    summaries = []
    for chunk in chunks:
        if len(chunk.strip()) == 0:
            continue
        summary = summarizer(chunk, max_length=130, min_length=30, do_sample=False)[0]['summary_text']
        summaries.append(summary)
    return " ".join(summaries)

# Main view
def home(request):
    summary = ''
    error = ''
    if request.method == 'POST':
        url = request.POST.get('youtube_url')
        try:
            video_id = get_video_id(url)
            transcript = YouTubeTranscriptApi.get_transcript(video_id)
            full_text = ' '.join([i['text'] for i in transcript])

            # Detect original language
            original_lang = detect(full_text)

            # Translate to English if needed
            if original_lang != 'en':
                full_text_en = GoogleTranslator(source=original_lang, target='en').translate(full_text)
            else:
                full_text_en = full_text

            # Summarize in English
            eng_summary = summarize_text(full_text_en)

            # Translate back to original language if needed
            if original_lang != 'en':
                summary = GoogleTranslator(source='en', target=original_lang).translate(eng_summary)
            else:
                summary = eng_summary

        except Exception as e:
            print("Transcript Error:", e)
            error = "Transcript not available or error occurred."

    return render(request, 'home.html', {'summary': summary, 'error': error})
