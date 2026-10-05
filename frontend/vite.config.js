import { defineConfig } from 'vite'  // defineConfig: утилита Vite для автодополнения TypeScript-конфигурации
import vue from '@vitejs/plugin-vue'  // официальный плагин Vite для поддержки .vue файлов (SFC)

// https://vite.dev/config/
export default defineConfig({  // экспортируем объект конфигурации Vite
  plugins: [vue()],  // подключаем плагин Vue: он обрабатывает .vue файлы, компилирует шаблоны в render-функции
})
