document.addEventListener('DOMContentLoaded', function() {
  const toggle = document.getElementById('chat-toggle');
  const windowEl = document.getElementById('chat-window');
  const closeBtn = document.getElementById('chat-close');
  const form = document.getElementById('chat-form');
  const input = document.getElementById('chat-input');
  const messages = document.getElementById('chat-messages');
  const micBtn = document.getElementById('chat-mic');

  // Prefer server-side transcription via MediaRecorder if available (press-to-record).
  const supportsMedia = navigator.mediaDevices && window.MediaRecorder;
  if (supportsMedia && micBtn) {
    let mediaStream = null;
    let recorder = null;
    let chunks = [];

    async function startRecording() {
      try {
        mediaStream = await navigator.mediaDevices.getUserMedia({ audio: true });
      } catch (err) {
        console.warn('No se pudo acceder al micrófono:', err);
        micBtn.disabled = true;
        micBtn.title = 'No se pudo acceder al micrófono';
        return;
      }

      chunks = [];
      recorder = new MediaRecorder(mediaStream);
      recorder.ondataavailable = (e) => { if (e.data && e.data.size) chunks.push(e.data); };
      recorder.onstop = async () => {
        micBtn.classList.remove('recording');
        const blob = new Blob(chunks, { type: 'audio/webm' });

        // show minimal UI feedback
        appendUser('[Audio enviado]');
        appendBot('Procesando audio...');
        const typingEl = messages.lastElementChild;

        try {
          const fd = new FormData();
          fd.append('audio', blob, 'recording.webm');

          const res = await fetch('/chat/ollama/audio', { method: 'POST', body: fd });
          if (!res.ok) {
            const err = await res.json().catch(()=>({error:'Respuesta inválida'}));
            appendBot('Error: ' + (err.error || res.statusText));
            return;
          }

          const data = await res.json();
          // remove the 'Procesando audio...' indicator
          if (typingEl && typingEl.classList.contains('bot') && typingEl.textContent === 'Procesando audio...') {
            typingEl.remove();
          }

          if (data.transcript) appendBot('Transcripción: ' + data.transcript);
          if (data.reply) appendBot(data.reply);
          if (!data.reply && !data.transcript) appendBot('No se obtuvo respuesta.');
        } catch (e) {
          appendBot('Error enviando audio: ' + e.message);
        } finally {
          try { mediaStream.getTracks().forEach(t=>t.stop()); } catch(_) {}
          mediaStream = null;
          recorder = null;
          chunks = [];
        }
      };

      recorder.start();
      micBtn.classList.add('recording');
    }

    function stopRecording() {
      if (recorder && recorder.state !== 'inactive') recorder.stop();
      micBtn.classList.remove('recording');
    }

    // press-to-record (mouse & touch)
    micBtn.addEventListener('mousedown', (ev) => { ev.preventDefault(); startRecording(); });
    micBtn.addEventListener('mouseup', (ev) => { ev.preventDefault(); stopRecording(); });
    micBtn.addEventListener('mouseleave', (ev) => { if (micBtn.classList.contains('recording')) stopRecording(); });
    micBtn.addEventListener('touchstart', (ev) => { ev.preventDefault(); startRecording(); });
    micBtn.addEventListener('touchend', (ev) => { ev.preventDefault(); stopRecording(); });

    // For keyboard users: click toggles a short recording
    micBtn.addEventListener('click', async (ev) => {
      ev.preventDefault();
      if (micBtn.classList.contains('recording')) stopRecording(); else {
        await startRecording();
        // auto stop after 6 seconds if user just clicked
        setTimeout(() => { if (micBtn.classList.contains('recording')) stopRecording(); }, 6000);
      }
    });
  } else {
    // Fallback to Web Speech API (client-side transcription) if available
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition || null;
    let recognizer = null;
    if (SpeechRecognition && micBtn) {
      recognizer = new SpeechRecognition();
      recognizer.lang = 'es-ES';
      recognizer.interimResults = true;
      recognizer.maxAlternatives = 1;

      let finalTranscript = '';

      recognizer.addEventListener('result', (event) => {
        let interim = '';
        for (let i = event.resultIndex; i < event.results.length; i++) {
          const transcript = event.results[i][0].transcript;
          if (event.results[i].isFinal) finalTranscript += transcript;
          else interim += transcript;
        }
        input.value = (finalTranscript + ' ' + interim).trim();
      });

      recognizer.addEventListener('end', () => {
        micBtn.classList.remove('listening');
        if (input.value && input.value.trim().length > 0) {
          setTimeout(() => form.dispatchEvent(new Event('submit', { cancelable: true, bubbles: true })), 100);
        }
      });

      recognizer.addEventListener('error', (ev) => {
        console.warn('Speech recognition error', ev.error);
        micBtn.classList.remove('listening');
      });

      micBtn.addEventListener('click', () => {
        if (micBtn.classList.contains('listening')) {
          recognizer.stop();
          micBtn.classList.remove('listening');
        } else {
          finalTranscript = '';
          input.value = '';
          recognizer.start();
          micBtn.classList.add('listening');
        }
      });
    } else if (micBtn) {
      micBtn.title = 'Reconocimiento de voz no soportado en este navegador';
      micBtn.disabled = true;
      micBtn.style.opacity = '0.45';
    }
  }

  function openChat() {
    windowEl.style.display = 'flex';
    windowEl.setAttribute('aria-hidden', 'false');
    input.focus();
    if (!messages.dataset.started) {
      appendBot("Hola, soy el asistente. Pregúntame lo que quieras sobre eventos.");
      messages.dataset.started = 'true';
    }
  }

  function closeChat() {
    windowEl.style.display = 'none';
    windowEl.setAttribute('aria-hidden', 'true');
  }

  toggle.addEventListener('click', () => {
    if (windowEl.style.display === 'flex') closeChat(); else openChat();
  });
  closeBtn.addEventListener('click', closeChat);

  function appendMessage(cls, text) {
    const el = document.createElement('div');
    el.className = 'chat-message ' + cls;
    el.textContent = text;
    messages.appendChild(el);
    messages.scrollTop = messages.scrollHeight;
  }
  function appendUser(text) { appendMessage('user', text); }
  function appendBot(text) { appendMessage('bot', text); }

  async function sendMessage(text) {
    try {
      const res = await fetch('/chat/ollama', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: text })
      });

      if (!res.ok) {
        const err = await res.json().catch(()=>({error:'Respuesta inválida'}));
        appendBot('Error: ' + (err.error || res.statusText));
        return;
      }

      const data = await res.json();
      if (data.reply) appendBot(data.reply);
      else appendBot('No se obtuvo respuesta.');
    } catch (e) {
      appendBot('Error de conexión: ' + e.message);
    }
  }

  form.addEventListener('submit', function(evt) {
    evt.preventDefault();
    const text = input.value.trim();
    if (!text) return;
    appendUser(text);
    input.value = '';
    appendBot('…');
    const typingEl = messages.lastElementChild;

    sendMessage(text).then(() => {
      // remove the typing indicator if still present and replace with real reply handled inside sendMessage
      if (typingEl && typingEl.classList.contains('bot') && typingEl.textContent === '…') {
        typingEl.remove();
      }
    });
  });
});
