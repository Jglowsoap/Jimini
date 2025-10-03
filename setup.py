from setuptools import setup, find_packages

setup(
    name="jimini",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "fastapi>=0.95.0",
        "uvicorn>=0.21.1",
        "pydantic>=2.0.0",
        "pyyaml>=6.0",
        "cryptography>=41.0.0",
        "httpx>=0.24.0",
        "opentelemetry-api>=1.19.0",
        "opentelemetry-sdk>=1.19.0",
        "opentelemetry-exporter-otlp>=1.19.0",
        "openai>=1.0.0",
    ],
    entry_points={
        "console_scripts": [
            "jimini=jimini_cli.cli:main",
        ],
    },
)
