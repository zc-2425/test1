/**
 * 路由 meta 的类型扩展。
 * 每个页面的「骨架配方 / 计划阶段 / 对照截图」都写在 meta 里，
 * 这样 P1 的占位页可以直接当「规格浏览器」用，P5–P10 逐页替换组件即可。
 */
import 'vue-router'
import type { SkeletonKind } from '@/app/router/skeletons'

declare module 'vue-router' {
  interface RouteMeta {
    /** 页面标题（= 截图上的大标题原文） */
    title: string
    /** 副标题/说明，列表页与详情页常有一条 */
    subtitle?: string
    /** 所属模块，用于侧栏高亮与文档归类 */
    module: string
    /** 侧栏高亮键，见 nav.ts；登录页无 */
    navKey?: string
    /** 页面骨架类型 */
    skeleton?: SkeletonKind
    /** 计划在哪个阶段实现 */
    phase?: string
    /** 对照截图文件名（在 _ref/ 下） */
    screen?: string
    /** 本页待办要点，占位页上直接展示 */
    todo?: string[]
    /** 隐藏侧边栏（画布页专用） */
    hideSidebar?: boolean
    /** 无壳布局（登录页专用） */
    blank?: boolean
  }
}
