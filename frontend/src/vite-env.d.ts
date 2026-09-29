/// <reference types="vite/client" />

/** 前端可读取的 Vite 环境变量。 */
interface ImportMetaEnv {
  readonly VITE_API_BASE_URL?: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}
