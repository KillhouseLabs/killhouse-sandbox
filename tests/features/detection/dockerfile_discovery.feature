Feature: Dockerfile 탐색
  보안 분석을 위해 sandbox가 레포에서 서비스 Dockerfile을 자동으로 찾아야 한다.

  Background:
    Given 레포가 클론되어 있다

  Scenario: 루트 Dockerfile 감지
    Given 루트에 서비스 Dockerfile이 있다
    When Dockerfile을 탐색한다
    Then "Dockerfile" 경로가 반환된다

  Scenario: 하위 디렉토리 Dockerfile 감지
    Given "infra" 디렉토리에 서비스 Dockerfile이 있다
    When Dockerfile을 탐색한다
    Then "infra/Dockerfile" 경로가 반환된다

  Scenario: 루트 Dockerfile이 하위 디렉토리보다 우선
    Given 루트에 서비스 Dockerfile이 있다
    And "infra" 디렉토리에 서비스 Dockerfile이 있다
    When Dockerfile을 탐색한다
    Then "Dockerfile" 경로가 반환된다

  Scenario: .devcontainer Dockerfile은 제외
    Given ".devcontainer" 디렉토리에 서비스 Dockerfile이 있다
    When Dockerfile을 탐색한다
    Then Dockerfile이 발견되지 않는다

  Scenario: EXPOSE/CMD 없는 빌더 이미지 제외
    Given "infra" 디렉토리에 빌더 전용 Dockerfile이 있다
    When Dockerfile을 탐색한다
    Then Dockerfile이 발견되지 않는다

  Scenario: docker-compose.yml에서 Dockerfile 경로 참조
    Given docker-compose.yml에 Dockerfile 경로가 참조되어 있다
    And "infra" 디렉토리에 서비스 Dockerfile이 있다
    When Dockerfile을 탐색한다
    Then "infra/Dockerfile" 경로가 반환된다

  Scenario: Dockerfile이 아예 없는 레포
    Given 루트에 소스 파일만 있다
    When Dockerfile을 탐색한다
    Then Dockerfile이 발견되지 않는다
