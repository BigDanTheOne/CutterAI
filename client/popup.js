const videoUrl = document.getElementById('video-url');
const audioUrl = document.getElementById('audio-url');
const textUrl = document.getElementById('text-url');

const processBtn = document.getElementById('process-btn');  
const loadAudioBtn = document.getElementById('load-audio');
const loadTextBtn = document.getElementById('load-text');

const loading = document.getElementById('loading');

const videoSummary = document.getElementById('video-summary');
const audioSummary = document.getElementById('audio-summary');  
const textSummary = document.getElementById('text-summary');

let cache = {};

loadAudioBtn.addEventListener('click', () => {
  const url = audioUrl.value;
  fetchAudio(url); 
});

loadTextBtn.addEventListener('click', () => {
  const url = textUrl.value;
  fetchText(url);
});

processBtn.addEventListener('click', () => {
  loading.style.display = 'block';

  const videoUrl = videoUrl.value;
  fetchData(videoUrl); 
});

function fetchAudio(url) {
  fetch('/process-audio', {
    method: 'POST', 
    body: JSON.stringify({url})
  })
  .then(r => r.json())
  .then(data => {
    audioSummary.innerText = data.summary;
  });
}

function fetchText(url) {
  fetch('/process-text', {
    method: 'POST',
    body: JSON.stringify({url})  
  })
  .then(r => r.json())
  .then(data => {
    textSummary.innerText = data.summary;
  });
} 

function fetchData(videoUrl) {
  fetch('/process', {
    method: 'POST',
    body: JSON.stringify({videoUrl})
  })
  .then(response => response.json())
  .then(data => {

    videoSummary.innerText = data.video.summary;
    audioSummary.innerText = data.audio.summary;
    textSummary.innerText = data.text.summary;

    if(!data.video.summary) {
      alert('Не удалось сгенерировать резюме видео');
    }

    cache[videoUrl] = data;
    
    loading.style.display = 'none';

  });
}