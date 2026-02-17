Feature: 샌드박스 네트워크 기반 Target URL

  Scenario: 환경 생성 시 네트워크 내부 URL 반환
    Given 레포가 클론되어 있다
    And 서비스 Dockerfile이 있다
    When 환경을 생성한다
    Then target_url은 컨테이너 이름 기반이다
    And network_name이 응답에 포함된다
