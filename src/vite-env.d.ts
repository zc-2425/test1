/// <reference types="vite/client" />

interface ImportMetaEnv {
  /** 接口前缀，默认 '/api'（由 Vite 代理到 FastAPI） */
  readonly VITE_API_BASE?: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}
