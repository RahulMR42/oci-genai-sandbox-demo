FROM python:3.11-slim

WORKDIR /workspace

# Keep the image deliberately small. Add only packages required by the tutorial workload.
RUN python -m pip install --no-cache-dir --upgrade pip \
    && python -m pip install --no-cache-dir openai==1.109.1 pydantic==2.13.5

COPY smoke_test.py /workspace/smoke_test.py

CMD ["python", "/workspace/smoke_test.py"]
