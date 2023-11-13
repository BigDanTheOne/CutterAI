from youtube_transcript_api import YouTubeTranscriptApi
import torch
from transformers import AutoModelForSpeechSeq2Seq, AutoProcessor, pipeline
import requests
from pytube import YouTube
import os
import audiosegment
import numpy as np

data = {"transcriber" : None}
TMP_WEBM_FILE_NAME = "tmp.webm"
def subtitles_to_text(srt):
    content = ""
    for element in srt:
        if not '[' in element["text"]:
            content += "[" + str(int(element['start'])) + "]"
            content += "\n"
            content += element['text']
            content += "\n"

def get_youtube_subtitles(link):
    VIDEO_ID = link.split("watch?v=")[1].split('&')[0]
    return YouTubeTranscriptApi.get_transcript(VIDEO_ID)


def generate_transcriber():
    device = "cuda:7" if torch.cuda.is_available() else "cpu"
    torch_dtype = torch.float16 if torch.cuda.is_available() else torch.float32

    model_id = "openai/whisper-base"

    model = AutoModelForSpeechSeq2Seq.from_pretrained(
        model_id, torch_dtype=torch_dtype, low_cpu_mem_usage=True, use_safetensors=True
    )
    model.to(device)

    processor = AutoProcessor.from_pretrained(model_id)

    pipe = pipeline(
        "automatic-speech-recognition",
        generate_kwargs={"task": "transcribe"},
        model=model,
        tokenizer=processor.tokenizer,
        feature_extractor=processor.feature_extractor,
        max_new_tokens=128,
        chunk_length_s=30,
        batch_size=22,
        return_timestamps=True,
        torch_dtype=torch_dtype,
        device=device,
    )
    return pipe
def generate_youtube_subtitles(url, data):

    if data["transcriber"] is None:
        data["transcriber"] = generate_transcriber()

    pipe = data.transcriber
    yt = YouTube(url)

    audio_streams = yt.streams.filter(only_audio=True).desc().filter(mime_type="audio/webm")
    max_abr_stream = audio_streams.order_by('abr').last()
    audio = max_abr_stream

    for audio_stream in audio_streams:
        if (audio_stream.abr == max_abr_stream.abr):
            audio = audio_stream
            break

    audio.download(filename=TMP_WEBM_FILE_NAME)

    mono_audio = audiosegment.from_file(TMP_WEBM_FILE_NAME).resample(sample_rate_Hz=16000, sample_width=2, channels=1)
    mono_audio_array = mono_audio.to_numpy_array()
    mono_audio_array = mono_audio_array.astype(np.float32) / (2 ** (2 * 8 - 1))

    if os.path.isfile(TMP_WEBM_FILE_NAME):
        os.remove(TMP_WEBM_FILE_NAME)

    transcription = pipe({'array': mono_audio_array,
                          'sampling_rate': 16000})

    subtitles = transcription["chunks"]
    for i in range(len(subtitles)):
        subtitles[i]['start'] = subtitles[i]['timestamp'][0]

    return subtitles

def youtube_to_text(link):
    subtitles = ""
    try:
        subtitles = get_youtube_subtitles(link)
    except():
        pass
    #
    # try:
    #     subtitles = generate_youtube_subtitles(link, data)
    # except():
    #     pass

    if (subtitles.empty()):
        return None
    else:
        return subtitles_to_text(subtitles)



