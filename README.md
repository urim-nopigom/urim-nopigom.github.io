# 한솔 노피곰 걸포오스타파라곤교실 홈페이지

블로그: https://m.blog.naver.com/urim_cozy_study  
RSS: https://rss.blog.naver.com/urim_cozy_study.xml

## 자동 업데이트
- GitHub Actions가 3시간마다 공개 RSS를 확인합니다 (지연 가능).
- `scripts/update_posts.py`가 공개 글 최신 6개의 제목, 링크, 날짜를 `posts.json`에 저장합니다.
- 같은 Actions 실행에서 GitHub Pages를 배포하므로 자동 갱신 후 공개 사이트에도 적용됩니다.
- RSS에 접근할 수 없으면 이전 `posts.json`을 그대로 사용합니다.
- 게시글 사진은 수집하지 않습니다. RSS는 아직 실연결 검증을 하지 못했습니다.

## 공개 방법 — GitHub Pages
1. https://github.com 에 가입/로그인합니다.
2. 새 **Public** 저장소를 만들고 이름을 `nopigom-site`로 지정합니다.
3. 압축을 풀고 나온 파일과 폴더를 저장소 최상위에 업로드합니다. `.github/workflows/update-blog.yml` 파일도 반드시 포함하세요. GitHub 웹 업로드에서 숨김 폴더가 빠질 수 있으므로 확인하세요.
4. **Settings → Pages → Build and deployment → Source: GitHub Actions**로 설정합니다. (Deploy from a branch가 아닙니다.)
5. **Settings → Actions → General → Workflow permissions**에서 필요시 **Read and write permissions**를 허용합니다. 저장소 정책에 따라 다를 수 있습니다.
6. **Actions → Update Naver blog posts and publish site → Run workflow**를 실행합니다. 첫 업로드에서 push로 자동 실행될 수도 있습니다.
7. **Settings → Pages**에서 실제 사이트 URL을 확인합니다. 보통 `https://사용자이름.github.io/nopigom-site/` 형태입니다.

## 주의
- ZIP 파일 또는 로컬 HTML에서는 `posts.json`을 브라우저가 읽지 못할 수 있습니다. HTTPS에 배포하여 확인하세요.
- GitHub Actions 자동 실행은 지연 또는 중단될 수 있으므로 100% 즉시 반영을 보장하지 않습니다.
- 사이트와 공개 저장소에는 아이들 개인정보, 연락처, 비공개 사진을 넣지 마세요.
- GitHub Pages와 GitHub Actions의 무료 이용에는 사용량 및 정책 제한이 있습니다.
