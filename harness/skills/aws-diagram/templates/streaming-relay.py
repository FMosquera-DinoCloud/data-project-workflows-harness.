#!/usr/bin/env python
"""
Template: relay de streaming near-real-time con dos consumers independientes
sobre el mismo stream (enhanced fan-out), uno de baja latencia y otro con LLM.

Correr SIEMPRE con el python del venv de la skill:
    ~/.dino/aws-diagram/.venv/bin/python streaming-relay.py

Variables de entorno:
    OUTDIR=docs/diagrams   (default)

Arquitectura genérica de referencia — sin nombre de cliente ni recursos reales.
"""

import os

from diagrams.aws.analytics import KinesisDataStreams
from diagrams.aws.compute import Fargate
from diagrams.aws.integration import Appsync
from diagrams.aws.management import Cloudwatch
from diagrams.aws.ml import Bedrock
from diagrams.onprem.client import Users
from diagrams.onprem.compute import Server

from aws_diagram_theme import cluster, diagram, edge

OUTDIR = os.environ.get("OUTDIR", "docs/diagrams")

with diagram("Relay de streaming near-real-time", outdir=OUTDIR, direction="LR"):
    source = Server("Origen de eventos")

    stream = KinesisDataStreams("Kinesis Data Streams")

    with cluster("ECS Fargate"):
        relay = Fargate("Relay\npassthrough")
        enrich = Fargate("Enriquecimiento\n(2º proceso)")

    pubsub = Appsync("AppSync Events API")
    llm = Bedrock("Bedrock")
    obs = Cloudwatch("CloudWatch")

    front = Users("Operador · browser")

    source >> edge("PutRecord") >> stream
    stream >> edge("EFO · SubscribeToShard") >> relay
    stream >> edge("EFO · 2º consumer") >> enrich
    relay >> edge("POST /event · ≤5 por batch") >> pubsub
    enrich >> edge("InvokeModel") >> llm
    enrich >> edge("POST /event") >> pubsub
    pubsub >> edge("WebSocket") >> front
    relay >> edge("métricas", style="dotted") >> obs
