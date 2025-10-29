/**
 * Vite 번들러 설정 파일
 * - React 플러그인 활성화
 * - 개발 서버 및 빌드 설정 관리
 */
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
})