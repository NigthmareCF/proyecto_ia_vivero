/// <reference types="vite/client" />

interface Window {
  SpeechRecognition?: new () => EventTarget;
  webkitSpeechRecognition?: new () => EventTarget;
}
