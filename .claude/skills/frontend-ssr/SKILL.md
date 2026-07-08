---
name: frontend-ssr
description: "템플릿 엔진·프론트 프레임워크 없이 순수 Vanilla HTML/CSS(Tailwind)를 파편으로 조립하는 SSR 프론트 레이어 — layouts/pages 파편, ssrRenderer 조립 엔진, escapeHtml XSS 방어, dev/prod 분기 빌드. 화면(페이지) 추가·SSR 렌더링 구성 시 적용."
---
# Frontend SSR — 순수 HTML 조립 렌더링 (Vanilla SSR)

복잡한 프론트 프레임워크(React/Vue)나 템플릿 엔진(EJS/Nunjucks) 없이, 순수 Vanilla HTML/CSS(Tailwind)로 SSR을 구성한다.

> **⚠️ 이 프로젝트 매핑 (kist)** — 아래 본문은 TypeScript·`services/web` 모노레포 기준의 범용 표준이다. 이 프로젝트의 실제 구조로 읽는다:
> | 범용 표준(본문) | 이 프로젝트 실제 |
> |---|---|
> | `services/web/{layouts,pages,public}` | `client/{components,pages,styles}` + 정적 `public/` |
> | `ssrRenderer.ts` (TS) | `server/server.js`의 조립 로직 (순수 JS, ES Modules) |
> | `escapeHtml.ts` | `server/utils/escapeHtml.js` |
> | `build.js` | 루트 `build.mjs` (`npm run build` → `dist/`) |
> | `app.ts` 정적 서빙 | `server/server.js` |
> 원칙(파편 조립·`escapeHtml` XSS 방어·dev/prod 분기 빌드)은 그대로 적용하되, **파일 경로·언어는 위 매핑을 따른다.**

## 경계 (담당 / 위임)
- **담당**: `services/web/`의 HTML 파편(layouts/pages/public), 렌더링 엔진(`ssrRenderer.ts`), XSS 유틸(`escapeHtml.ts`), 프론트 빌드(`build.js`), 페이지 추가.
- **위임 → `backend-service-architecture`(②)**: 모노레포 골격, `package.json`/`tsconfig`, `app.ts` 전체 구조·미들웨어 순서, 서버 내부 계층(Router/Controller/Service). 이 스킬은 `app.ts`에 정적 서빙 한 줄만 기여한다.

> 순서: ②가 서버 골격·`app.ts`를 세우고, 그 위에 이 스킬이 `web/` + 렌더링 엔진을 얹는다.

## 핵심 규칙
1. **프레임워크 다이어트**: `base.html`/`header`/`footer` 파편을 `fs.readFileSync`로 읽어 캐싱하고 Slot(`<!-- {{content}} -->`)을 치환해 서빙.
2. **XSS 차단**: 동적 데이터 주입은 반드시 `escapeHtml`을 거친다.
3. **프론트/백 물리 분리**: 프론트 리소스는 `services/web/`. (모노레포 골격 결정 자체는 ② 소관)
4. **독립 프로덕션 빌드**: dev에선 `web/` 원본 참조, prod 빌드 시 정적 리소스를 `dist/web`로 복사해 독립 실행.

## 디렉터리 (이 스킬이 만드는 것)
```text
services/
 ├── server/
 │    └── src/
 │         ├── lib/ssrRenderer.ts      # HTML 조립 엔진
 │         └── utils/escapeHtml.ts     # XSS 방어 유틸
 └── web/
      ├── layouts/                     # base.html, header.html, footer.html …
      ├── pages/                       # 알맹이 페이지 조각
      ├── public/                      # 정적 파일 (CSS, JS, 이미지)
      └── build.js                     # dist로 복사하는 빌더
```

## 핵심 스니펫

### 1. XSS 방어 유틸 (`server/src/utils/escapeHtml.ts`)
```typescript
export function escapeHtml(unsafe: string): string {
    if (typeof unsafe !== 'string') return unsafe;
    return unsafe
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}
```

