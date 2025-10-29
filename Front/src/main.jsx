/**
 * React 애플리케이션 진입점 파일
 * - React DOM을 통해 App 컴포넌트를 root 엘리먼트에 마운트
 * - StrictMode로 개발 중 잠재적 문제를 감지
 */
import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.jsx'

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
