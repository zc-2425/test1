/**
 * 开发期截图工具：用系统自带 Edge 的 CDP 协议打开页面 → 执行一段 JS（可点按钮）→ 截图。
 *
 * 为什么需要它：toast / 弹窗 / 抽屉 / 确认框这类东西只有真点击才会出现，
 * 而 `msedge --screenshot` 只能截静态首屏。后续每个阶段的自查都靠这个脚本。
 *
 * 用法：
 *   node scripts/dev-screenshot.mjs --url http://127.0.0.1:5273/dev/ui --out _ref/_shots/a.png
 *   node scripts/dev-screenshot.mjs --url ... --out ... --js "document.querySelector('.x').click()"
 *   node scripts/dev-screenshot.mjs --url ... --out ... --height 2400 --wait 1200
 *
 * 依赖：本机安装的 Microsoft Edge（默认路径可用 --edge 覆盖），Node ≥ 22（原生 WebSocket）。
 */

import { spawn } from 'node:child_process'
import { mkdir, writeFile } from 'node:fs/promises'
import { existsSync } from 'node:fs'
import { dirname, resolve } from 'node:path'
import { randomUUID } from 'node:crypto'

const EDGE_CANDIDATES = [
  'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',
  'C:/Program Files/Microsoft/Edge/Application/msedge.exe'
]

function parseArgs(argv) {
  const args = {
    url: 'http://127.0.0.1:5273/',
    out: '_ref/_shots/shot.png',
    width: 1600,
    height: 1000,
    js: '',
    wait: 800,
    edge: ''
  }
  for (let i = 0; i < argv.length; i += 1) {
    const key = argv[i]
    const value = argv[i + 1]
    if (!key?.startsWith('--')) continue
    const name = key.slice(2)
    if (name in args) {
      args[name] = typeof args[name] === 'number' ? Number(value) : value
      i += 1
    }
  }
  return args
}

const args = parseArgs(process.argv.slice(2))
const edgePath = args.edge || EDGE_CANDIDATES.find((p) => existsSync(p))

if (!edgePath) {
  console.error('找不到 msedge.exe，请用 --edge 指定路径')
  process.exit(1)
}

const port = 9300 + Math.floor(Math.random() * 400)
const profile = `C:/Users/${process.env.USERNAME ?? 'HP'}/AppData/Local/Temp/edge-cdp-${randomUUID()}`

const child = spawn(
  edgePath,
  [
    '--headless=new',
    '--disable-gpu',
    '--no-first-run',
    '--no-default-browser-check',
    '--hide-scrollbars',
    '--force-device-scale-factor=1',
    `--window-size=${args.width},${args.height}`,
    `--remote-debugging-port=${port}`,
    `--user-data-dir=${profile}`,
    'about:blank'
  ],
  { stdio: 'ignore' }
)

const sleep = (ms) => new Promise((r) => setTimeout(r, ms))

async function waitForDevtools(timeoutMs = 15000) {
  const deadline = Date.now() + timeoutMs
  while (Date.now() < deadline) {
    try {
      const res = await fetch(`http://127.0.0.1:${port}/json/list`)
      const targets = await res.json()
      const page = targets.find((t) => t.type === 'page' && t.webSocketDebuggerUrl)
      if (page) return page.webSocketDebuggerUrl
    } catch {
      /* 还没起来 */
    }
    await sleep(150)
  }
  throw new Error('等待 CDP 端口超时')
}

function createClient(wsUrl) {
  const socket = new WebSocket(wsUrl)
  const pending = new Map()
  let seq = 0

  const ready = new Promise((res, rej) => {
    socket.addEventListener('open', () => res())
    socket.addEventListener('error', (e) => rej(e))
  })

  socket.addEventListener('message', (event) => {
    const message = JSON.parse(event.data)
    if (message.id && pending.has(message.id)) {
      const { resolve: ok, reject } = pending.get(message.id)
      pending.delete(message.id)
      if (message.error) reject(new Error(JSON.stringify(message.error)))
      else ok(message.result)
    }
  })

  return {
    ready,
    send(method, params = {}) {
      seq += 1
      const id = seq
      return new Promise((ok, reject) => {
        pending.set(id, { resolve: ok, reject })
        socket.send(JSON.stringify({ id, method, params }))
      })
    },
    close() {
      socket.close()
    }
  }
}

try {
  const wsUrl = await waitForDevtools()
  const client = createClient(wsUrl)
  await client.ready

  await client.send('Page.enable')
  await client.send('Runtime.enable')
  await client.send('Emulation.setDeviceMetricsOverride', {
    width: args.width,
    height: args.height,
    deviceScaleFactor: 1,
    mobile: false
  })

  await client.send('Page.navigate', { url: args.url })
  await sleep(args.wait)

  if (args.js) {
    const result = await client.send('Runtime.evaluate', {
      expression: args.js,
      awaitPromise: true,
      returnByValue: true
    })
    if (result.exceptionDetails) {
      throw new Error(`页面内脚本报错：${result.exceptionDetails.text}`)
    }
    if (result.result?.value !== undefined) {
      console.log('eval =>', JSON.stringify(result.result.value))
    }
    // 交互后再等一会儿，让过渡动画走完
    await sleep(500)
  }

  const shot = await client.send('Page.captureScreenshot', { format: 'png' })
  const outPath = resolve(process.cwd(), args.out)
  await mkdir(dirname(outPath), { recursive: true })
  await writeFile(outPath, Buffer.from(shot.data, 'base64'))
  console.log(`saved ${args.out}`)
  client.close()
} catch (error) {
  console.error(String(error))
  process.exitCode = 1
} finally {
  child.kill()
}