### 2. SSR 조립 엔진 (`server/src/lib/ssrRenderer.ts`)
`NODE_ENV` 분기(prod=`dist/web`, dev=원본 `web`), Fragment 캐싱, 시작 시 필수 레이아웃 검증, Slot 치환을 포함한다.
```typescript
import fs from 'fs';
import path from 'path';
import { escapeHtml } from '../utils/escapeHtml';

const isProd = process.env.NODE_ENV === 'production';
const WEB_VIEWS_DIR = isProd
    ? path.join(__dirname, '../web')
    : path.join(__dirname, '../../../web');

const fragmentCache = new Map<string, string>();

const REQUIRED_LAYOUTS = ['layouts/base.html', 'layouts/header.html', 'layouts/footer.html'];
function validateLayouts() {
    REQUIRED_LAYOUTS.forEach(layout => {
        const fullPath = path.join(WEB_VIEWS_DIR, layout);
        if (!fs.existsSync(fullPath)) {
            throw new Error(`[SSR] 필수 레이아웃 파일 누락: ${fullPath}`);
        }
    });
    console.log('[SSR] 레이아웃 파일 검증 완료');
}
validateLayouts();

function readWithCache(filePath: string): string {
    if (isProd && fragmentCache.has(filePath)) return fragmentCache.get(filePath)!;
    const content = fs.existsSync(filePath) ? fs.readFileSync(filePath, 'utf-8') : '';
    if (isProd) fragmentCache.set(filePath, content);
    return content;
}

export interface RenderOptions {
    title?: string;
    extraHead?: string;
    extraScripts?: string;
}

export function renderPage(pageViewPath: string, options: RenderOptions = {}): string {
    const layoutDir = path.join(WEB_VIEWS_DIR, 'layouts');
    const baseLayout = readWithCache(path.join(layoutDir, 'base.html'));
    const header = readWithCache(path.join(layoutDir, 'header.html'));
    const footer = readWithCache(path.join(layoutDir, 'footer.html'));
    const pageContent = readWithCache(path.join(WEB_VIEWS_DIR, pageViewPath));

    return baseLayout
        .replace('<!-- {{head}} -->', options.extraHead || '')
        .replace('<!-- {{title}} -->', escapeHtml(options.title || 'Default Title'))
        .replace('<!-- {{header}} -->', header)
        .replace('<!-- {{content}} -->', pageContent || '<main><h1>Page Not Found</h1></main>')
        .replace('<!-- {{footer}} -->', footer)
        .replace('<!-- {{scripts}} -->', options.extraScripts || '');
}
```

### 3. 정적 서빙 (`app.ts`에 기여하는 한 줄)
`app.ts`의 주인은 ②다. 이 분기만 ②의 미들웨어 순서에 맞춰 끼운다.
```typescript
import path from 'path';
const isProd = process.env.NODE_ENV === 'production';
const PUBLIC_DIR = isProd
    ? path.join(__dirname, 'web/public')          // prod
    : path.join(__dirname, '../../web/public');   // dev
app.use(express.static(PUBLIC_DIR));
```

### 4. 프론트 독립 빌더 (`web/build.js`)
```javascript
const fs = require('fs');
const path = require('path');

const srcDir = __dirname;
const destDir = path.join(__dirname, '../server/dist/web');
const copyOptions = { recursive: true, force: true }; // Node 16+

if (!fs.existsSync(destDir)) fs.mkdirSync(destDir, { recursive: true });

['layouts', 'pages', 'public', 'index.html'].forEach(item => {
    const srcPath = path.join(srcDir, item);
    const destPath = path.join(destDir, item);
    if (fs.existsSync(srcPath)) fs.cpSync(srcPath, destPath, copyOptions);
});
```

## 적용 지침

### 새 화면(페이지) 추가
1. `web/pages/`에 페이지 HTML 파편 생성.
2. 라우터에서 `renderPage('pages/<파일>.html', { title })`로 조립해 응답. (라우터→컨트롤러→서비스 계층은 ②를 따름)
3. 동적 데이터는 반드시 `escapeHtml`을 거쳐 주입.
4. `base.html`에 Slot 마커(`<!-- {{content}} -->` 등)가 있는지 확인.

### SSR을 처음 붙일 때
1. 먼저 ②로 서버 골격·`app.ts`가 서 있는지 확인(없으면 ②부터).
2. `services/web/{layouts,pages,public}`와 `build.js` 생성, `server/src`에 `ssrRenderer.ts`·`escapeHtml.ts` 이식.
3. `base.html`에 Slot 마커 + Tailwind 연동.
4. `app.ts`에 정적 서빙 분기(§3)를 ②의 순서에 맞게 삽입.
5. `npm run dev`(원본 참조) / `npm run build`(dist 복사) 동작 안내.
