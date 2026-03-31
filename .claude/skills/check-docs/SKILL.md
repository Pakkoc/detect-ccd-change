---
name: check-docs
description: >
  Claude Code 공식 문서(code.claude.com/docs)의 변경사항을 감지하고, 변경된 부분의 diff를 포함한 HTML 리포트를
  Gmail로 직접 발송하는 스킬. /check-docs를 입력하면 실행된다.
  사용자가 "문서 변경사항 확인", "docs 업데이트 체크", "문서 바뀐거 있어?", "check docs changes" 등의 표현을
  사용할 때도 이 스킬을 사용한다.
---

# Check Claude Code Docs Changes

Claude Code 공식 문서 75개 페이지를 가져와서 이전 스냅샷과 비교한 뒤, 변경사항이 있으면 diff가 포함된 HTML 이메일을 Gmail SMTP로 직접 발송한다.

## 실행 흐름

### Step 1: Python 스크립트 실행

프로젝트 루트(`C:\dev\detect_ccd_change`)에서 다음 명령을 실행한다:

```bash
cd C:/dev/detect_ccd_change && uv run python main.py --send-email
```

이 스크립트가 하는 일:
1. 75개 문서 페이지를 fetch하여 `snapshots/` 디렉토리에 저장
2. git diff로 이전 커밋과 비교
3. 변경사항이 있으면 HTML 리포트를 생성하고 Gmail로 발송
4. 새 스냅샷을 git commit

### Step 2: 사용자에게 결과 보고

스크립트 출력을 읽고 사용자에게 결과를 알려준다:

**첫 실행 (baseline)인 경우:**
- "최초 실행으로 기준 스냅샷 75개를 저장했습니다. 다음 실행부터 변경사항을 감지합니다."

**변경사항이 없는 경우:**
- "75개 문서 페이지를 확인했습니다. 변경사항이 없습니다."

**변경사항이 있는 경우:**
- 추가된 페이지 수, 수정된 페이지 수, 삭제된 페이지 수
- 각 변경된 페이지의 URL
- "이메일로 상세 리포트를 발송했습니다."

## 참고사항

- 문서 URL 목록은 `urls.json`에 정의되어 있으며, 새 페이지가 추가되면 이 파일을 업데이트하면 된다
- `.env` 파일에서 `EMAIL_TO`, `GMAIL_APP_PASSWORD` 등 설정을 변경할 수 있다
- 스냅샷은 git으로 버전 관리되므로 변경 이력이 모두 보존된다
- GitHub Actions로 매일 오전 9시(KST) 자동 실행됨 (PC 꺼져있어도 동작)
