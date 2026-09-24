# X1 임시 시험 이미지(앱 이미지가 아니다).
# OpenShell 공동체 기본 샌드박스 이미지 위에 Python 3.12 + NAT(nvidia-nat 1.9.0)와 X1 최소 CLI를 넣는다.
# NAT는 이미지 빌드 때 넣는다(호스트 Docker가 빌드하므로 샌드박스 정책의 전송 허용을 열 필요가 없다).
FROM ghcr.io/nvidia/openshell-community/sandboxes/base:latest

USER root
ENV UV_PYTHON_INSTALL_DIR=/opt/x1/python
RUN uv python install 3.12 \
 && uv venv --python 3.12 /opt/x1/venv \
 && VIRTUAL_ENV=/opt/x1/venv uv pip install --no-cache "nvidia-nat==1.9.0" "pyyaml" \
 && chmod -R a+rX /opt/x1

COPY x1_probe.py nat_workflow.yml key_check.py /opt/x1/app/

# 요건 (a) 미끼 파일: 허용 목록 밖 경로에 둔 가짜 정답 파일. 실제 정답은 넣지 않는다.
# DAC(파일 권한)는 읽기를 허용해(0644) 거부가 난다면 Landlock 때문임을 가린다.
RUN mkdir -p /srv/x1-decoy \
 && printf '{"decoy": true, "note": "X1 Landlock decoy. Not a real answer key."}\n' > /srv/x1-decoy/oracle_decoy.json \
 && chmod 755 /srv/x1-decoy && chmod 644 /srv/x1-decoy/oracle_decoy.json \
 && chmod -R a+rX /opt/x1/app

USER sandbox
WORKDIR /sandbox
