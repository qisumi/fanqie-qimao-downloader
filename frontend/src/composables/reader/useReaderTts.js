/**
 * TTS朗读 composable
 * 负责语音合成控制
 */
import { ref } from 'vue'

export function useReaderTts(options = {}) {
  const { message } = options

  const ttsState = ref('idle') // idle | playing | paused
  let currentUtterance = null

  // 获取当前章节纯文本
  function getCurrentPlainText(chapterContent) {
    if (chapterContent?.content_text) return chapterContent.content_text
    if (chapterContent?.content_html) {
      const temp = document.createElement('div')
      temp.innerHTML = chapterContent.content_html
      const text = temp.innerText || temp.textContent || ''
      return text
    }
    return ''
  }

  // 停止朗读
  function stopTts() {
    if (!('speechSynthesis' in window)) return
    window.speechSynthesis.cancel()
    currentUtterance = null
    ttsState.value = 'idle'
  }

  // 暂停朗读
  function pauseTts() {
    if (!('speechSynthesis' in window)) return
    if (window.speechSynthesis.speaking) {
      window.speechSynthesis.pause()
      ttsState.value = 'paused'
    }
  }

  // 继续朗读
  function resumeTts() {
    if (!('speechSynthesis' in window)) return
    if (ttsState.value === 'paused') {
      window.speechSynthesis.resume()
      ttsState.value = 'playing'
    }
  }

  // 开始朗读
  function startTts(chapterContent) {
    if (!('speechSynthesis' in window)) {
      message?.warning?.('当前浏览器不支持朗读')
      return
    }
    stopTts()
    const text = getCurrentPlainText(chapterContent)
    if (!text.trim()) {
      message?.warning?.('无可朗读文本')
      return
    }
    const utter = new SpeechSynthesisUtterance(text)
    utter.lang = 'zh-CN'
    utter.rate = 1
    utter.onend = () => {
      ttsState.value = 'idle'
      currentUtterance = null
    }
    utter.onerror = () => {
      ttsState.value = 'idle'
      currentUtterance = null
    }
    currentUtterance = utter
    window.speechSynthesis.speak(utter)
    ttsState.value = 'playing'
  }

  // 切换朗读状态
  function toggleTts(chapterContent) {
    if (ttsState.value === 'playing') {
      pauseTts()
    } else if (ttsState.value === 'paused') {
      resumeTts()
    } else {
      startTts(chapterContent)
    }
  }

  return {
    ttsState,
    stopTts,
    pauseTts,
    resumeTts,
    startTts,
    toggleTts,
    getCurrentPlainText
  }
}
